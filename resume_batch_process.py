#!/usr/bin/env python3
"""
Resume batch processing script for transcribing and diarizing audio files
Processes remaining WAV files in Input/ContactCenter and saves results to Output folder
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio import convert_audio_to_wav, split_audio_into_chunks
from transcription import load_model, format_srt, format_vtt, transcribe_audio_chunk
from diarization import Diarizer
from config import get_config
from models import WhisperSegment, TranscriptionResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def is_file_processed(base_name: str, output_dir: str) -> bool:
    """Check if a file has already been processed"""
    json_file = os.path.join(output_dir, f"{base_name}.json")
    txt_file = os.path.join(output_dir, f"{base_name}.txt")
    return os.path.exists(json_file) and os.path.exists(txt_file)

def process_audio_file(audio_path: str, output_dir: str, asr_model, diarizer: Optional[Diarizer] = None):
    """
    Process a single audio file for transcription and diarization
    
    Args:
        audio_path: Path to the input audio file
        output_dir: Directory to save output files
        asr_model: Loaded ASR model
        diarizer: Optional diarizer for speaker identification
    """
    logger.info(f"Processing: {audio_path}")
    
    # Get base filename without extension
    base_name = Path(audio_path).stem
    
    try:
        # Convert to WAV format if needed
        wav_file = convert_audio_to_wav(audio_path)
        
        # Split audio into chunks if it's too long
        config = get_config()
        chunk_duration = config.chunk_duration
        audio_chunks = split_audio_into_chunks(wav_file, chunk_duration=chunk_duration)
        
        # Process speaker diarization if available
        diarization_result = None
        if diarizer:
            logger.info(f"Performing speaker diarization for {base_name}")
            diarization_result = diarizer.diarize(wav_file)
            logger.info(f"Diarization found {diarization_result.num_speakers} speakers")
        
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
        
        # Apply diarization if available
        if diarizer and diarization_result and diarization_result.segments:
            logger.info(f"Applying diarization to {len(all_segments)} segments")
            all_segments = diarizer.merge_with_transcription(diarization_result, all_segments)
            
            # Include speaker labels in text
            previous_speaker = None
            seen_speakers = set()
            
            for segment in all_segments:
                if hasattr(segment, 'speaker') and segment.speaker:
                    speaker_label = segment.speaker
                    if speaker_label.startswith("speaker_"):
                        try:
                            # Extract speaker number from the label
                            parts = speaker_label.split("_")
                            speaker_num = int(parts[-1]) + 1  # Add 1 to make it 1-indexed
                            
                            # Only add speaker prefix if this is a different speaker than the previous one
                            if speaker_label != previous_speaker:
                                if speaker_label not in seen_speakers:
                                    prefix = f"Speaker {speaker_num}: "
                                    seen_speakers.add(speaker_label)
                                else:
                                    prefix = f"{speaker_num}: "
                                
                                segment.text = f"{prefix}{segment.text}"
                            
                            previous_speaker = speaker_label
                            
                        except (ValueError, IndexError):
                            if "Speaker" != previous_speaker:
                                segment.text = f"Speaker: {segment.text}"
                                previous_speaker = "Speaker"
            
            # Reconstruct full text with speaker labels
            full_text = " ".join(segment.text for segment in all_segments)
        
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
    """Main function to process remaining audio files"""
    
    # Set up paths
    input_dir = "Input/ContactCenter"
    output_dir = "Output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of WAV files
    wav_files = []
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            if file.lower().endswith('.wav'):
                wav_files.append(os.path.join(input_dir, file))
    
    if not wav_files:
        logger.error(f"No WAV files found in {input_dir}")
        return
    
    # Filter out already processed files
    remaining_files = []
    for wav_file in wav_files:
        base_name = Path(wav_file).stem
        if not is_file_processed(base_name, output_dir):
            remaining_files.append(wav_file)
        else:
            logger.info(f"Skipping already processed file: {os.path.basename(wav_file)}")
    
    if not remaining_files:
        logger.info("All files have already been processed!")
        return
    
    logger.info(f"Found {len(remaining_files)} remaining WAV files to process")
    
    # Load the ASR model
    logger.info("Loading ASR model...")
    config = get_config()
    asr_model = load_model(config.model_id)
    logger.info("ASR model loaded successfully")
    
    # Initialize diarization if token is available
    diarizer = None
    hf_token = config.get_hf_token()
    if hf_token:
        logger.info("Initializing speaker diarization...")
        diarizer = Diarizer(access_token=hf_token)
        logger.info("Speaker diarization initialized")
    else:
        logger.warning("No HuggingFace token found. Speaker diarization will be disabled.")
        logger.info("To enable diarization, set HUGGINGFACE_ACCESS_TOKEN environment variable")
    
    # Process each remaining file
    for i, wav_file in enumerate(remaining_files, 1):
        logger.info(f"Processing file {i}/{len(remaining_files)}: {os.path.basename(wav_file)}")
        try:
            process_audio_file(wav_file, output_dir, asr_model, diarizer)
        except Exception as e:
            logger.error(f"Failed to process {wav_file}: {str(e)}")
            continue
    
    logger.info("Batch processing completed!")
    logger.info(f"Results saved to: {output_dir}")

if __name__ == "__main__":
    main()