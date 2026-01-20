"""
NeMo-based Speaker Diarization Service

This service provides speaker diarization using NVIDIA NeMo's ClusteringDiarizer.

The service includes:
- Voice Activity Detection (VAD) using MarbleNet
- Speaker embedding extraction using TitaNet
- Spectral clustering for speaker assignment

Configuration:
- Batch size: 16 (adjust based on GPU memory)
- Max speakers: 8
- Window length: 1.5s
- Shift length: 0.75s
"""

from typing import List, Optional, Dict
from datetime import datetime
import threading
import tempfile
import os
import json
import torch
from omegaconf import OmegaConf
import numpy as np

diarization_throttler = threading.Semaphore(3)

# Global diarizer instance (initialized once)
_diarizer = None
_diarizer_lock = threading.Lock()

def _fixed_seq_collate_fn_patched(self, batch):
    """
    Patched version of NeMo's collate function that handles edge cases
    """
    # Handle empty batch
    if not batch:
        raise StopIteration("Empty batch")
    
    # Filter out None values
    batch = [item for item in batch if item is not None]
    
    if not batch:
        raise StopIteration("All items in batch are None")
    
    # Check if batch items are properly formatted (should be tuples/lists of 4 elements)
    valid_batch = []
    for item in batch:
        if isinstance(item, (tuple, list)) and len(item) == 4:
            valid_batch.append(item)
        else:
            print(f"Warning: Skipping malformed batch item: {type(item)}")
    
    if not valid_batch:
        raise StopIteration("No valid items in batch")
    
    batch = valid_batch
    
    try:
        # Original logic
        _, audio_lengths, _, tokens_lengths = zip(*batch)
        
        max_audio_len = 0
        has_audio = audio_lengths[0] is not None
        if has_audio:
            max_audio_len = max(audio_lengths).item()
        
        max_tokens_len = 0
        has_tokens = tokens_lengths[0] is not None
        if has_tokens:
            max_tokens_len = max(tokens_lengths).item()
        
        audio_signal, tokens = [], []
        for sig, sig_len, tokens_i, tokens_i_len in batch:
            if has_audio:
                sig_len = sig_len.item()
                if sig_len < max_audio_len:
                    pad = (0, max_audio_len - sig_len)
                    sig = torch.nn.functional.pad(sig, pad)
                audio_signal.append(sig)
            
            if has_tokens:
                tokens_i_len = tokens_i_len.item()
                if tokens_i_len < max_tokens_len:
                    pad = (0, max_tokens_len - tokens_i_len)
                    tokens_i = torch.nn.functional.pad(tokens_i, pad, value=self.pad_id)
                tokens.append(tokens_i)
        
        if has_audio:
            audio_signal = torch.stack(audio_signal)
            audio_lengths = torch.stack(audio_lengths)
        else:
            audio_signal, audio_lengths = None, None
        
        if has_tokens:
            tokens = torch.stack(tokens)
            tokens_lengths = torch.stack(tokens_lengths)
        else:
            tokens, tokens_lengths = None, None
        
        return audio_signal, audio_lengths, tokens, tokens_lengths
    
    except Exception as e:
        # If anything fails, raise StopIteration to skip this batch
        print(f"Collate function error (skipping batch): {e}")
        raise StopIteration(f"Collate error: {e}")

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
            from nemo.collections.asr.data.audio_to_label import AudioToSpeechLabelDataset
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            temp_dir = tempfile.mkdtemp()
            
            # Patch the collate function before creating diarizer
            print("Applying collate function patch...")
            original_collate = AudioToSpeechLabelDataset.fixed_seq_collate_fn
            AudioToSpeechLabelDataset.fixed_seq_collate_fn = _fixed_seq_collate_fn_patched
            
            # Create diarization config
            config = OmegaConf.create({
                'device': device,
                'num_workers': 1,  # Use 1 worker to avoid single-process issues
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
                        'batch_size': 16  # Larger batch size for better batching
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
            import traceback
            traceback.print_exc()
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
        import soundfile as sf
        import librosa
        
        # Ensure audio file is in proper format for NeMo
        audio_file_name = os.path.splitext(os.path.basename(audio_path))[0]
        temp_audio_path = os.path.join(temp_dir, f"{audio_file_name}_processed.wav")
        
        print(f"Preparing audio file for diarization: {audio_file_name}")
        
        # Read and process audio to ensure proper format
        try:
            # Load audio with librosa (handles various formats)
            audio_data, sample_rate = librosa.load(audio_path, sr=16000, mono=True)
            
            # Ensure float32 format and normalize
            audio_data = audio_data.astype(np.float32)
            
            # Normalize to prevent clipping
            max_val = np.abs(audio_data).max()
            if max_val > 0:
                audio_data = audio_data / max_val * 0.95
            
            # Write as proper 16kHz mono WAV file with PCM_16 encoding
            sf.write(temp_audio_path, audio_data, 16000, subtype='PCM_16')
            
            duration = len(audio_data) / 16000
            print(f"Audio prepared: {duration:.2f}s, 16kHz, mono, PCM_16")
            
        except Exception as e:
            print(f"Error preparing audio file: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        # Create manifest file for NeMo
        manifest_path = os.path.join(temp_dir, "input_manifest.json")
        manifest_entry = {
            "audio_filepath": temp_audio_path,
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
        
        print(f"Manifest created: {manifest_path}")
        
        # Update diarizer config with manifest path
        diarizer._cfg.diarizer.manifest_filepath = manifest_path
        diarizer._cfg.diarizer.out_dir = temp_dir
        diarizer._cfg.num_workers = 1  # Use 1 worker for better stability
        
        # Run diarization with error handling
        print(f"Running NeMo diarization on {audio_file_name}...")
        try:
            diarizer.diarize()
        except (AttributeError, TypeError, StopIteration) as e:
            print(f"Diarization pipeline error: {e}")
            print("This is likely due to audio segmentation issues. Trying alternative approach...")
            # The error occurred during embedding extraction, but VAD might have succeeded
            # Check if we can use VAD results alone
            vad_dir = os.path.join(temp_dir, "speaker_outputs")
            if os.path.exists(vad_dir):
                print("VAD completed, but speaker embedding extraction failed")
            return {}
        
        # Parse RTTM output
        rttm_dir = os.path.join(temp_dir, "pred_rttms")
        rttm_path = os.path.join(rttm_dir, f"{audio_file_name}_processed.rttm")
        
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
            # Check for alternative filename
            alt_rttm_path = os.path.join(rttm_dir, f"{audio_file_name}.rttm")
            if os.path.exists(alt_rttm_path):
                print(f"Found RTTM at alternative path: {alt_rttm_path}")
                rttm_path = alt_rttm_path
                # Re-parse with alternative path
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
            print("No speaker segments found from NeMo diarization")
            # No fallback - if NeMo fails, segments remain without speaker labels
        else:
            # Assign speakers to transcription segments using NeMo results
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
            
            print(f"Successfully assigned speakers to {len(transcription['segments'])} segments using NeMo")
        
    except Exception as e:
        print(f"Diarization failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: add default speaker labels
        for segment in transcription["segments"]:
            if "speaker" not in segment:
                segment["speaker"] = "Speaker 1"
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
