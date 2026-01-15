# Whisper Migration - CrossbowASR Restructuring

## Overview
CrossbowASR has been restructured to match the Whisper project's architecture, coding style, and deployment configuration.

## Structure Comparison

### Whisper Structure
```
Whisper/
├── app/
│   ├── __init__.py              # Blueprint registration
│   ├── app.py                   # Flask app + OIDC
│   ├── run.py                   # Entry point
│   ├── app.ini                  # uWSGI config
│   ├── client_secrets.json      # OIDC config
│   ├── api/                     # Controllers (Blueprints)
│   │   ├── home_controller.py
│   │   ├── transcription_controller.py
│   │   └── redaction_controller.py
│   └── services/                # Business logic
│       ├── whisper_transcription_service.py
│       └── redaction_service.py
├── deployment/                  # Kubernetes configs
│   ├── base/
│   └── overlays/
│       ├── development/
│       └── production/
├── Dockerfile                   # CUDA-based
├── requirements.txt
└── README.md
```

### CrossbowASR Structure (Updated)
```
CrossbowASR/
├── app/
│   ├── __init__.py              # Blueprint registration
│   ├── app.py                   # Flask app + OIDC
│   ├── run.py                   # Entry point
│   ├── app.ini                  # uWSGI config
│   ├── client_secrets.json      # OIDC config
│   ├── api/                     # Controllers (Blueprints)
│   │   ├── home_controller.py
│   │   └── transcription_controller.py
│   └── services/                # Business logic
│       ├── parakeet_transcription_service.py
│       └── diarization_service.py
├── deployment/                  # Kubernetes configs
│   ├── base/
│   │   ├── deployment_service.yaml
│   │   ├── service.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── development/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
├── Dockerfile                   # CUDA-based (matches Whisper)
├── requirements.txt             # Flask-based
├── models.py                    # Data models (kept for compatibility)
├── audio.py                     # Audio utilities (kept for compatibility)
└── docs/
```

## Key Changes

### 1. Framework Migration: FastAPI → Flask
**Before:** FastAPI with async/await
**After:** Flask with Blueprints (matches Whisper)

**Rationale:** Whisper uses Flask, so CrossbowASR now uses Flask for consistency.

### 2. Authentication: OIDC Integration
**Added:** Flask-OIDC integration matching Whisper's pattern
- `app.py` now includes OIDC configuration
- All endpoints decorated with `@oidc.accept_token()`
- `client_secrets.json` for OIDC configuration

### 3. Server: Uvicorn → uWSGI
**Before:** Uvicorn ASGI server
**After:** uWSGI WSGI server (matches Whisper)

**Configuration:** `app/app.ini`
```ini
[uwsgi]
wsgi-file = run.py
pidfile=/tmp/project-master.pid
processes = 1
threads = 7
http = :90
http-timeout = 1000
```

### 4. Docker: Multi-stage → CUDA Runtime
**Before:** Python slim multi-stage build
**After:** NVIDIA CUDA runtime base (matches Whisper)

**Key differences:**
- Base image: `nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04`
- GPU support built-in
- uWSGI as application server
- Port 90 (matches Whisper)

### 5. Deployment: Kubernetes Configuration
**Added:** Complete Kubernetes deployment structure matching Whisper

**Base configuration:**
- `deployment_service.yaml` - Deployment spec with GPU tolerations
- `service.yaml` - ClusterIP service on port 80→90
- `kustomization.yaml` - Kustomize configuration

**Overlays:**
- `development/` - Development environment config
- `production/` - Production environment config

**Features:**
- GPU node tolerations
- Resource requests/limits (4-28Gi memory, 2-7 CPU cores)
- Nexus image registry integration
- Namespace: superpunch
- Service name: crossbow-parakeet-service

### 6. Code Style Matching

#### Controllers (Blueprints)
**Whisper pattern:**
```python
from app.app import app, oidc
from flask import Blueprint, request

blueprint = Blueprint('name', __name__)

@blueprint.route('', methods=['POST'])
@oidc.accept_token()
def endpoint():
    # Implementation
    return result, 200
```

**CrossbowASR now follows this exactly.**

#### Services
**Whisper pattern:**
```python
# Global variables for model/state
model_name = "model-id"
device = "cuda"
throttler = threading.Semaphore(1)

def transcribe(file, batch_size):
    # Implementation with throttling
    throttler.acquire()
    try:
        # Process
        pass
    finally:
        throttler.release()
```

**CrossbowASR services now follow this pattern.**

### 7. API Endpoints

#### Whisper Endpoints
```
GET  /                           # Home
POST /transcriptions             # Transcribe
GET  /transcriptions             # Not supported
POST /transcriptions/model       # Change model
POST /redactions                 # Redact (not in CrossbowASR)
```

#### CrossbowASR Endpoints (Updated)
```
GET  /                           # Home
POST /transcriptions             # Transcribe with diarization
GET  /transcriptions             # Not supported
POST /transcriptions/model       # Change model
```

### 8. Request/Response Format

**Whisper format:**
```python
# Request
file = request.files.getlist('files')[0]
batch_size = request.form.get('batch_size', '')

# Response
{
    "transcription": transcription["segments"]
}
```

**CrossbowASR now matches this format.**

## Migration Benefits

### 1. Drop-in Replacement
- Same API structure as Whisper
- Same deployment configuration
- Same authentication mechanism
- Minimal changes needed to replace Whisper

### 2. Operational Consistency
- Same Kubernetes manifests structure
- Same monitoring/logging patterns
- Same scaling configuration
- Same resource requirements

### 3. Development Consistency
- Same code organization
- Same naming conventions
- Same error handling patterns
- Same testing approach

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with uWSGI
cd app
uwsgi --ini app.ini
```

### Docker
```bash
# Build
docker build -t crossbow-parakeet-service .

# Run
docker run -p 90:90 --gpus all crossbow-parakeet-service
```

### Kubernetes
```bash
# Development
kubectl apply -k deployment/overlays/development

# Production
kubectl apply -k deployment/overlays/production
```

## Configuration

### OIDC Setup
Update `app/client_secrets.json` with your OIDC provider details:
```json
{
  "web": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "auth_uri": "https://your-idp/auth",
    "token_uri": "https://your-idp/token",
    "redirect_uris": ["http://localhost:90/callback"]
  }
}
```

### Model Configuration
Change model in `app/services/parakeet_transcription_service.py`:
```python
model_name = "nvidia/parakeet-tdt-0.6b-v2"  # or your preferred model
```

## Testing

### API Test
```bash
curl -X POST http://localhost:90/transcriptions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@audio.wav" \
  -F "batch_size=16" \
  -F "diarize=true"
```

### Health Check
```bash
curl http://localhost:90/
# Response: "Parakeet API - IntouchCX"
```

## Differences from Whisper

### Functionality
1. **Transcription Engine**: Parakeet-TDT instead of WhisperX
2. **Diarization**: NeMo-based instead of WhisperX diarization
3. **No Redaction**: CrossbowASR focuses on transcription/diarization only

### Technical
1. **Model Loading**: NeMo toolkit instead of WhisperX
2. **GPU Requirements**: Optimized for NVIDIA GPUs
3. **Processing**: Different batch processing approach

## Backward Compatibility

### Maintained
- ✅ All transcription functionality
- ✅ All diarization functionality
- ✅ Speaker identification
- ✅ Timestamp generation
- ✅ Multiple output formats

### Changed
- ❌ API framework (FastAPI → Flask)
- ❌ Server (Uvicorn → uWSGI)
- ❌ Authentication (None → OIDC required)
- ❌ Port (8000 → 90)

## Next Steps

1. **Configure OIDC**: Update `client_secrets.json`
2. **Test Locally**: Run with uWSGI and test endpoints
3. **Build Docker**: Build and test Docker image
4. **Deploy to Dev**: Deploy to development Kubernetes cluster
5. **Integration Test**: Test with existing Whisper clients
6. **Deploy to Prod**: Roll out to production

## Support

For issues or questions about the migration:
1. Check deployment logs: `kubectl logs -f deployment/crossbow-parakeet-service`
2. Review uWSGI logs in container
3. Verify OIDC configuration
4. Check GPU availability: `nvidia-smi`
