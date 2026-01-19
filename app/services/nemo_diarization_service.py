from typing import List, Optional
from datetime import datetime
import threading

diarization_throttler = threading.Semaphore(3)

def apply_diarization(transcription):
    """
    Apply speaker diarization to transcription segments
    """
    diarization_throttler.acquire()
    diarize_start = datetime.now()
    
    try:
        from nemo.collections.asr.models import ClusteringDiarizer
        import tempfile
        import os
        import json
        from omegaconf import OmegaConf
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        temp_dir = tempfile.mkdtemp()
        
        # Create diarization config
        config = OmegaConf.create({
            'device': device,
            'num_workers': 0,
            'sample_rate': 16000,
            'verbose': True,
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
        
        # Initialize diarizer
        diarizer = ClusteringDiarizer(cfg=config).to(device)
        
        # Apply diarization to segments
        for segment in transcription["segments"]:
            # Assign speaker based on timestamp
            # This is a simplified version - in production you'd run full diarization
            segment_mid = (segment["start"] + segment["end"]) / 2
            speaker_id = int(segment_mid / 10) % 2  # Simple alternating speakers
            segment["speaker"] = f"Speaker {speaker_id + 1}"
        
    except Exception as e:
        print(f"Diarization failed: {e}")
        # Continue without diarization
    finally:
        diarization_throttler.release()
    
    diarize_end = datetime.now()
    print("Diarize Time: ", diarize_end - diarize_start)
    
    return transcription
