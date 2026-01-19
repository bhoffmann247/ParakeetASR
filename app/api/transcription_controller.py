from app.app import app, oidc
from flask import Blueprint, request
from services.parakeet_transcription_service import transcribe, change_model
from services.nemo_diarization_service import apply_diarization
import traceback

transcription_blueprint = Blueprint('transcriptions_blueprint', __name__)

@transcription_blueprint.route('', methods=['POST'])
@oidc.accept_token()
def start_transcription():
    """
    Transcribe audio file with optional diarization
    """
    diarize = request.form.get('diarize', 'true').lower() == 'true'
    response_format = request.form.get('response_format', 'json')
    batch_size = request.form.get('batch_size', '16')
    
    file = request.files.getlist('files')[0]
    
    try:
        transcription = transcribe(file, batch_size)
        
        if diarize:
            try:
                transcription = apply_diarization(transcription)
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

@transcription_blueprint.route('', methods=['GET'])
@oidc.accept_token()
def get():
    return "GET Not Supported", 404

@transcription_blueprint.route('/model', methods=['POST'])
@oidc.accept_token()
def change_transcribe_model():
    model_name = request.form.get('model_name', 'parakeet-tdt-0.6b-v2')
    
    change_model(model_name)
    
    return f"Model Updated to {model_name}", 200
