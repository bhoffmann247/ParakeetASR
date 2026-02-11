"""
SageMaker serving script for custom container

This script provides the Flask server that SageMaker expects.
"""

import os
import sys
import json
import base64
import tempfile
from flask import Flask, request, jsonify

# Add app directory to path
sys.path.insert(0, '/opt/ml/code/app')

from services.parakeet_transcription_service import transcribe
from services.nemo_diarization_service import apply_diarization

app = Flask(__name__)


@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint required by SageMaker"""
    return '', 200


@app.route('/invocations', methods=['POST'])
def invocations():
    """
    Inference endpoint required by SageMaker
    
    Expects JSON with:
    - audio_base64: Base64 encoded audio file
    - batch_size: Batch size for processing (default: 16)
    - diarize: Enable speaker diarization (default: true)
    """
    try:
        # Parse request
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            return jsonify({'error': f'Unsupported content type: {request.content_type}'}), 400
        
        # Get parameters
        audio_base64 = data.get('audio_base64')
        batch_size = data.get('batch_size', 16)
        diarize = data.get('diarize', True)
        
        if not audio_base64:
            return jsonify({'error': 'Missing audio_base64 parameter'}), 400
        
        # Decode audio
        audio_data = base64.b64decode(audio_base64)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Create a mock file object for the transcribe function
            class MockFile:
                def __init__(self, path, filename):
                    self.path = path
                    self.filename = filename
                
                def save(self, destination):
                    import shutil
                    shutil.copy(self.path, destination)
            
            mock_file = MockFile(temp_path, 'audio.wav')
            
            # Transcribe
            transcription, audio_path = transcribe(mock_file, batch_size)
            
            # Apply diarization if requested
            if diarize:
                transcription = apply_diarization(transcription, audio_path)
            
            # Format response
            result = {
                "transcription": transcription["segments"]
            }
            
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return jsonify(result), 200
            
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # SageMaker expects the server to listen on port 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
