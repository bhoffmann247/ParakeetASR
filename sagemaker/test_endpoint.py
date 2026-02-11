"""
Test script for SageMaker endpoint

Usage:
    python test_endpoint.py --endpoint parakeet-transcription --audio ../tests/Input/ContactCenter/103046_1000780789-21-00-01.wav
"""

import argparse
import boto3
import json
import base64
import os
from datetime import datetime


def test_with_base64(endpoint_name, audio_path, diarize=True, batch_size=16):
    """Test endpoint with base64 encoded audio"""
    
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return
    
    print(f"Testing endpoint: {endpoint_name}")
    print(f"Audio file: {audio_path}")
    print(f"File size: {os.path.getsize(audio_path) / 1024:.2f} KB")
    
    # Read and encode audio
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Prepare payload
    payload = {
        'audio_base64': audio_base64,
        'batch_size': batch_size,
        'diarize': diarize,
        'model_name': 'nvidia/parakeet-tdt-0.6b-v2'
    }
    
    # Invoke endpoint
    runtime = boto3.client('sagemaker-runtime')
    
    print("\nSending request...")
    start_time = datetime.now()
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = json.loads(response['Body'].read().decode())
        
        print(f"\n✓ Request completed in {duration:.2f}s")
        print(f"\nTranscription Results:")
        print("=" * 80)
        
        if 'transcription' in result:
            for segment in result['transcription']:
                speaker = segment.get('speaker', 'Unknown')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                
                print(f"[{start:.2f}s - {end:.2f}s] {speaker}: {text}")
        else:
            print(json.dumps(result, indent=2))
        
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_with_s3(endpoint_name, s3_uri, diarize=True, batch_size=16):
    """Test endpoint with S3 URI"""
    
    print(f"Testing endpoint: {endpoint_name}")
    print(f"S3 URI: {s3_uri}")
    
    payload = {
        'audio_s3_uri': s3_uri,
        'batch_size': batch_size,
        'diarize': diarize,
        'model_name': 'nvidia/parakeet-tdt-0.6b-v2'
    }
    
    runtime = boto3.client('sagemaker-runtime')
    
    print("\nSending request...")
    start_time = datetime.now()
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = json.loads(response['Body'].read().decode())
        
        print(f"\n✓ Request completed in {duration:.2f}s")
        print(f"\nTranscription Results:")
        print("=" * 80)
        
        if 'transcription' in result:
            for segment in result['transcription']:
                speaker = segment.get('speaker', 'Unknown')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                
                print(f"[{start:.2f}s - {end:.2f}s] {speaker}: {text}")
        else:
            print(json.dumps(result, indent=2))
        
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Test SageMaker Parakeet Endpoint')
    
    parser.add_argument(
        '--endpoint',
        required=True,
        help='SageMaker endpoint name'
    )
    
    parser.add_argument(
        '--audio',
        help='Path to local audio file'
    )
    
    parser.add_argument(
        '--s3-uri',
        help='S3 URI to audio file (e.g., s3://bucket/path/audio.wav)'
    )
    
    parser.add_argument(
        '--no-diarize',
        action='store_true',
        help='Disable speaker diarization'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=16,
        help='Batch size for processing (default: 16)'
    )
    
    args = parser.parse_args()
    
    if not args.audio and not args.s3_uri:
        print("Error: Must provide either --audio or --s3-uri")
        parser.print_help()
        return
    
    diarize = not args.no_diarize
    
    if args.audio:
        test_with_base64(args.endpoint, args.audio, diarize, args.batch_size)
    elif args.s3_uri:
        test_with_s3(args.endpoint, args.s3_uri, diarize, args.batch_size)


if __name__ == '__main__':
    main()
