from flask import Blueprint, jsonify
import sys

home_blueprint = Blueprint('home_blueprint', __name__)

@home_blueprint.route('/', methods=['GET'])
def home():
    return "Parakeet API - IntouchCX", 200

@home_blueprint.route('/health', methods=['GET'])
def health():
    """Health check endpoint with system diagnostics"""
    try:
        import torch
        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        
        # Check for device_mesh module
        device_mesh_available = False
        device_mesh_error = None
        try:
            from torch.distributed import device_mesh
            device_mesh_available = True
        except ImportError as e:
            device_mesh_error = str(e)
        
        return jsonify({
            "status": "healthy",
            "python_version": sys.version,
            "torch_version": torch_version,
            "cuda_available": cuda_available,
            "device_mesh_available": device_mesh_available,
            "device_mesh_error": device_mesh_error
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
