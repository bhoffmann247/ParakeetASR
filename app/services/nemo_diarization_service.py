from typing import List, Optional, Dict
from datetime import datetime
import threading
import tempfile
import os
import json
import torch
from omegaconf import OmegaConf

diarization_throttler = threading.Semaphore(3)

# Global diarizer instance (initialized once)
_diarizer = None
_diarizer_lock = threading.Lock()

def _get_diarizer():
    """
    Get or initialize the global diarizer instance (singleton pattern)
    """
    global _diarizer
    
    if _diarizer is not None:
        return _diarizer
    
    with _diarizer_lock:
        # Double-check after acquiring lock
        if _diarizer is not None:
            return _diarizer
        
        try:
            from nemo.collections.asr.models import ClusteringDiarizer
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            temp_dir = tempfile.mkdtemp()
            
            # Create diarization config
            config = OmegaConf.create({
                'device': device,
                'num_workers': 0,
                'sample_rate': 16000,
                'verbose': False,
                'diarizer': {
                    'manifest_filepath': None,
                    'out_dir': temp_dir,
                    'oracle_vad': False,
                    'collar': 0.25,
                    'ignore_overlap': True,
                    'vad': {
                        'model_path': 'vad_multilingual_marblenet',
                        'parameters': {
                            'window_length_in_sec': 0.15,
                            'shift_length_in_sec': 0.01,
                            'smoothing': False,
                            'overlap': 0.5,
                            'onset': 0.8,
                            'offset': 0.6,
                            'pad_onset': 0.05,
                            'pad_offset': -0.05,
                            'min_duration_on': 0.2,
                            'min_duration_off': 0.2,
                            'filter_speech_first': True
                        }
                    },
                    'speaker_embeddings': {
                        'model_path': 'titanet_large',
                        'parameters': {
                            'window_length_in_sec': 1.5,
                            'shift_length_in_sec': 0.75,
                            'multiscale_weights': None,
                            'save_embeddings': False
                        },
                        'batch_size': 1
                    },
                    'clustering': {
                        'parameters': {
                            'oracle_num_speakers': False,
                            'max_num_speakers': 8,
                            'enhanced_count_thres': 40,
                            'max_rp_threshold': 0.25,
                            'sparse_search_volume': 30
                        }
                    }
                }
            })
            
            print("Initializing NeMo diarizer...")
            _diarizer = ClusteringDiarizer(cfg=config).to(device)
            print(f"NeMo diarizer initialized on {device}")
            
        except Exception as e:
            print(f"Failed to initialize diarizer: {e}")
            _diarizer = None
    
    return _diarizer

def _run_diarization(audio_path: str, temp_dir: str) -> Dict[str, List]:
    """
    Run NeMo diarization on an audio file
    
    Returns:
        Dictionary with speaker segments: {speaker_id: [(start, end), ...]}
    """
    diarizer = _get_diarizer()
    if diarizer is None:
        return {}
    
    try:
        # Get audio duration
        import librosa
        duration = librosa.get_duration(path=audio_path)
        audio_file_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Create manifest file for NeMo
        manifest_path = os.path.join(temp_dir, "input_manifest.json")
        manifest_entry = {
            "audio_filepath": audio_path,
            "offset": 0,
            "duration": duration,
            "label": "infer",
            "text": "-",
            "num_speakers": None,
            "rttm_filepath": None,
            "uem_filepath": None
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_entry, f)
            f.write('\n')
        
        # Update diarizer config with manifest path
        diarizer._cfg.diarizer.manifest_filepath = manifest_path
        diarizer._cfg.diarizer.out_dir = temp_dir
        
        # Run diarization
        print(f"Running diarization on {audio_file_name}...")
        diarizer.diarize()
        
        # Parse RTTM output
        rttm_dir = os.path.join(temp_dir, "pred_rttms")
        rttm_path = os.path.join(rttm_dir, f"{audio_file_name}.rttm")
        
        speaker_segments = {}
        if os.path.exists(rttm_path):
            with open(rttm_path, 'r') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 8 and parts[0] == "SPEAKER":
                            start_time = float(parts[3])
                            duration_val = float(parts[4])
                            end_time = start_time + duration_val
                            speaker_id = parts[7]
                            
                            if speaker_id not in speaker_segments:
                                speaker_segments[speaker_id] = []
                            speaker_segments[speaker_id].append((start_time, end_time))
            
            print(f"Diarization found {len(speaker_segments)} speakers")
        else:
            print(f"Warning: RTTM file not found at {rttm_path}")
        
        return speaker_segments
        
    except Exception as e:
        print(f"Error during diarization: {e}")
        import traceback
        traceback.print_exc()
        return {}

def _assign_speaker_to_segment(segment_start: float, segment_end: float, 
                               speaker_segments: Dict[str, List]) -> Optional[str]:
    """
    Assign a speaker to a transcription segment based on overlap with diarization results
    
    Args:
        segment_start: Start time of transcription segment
        segment_end: End time of transcription segment
        speaker_segments: Dictionary of speaker segments from diarization
        
    Returns:
        Speaker ID with most overlap, or None if no overlap found
    """
    if not speaker_segments:
        return None
    
    max_overlap = 0
    assigned_speaker = None
    
    # Calculate overlap with each speaker's segments
    for speaker_id, segments in speaker_segments.items():
        total_overlap = 0
        
        for spk_start, spk_end in segments:
            # Calculate overlap between transcription segment and speaker segment
            overlap_start = max(segment_start, spk_start)
            overlap_end = min(segment_end, spk_end)
            
            if overlap_end > overlap_start:
                total_overlap += (overlap_end - overlap_start)
        
        if total_overlap > max_overlap:
            max_overlap = total_overlap
            assigned_speaker = speaker_id
    
    return assigned_speaker

def apply_diarization(transcription, audio_path: str):
    """
    Apply speaker diarization to transcription segments using NeMo
    
    Args:
        transcription: Transcription result with segments
        audio_path: Path to the audio file that was transcribed
        
    Returns:
        Transcription with speaker labels added to segments
    """
    diarization_throttler.acquire()
    diarize_start = datetime.now()
    
    temp_dir = None
    
    try:
        # Create temporary directory for diarization outputs
        temp_dir = tempfile.mkdtemp()
        
        # Run diarization
        speaker_segments = _run_diarization(audio_path, temp_dir)
        
        if not speaker_segments:
            print("No speaker segments found, skipping speaker assignment")
            diarization_throttler.release()
            return transcription
        
        # Assign speakers to transcription segments
        for segment in transcription["segments"]:
            speaker_id = _assign_speaker_to_segment(
                segment["start"], 
                segment["end"], 
                speaker_segments
            )
            
            if speaker_id:
                # Format speaker label consistently
                segment["speaker"] = f"Speaker {int(speaker_id.split('_')[-1]) + 1}"
            else:
                segment["speaker"] = "Unknown"
        
        print(f"Successfully assigned speakers to {len(transcription['segments'])} segments")
        
    except Exception as e:
        print(f"Diarization failed: {e}")
        import traceback
        traceback.print_exc()
        # Continue without diarization
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Failed to cleanup temp directory: {e}")
        
        diarization_throttler.release()
    
    diarize_end = datetime.now()
    print("Diarize Time: ", diarize_end - diarize_start)
    
    return transcription
