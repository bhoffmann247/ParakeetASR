import torch
import gc
import os
from datetime import datetime
import threading

model_name = "nvidia/parakeet-tdt-0.6b-v2"
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "float32"
model_dir = "/mdl/"
transcription_throttler = threading.Semaphore(1)

class Options:
    def __init__(self, batch_size=16, file_name="Unknown"):
        self.batch_size = batch_size
        self.file_name = file_name

def change_model(new_model):
    """Change the transcription model"""
    print(f"Changing model to {new_model} in variables!")
    global model_name
    model_name = new_model

def transcribe_audio_file(audio, options):
    """Transcribe audio file using Parakeet-TDT"""
    transcription_throttler.acquire()
    transcribe_start = datetime.now()
    
    try:
        from nemo.collections.asr.models import EncDecRNNTBPEModel
        
        model = EncDecRNNTBPEModel.from_pretrained(model_name)
        if device == "cuda":
            model = model.cuda()
        
        with torch.no_grad():
            transcription = model.transcribe([audio], timestamps=True)
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        del model
        
    finally:
        transcription_throttler.release()
    
    transcribe_end = datetime.now()
    transcribe_total = transcribe_end - transcribe_start
    print(f"{options.file_name} - Transcribe Time: {transcribe_total}")
    
    return transcription[0] if transcription else {"text": "", "segments": []}

def transcribe(file, batch_size):
    """
    Main transcription function
    
    Returns:
        Tuple of (transcription_result, file_path) where file_path is the saved audio file
    """
    upload_dir = "/uploads"
    options = Options(file_name=file.filename, batch_size=batch_size)
    
    process_start = datetime.now()
    print(f"{options.file_name} - Starting transcription")
    print(f"Using model: {model_name}")
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Save uploaded file with proper format
    file_path = os.path.join(upload_dir, file.filename)
    
    # Save to temporary location first
    temp_path = file_path + ".tmp"
    file.save(temp_path)
    
    # Convert to proper WAV format using soundfile to ensure seekability
    try:
        import soundfile as sf
        import numpy as np
        
        # Read audio data
        audio_data, sample_rate = sf.read(temp_path)
        
        # Write as proper WAV file
        sf.write(file_path, audio_data, sample_rate, subtype='PCM_16')
        
        # Remove temp file
        os.remove(temp_path)
    except Exception as e:
        # If conversion fails, just use the original file
        print(f"Warning: Could not convert audio file: {e}")
        if os.path.exists(temp_path):
            os.rename(temp_path, file_path)
    
    try:
        # Transcribe
        transcription = transcribe_audio_file(file_path, options)
        
        # Format segments
        segments = []
        if hasattr(transcription, 'timestamp') and 'segment' in transcription.timestamp:
            for i, stamp in enumerate(transcription.timestamp['segment']):
                segments.append({
                    "id": i,
                    "start": stamp['start'],
                    "end": stamp['end'],
                    "text": stamp['segment']
                })
        else:
            # Fallback: create single segment
            segments.append({
                "id": 0,
                "start": 0.0,
                "end": len(transcription.text.split()) / 2.0,
                "text": transcription.text
            })
        
        result = {
            "text": transcription.text,
            "segments": segments,
            "language": "en"
        }
        
        process_end = datetime.now()
        process_total = process_end - process_start
        print(f"{options.file_name} - Total Process Time: {process_total}")
        
        # Return both result and file path (caller is responsible for cleanup)
        return result, file_path
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e
