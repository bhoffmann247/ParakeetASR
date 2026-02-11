"""
Example client for SageMaker Parakeet Transcription Endpoint

This demonstrates different ways to invoke the endpoint.
"""

import boto3
import json
import base64
import os


class ParakeetClient:
    """Client for Parakeet transcription endpoint"""
    
    def __init__(self, endpoint_name, region_name='us-east-1'):
        """
        Initialize client
        
        Args:
            endpoint_name: Name of the SageMaker endpoint
            region_name: AWS region
        """
        self.endpoint_name = endpoint_name
        self.runtime = boto3.client('sagemaker-runtime', region_name=region_name)
    
    def transcribe_file(self, audio_path, diarize=True, batch_size=16):
        """
        Transcribe a local audio file
        
        Args:
            audio_path: Path to audio file
            diarize: Enable speaker diarization
            batch_size: Batch size for processing
        
        Returns:
            Transcription result dictionary
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Read and encode audio
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Prepare payload
        payload = {
            'audio_base64': audio_base64,
            'batch_size': batch_size,
            'diarize': diarize
        }
        
        # Invoke endpoint
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        result = json.loads(response['Body'].read().decode())
        return result
    
    def transcribe_s3(self, s3_uri, diarize=True, batch_size=16):
        """
        Transcribe audio from S3
        
        Args:
            s3_uri: S3 URI (e.g., s3://bucket/path/audio.wav)
            diarize: Enable speaker diarization
            batch_size: Batch size for processing
        
        Returns:
            Transcription result dictionary
        """
        payload = {
            'audio_s3_uri': s3_uri,
            'batch_size': batch_size,
            'diarize': diarize
        }
        
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        result = json.loads(response['Body'].read().decode())
        return result
    
    def transcribe_bytes(self, audio_bytes, diarize=True, batch_size=16):
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            diarize: Enable speaker diarization
            batch_size: Batch size for processing
        
        Returns:
            Transcription result dictionary
        """
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        payload = {
            'audio_base64': audio_base64,
            'batch_size': batch_size,
            'diarize': diarize
        }
        
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        result = json.loads(response['Body'].read().decode())
        return result
    
    def format_transcription(self, result):
        """
        Format transcription result for display
        
        Args:
            result: Transcription result from endpoint
        
        Returns:
            Formatted string
        """
        if 'transcription' not in result:
            return str(result)
        
        lines = []
        for segment in result['transcription']:
            speaker = segment.get('speaker', 'Unknown')
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            
            lines.append(f"[{start:.2f}s - {end:.2f}s] {speaker}: {text}")
        
        return '\n'.join(lines)


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = ParakeetClient(endpoint_name='parakeet-transcription')
    
    # Example 1: Transcribe local file
    print("Example 1: Transcribe local file")
    print("-" * 80)
    
    audio_file = '../tests/Input/ContactCenter/103046_1000780789-21-00-01.wav'
    
    if os.path.exists(audio_file):
        result = client.transcribe_file(audio_file, diarize=True)
        print(client.format_transcription(result))
    else:
        print(f"Audio file not found: {audio_file}")
    
    print("\n")
    
    # Example 2: Transcribe from S3
    print("Example 2: Transcribe from S3")
    print("-" * 80)
    
    # Uncomment and update with your S3 URI
    # result = client.transcribe_s3('s3://my-bucket/audio/recording.wav')
    # print(client.format_transcription(result))
    print("(Update with your S3 URI)")
    
    print("\n")
    
    # Example 3: Transcribe without diarization (faster)
    print("Example 3: Transcribe without diarization")
    print("-" * 80)
    
    if os.path.exists(audio_file):
        result = client.transcribe_file(audio_file, diarize=False)
        print(client.format_transcription(result))
    else:
        print(f"Audio file not found: {audio_file}")
    
    print("\n")
    
    # Example 4: Batch processing multiple files
    print("Example 4: Batch processing")
    print("-" * 80)
    
    audio_dir = '../tests/Input/ContactCenter'
    
    if os.path.exists(audio_dir):
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')][:3]
        
        for audio_file in audio_files:
            file_path = os.path.join(audio_dir, audio_file)
            print(f"\nProcessing: {audio_file}")
            
            try:
                result = client.transcribe_file(file_path, diarize=True)
                print(client.format_transcription(result))
            except Exception as e:
                print(f"Error: {e}")
    else:
        print(f"Audio directory not found: {audio_dir}")
