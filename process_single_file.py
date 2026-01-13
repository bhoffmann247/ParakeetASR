#!/usr/bin/env python3
"""
Process a single audio file for transcription
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio import convert_audio_to_wav, split_audio_into_chunks
from transcription import load_model, format_srt, format_vtt, transcribe_audio_chunk
from config import get_config
from models import WhisperSegment, TranscriptionResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_audio_file(audio_path: str, output_dir: str):
    """Process a single audio file"""
    
    logger.info(f"Processing: {audio_path}")
    
    # Get base filename without extension
    base_name = Path(audio_path).stem
    
    # Check if already processed
    json_file = os.path.join(output_dir, f"{base_name}.json")
    if os.path.exists(json_file):
        logger.info(f"File {base_name} already processed, skipping")
        return
    
    # Load the ASR model
    logger.info("Loading ASR model...")
    config = get_config()
    asr_model = load_model(config.model_id)
    logger.info("ASR model loaded successfully")
    
    try:
        # Convert to WAV format if needed
        wav_file = convert_audio_to_wav(audio_path)
        
        # Split audio into chunks if it's too long
        chunk_duration = config.chunk_duration
        audio_chunks = split_audio_into_chunks(wav_file, chunk_duration=chunk_duration)
        
        # Process each chunk
        all_text = []
        all_segments = []
        
        for i, chunk_path in enumerate(audio_chunks):
            logger.info(f"Processing chunk {i+1}/{len(audio_chunks)} for {base_name}")
            
            # Transcribe the chunk
            chunk_text, chunk_segments = transcribe_audio_chunk(
                asr_model,
                chunk_path,
                language=None,  # Auto-detect
                word_timestamps=False
            )
            
            # Add offset to timestamps if not the first chunk
            if i > 0:
                offset = i * chunk_duration
                for segment in chunk_segments:
                    segment.start += offset
                    segment.end += offset
            
            all_text.append(chunk_text)
            all_segments.extend(chunk_segments)
        
        # Combine results
        full_text = " ".join(all_text)
        
        # Create output files
        output_base = os.path.join(output_dir, base_name)
        
        # Save as JSON (verbose format)
        response = TranscriptionResponse(
            text=full_text,
            segments=all_segments,
            language="auto-detected",
            duration=sum(segment.end - segment.start for segment in all_segments) if all_segments else 0,
            model="parakeet-tdt-0.6b-v2"
        )
        
        with open(f"{output_base}.json", "w", encoding="utf-8") as f:
            json.dump(response.dict(), f, indent=2, ensure_ascii=False)
        
        # Save as plain text
        with open(f"{output_base}.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
        
        # Save as SRT subtitle format
        if all_segments:
            with open(f"{output_base}.srt", "w", encoding="utf-8") as f:
                f.write(format_srt(all_segments))
            
            # Save as VTT subtitle format
            with open(f"{output_base}.vtt", "w", encoding="utf-8") as f:
                f.write(format_vtt(all_segments))
        
        logger.info(f"Successfully processed {base_name}")
        
        # Clean up temporary files
        if wav_file != audio_path and os.path.exists(wav_file):
            os.unlink(wav_file)
        for chunk in audio_chunks:
            if chunk != wav_file and os.path.exists(chunk):
                os.unlink(chunk)
                
    except Exception as e:
        logger.error(f"Error processing {audio_path}: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_single_file.py <audio_file_path>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_dir = "Output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(audio_file):
        logger.error(f"Audio file not found: {audio_file}")
        sys.exit(1)
    
    process_audio_file(audio_file, output_dir)

if __name__ == "__main__":
    main()