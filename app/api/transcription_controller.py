from app.app import app, oidc
from flask import Blueprint, request
from services.parakeet_transcription_service import transcribe, change_model
from services.nemo_diarization_service import apply_diarization
import traceback
import os

transcription_blueprint = Blueprint('transcriptions_blueprint', __name__)

@transcription_blueprint.route('', methods=['POST'])
# @oidc.accept_token()  # Temporarily disabled for testing
def start_transcription():
    """
    Transcribe audio file with optional diarization
    """
    diarize = request.form.get('diarize', 'true').lower() == 'true'
    response_format = request.form.get('response_format', 'json')
    batch_size = request.form.get('batch_size', '16')
    
    file = request.files.getlist('files')[0]
    audio_path = None
    
    try:
        # Transcribe (returns result and file path)
        transcription, audio_path = transcribe(file, batch_size)
        
        if diarize:
            try:
                transcription = apply_diarization(transcription, audio_path)
            except Exception as e:
                print(f"Error applying diarization: \n\n{e}")
                traceback.print_exc()
        
        transcription_result = {
            "transcription": transcription["segments"]
        }
        
        return transcription_result, 200
        
    except Exception as e:
        print(f"Error during transcription: \n\n{e}")
        traceback.print_exc()
        return {"error": str(e)}, 500
    finally:
        # Cleanup audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                print(f"Failed to cleanup audio file: {e}")

@transcription_blueprint.route('', methods=['GET'])
# @oidc.accept_token()  # Temporarily disabled for testing
def get():
    return "GET Not Supported", 404

@transcription_blueprint.route('/model', methods=['POST'])
# @oidc.accept_token()  # Temporarily disabled for testing
def change_transcribe_model():
    model_name = request.form.get('model_name', 'parakeet-tdt-0.6b-v2')
    
    change_model(model_name)
    
    return f"Model Updated to {model_name}", 200
