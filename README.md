# Parakeet Whisper-Compatible API

A Flask-based API server that provides transcription and speaker diarization using [NVIDIA's Parakeet-TDT model](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) and [NVIDIA NeMo](https://github.com/NVIDIA/NeMo).

**Designed as a drop-in replacement for the Whisper service.**

## Features

- Flask-based API with Blueprint architecture (matches Whisper structure)
- OIDC authentication integration
- NVIDIA Parakeet-TDT 0.6B V2 model for high-quality transcription
- Speaker diarization using NVIDIA NeMo
- uWSGI application server
- Kubernetes deployment ready
- GPU-optimized Docker image

## Quick Start

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

## API Endpoints

### Transcribe Audio

```
POST /transcriptions
```

**Headers:**
- `Authorization: Bearer <token>` (OIDC token required)

**Form Parameters:**
- `files`: Audio file (multipart/form-data)
- `batch_size`: Batch size for processing (default: 16)
- `diarize`: Enable speaker diarization (default: true)

**Example:**
```bash
curl -X POST http://localhost:90/transcriptions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@audio.wav" \
  -F "batch_size=16" \
  -F "diarize=true"
```

**Response:**
```json
{
  "transcription": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, how can I help you?",
      "speaker": "Speaker 1"
    }
  ]
}
```

### Change Model

```
POST /transcriptions/model
```

**Form Parameters:**
- `model_name`: Model ID (default: parakeet-tdt-0.6b-v2)

### Health Check

```
GET /
```

**Response:** `"Parakeet API - IntouchCX"`

## Configuration

### OIDC Setup

Update `app/client_secrets.json`:

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

### uWSGI Configuration

Edit `app/app.ini`:

```ini
[uwsgi]
wsgi-file = run.py
pidfile=/tmp/project-master.pid
processes = 1
threads = 7
http = :90
http-timeout = 1000
```

### Model Configuration

Edit `app/services/parakeet_transcription_service.py`:

```python
model_name = "nvidia/parakeet-tdt-0.6b-v2"
```

## Architecture

### Structure

```
CrossbowASR/
├── app/
│   ├── __init__.py              # Blueprint registration
│   ├── app.py                   # Flask app + OIDC
│   ├── run.py                   # Entry point
│   ├── app.ini                  # uWSGI config
│   ├── api/                     # Controllers
│   │   ├── home_controller.py
│   │   └── transcription_controller.py
│   └── services/                # Business logic
│       ├── parakeet_transcription_service.py
│       └── diarization_service.py
├── deployment/                  # Kubernetes configs
├── Dockerfile
└── requirements.txt
```

### Components

- **Flask**: Web framework with Blueprint architecture
- **Flask-OIDC**: Authentication middleware
- **uWSGI**: Application server
- **NeMo**: Transcription and diarization
- **Parakeet-TDT**: ASR model
- **CUDA**: GPU acceleration

## Deployment

### Kubernetes Resources

**Base:**
- Deployment with GPU tolerations
- ClusterIP Service (port 80→90)
- Resource limits: 4-28Gi memory, 2-7 CPU cores

**Overlays:**
- Development environment
- Production environment

**Namespace:** superpunch  
**Service Name:** crossbow-parakeet-service

### Deploy

```bash
# Development
kubectl apply -k deployment/overlays/development

# Production
kubectl apply -k deployment/overlays/production

# Check status
kubectl get pods -n development
kubectl logs -f deployment/crossbow-parakeet-service -n development
```

## Requirements

- NVIDIA GPU with CUDA support (recommended)
- Python 3.10+
- CUDA 12.2+
- 4GB+ RAM (28GB for production)
- OIDC provider for authentication

## Migration from Whisper

This service is designed as a drop-in replacement for the Whisper service:

- ✅ Same API structure
- ✅ Same deployment configuration
- ✅ Same authentication mechanism
- ✅ Same Kubernetes manifests structure

**Key Differences:**
- Transcription engine: Parakeet-TDT (instead of WhisperX)
- Diarization: NeMo-based (instead of WhisperX)
- No redaction endpoints (transcription/diarization only)

See [WHISPER_MIGRATION.md](WHISPER_MIGRATION.md) for detailed migration guide.

## Documentation

- [Whisper Migration Guide](WHISPER_MIGRATION.md) - Complete migration documentation
- [Docker Guide](docs/DOCKER_GUIDE.md) - Docker usage
- [Response Formats](docs/RESPONSE_FORMATS.md) - API response formats
- [Deployment Guide](docs/DEPLOYMENT.md) - AWS deployment

## Performance

### CPU
- Transcription: ~5x real-time
- With diarization: ~10x real-time

### GPU (Recommended)
- Transcription: 50-100x faster
- Optimized for NVIDIA GPUs with CUDA

## Troubleshooting

### Container Logs
```bash
kubectl logs -f deployment/crossbow-parakeet-service -n development
```

### GPU Check
```bash
nvidia-smi
```

### OIDC Issues
- Verify `client_secrets.json` configuration
- Check token validity
- Ensure redirect URIs match

### Model Loading
- First run downloads model (~600MB)
- Subsequent runs use cached model
- Check `/mdl/` directory for cached models

## Support

For issues or questions:
1. Check deployment logs
2. Review uWSGI logs
3. Verify OIDC configuration
4. Check GPU availability

## License

Internal use - IntouchCX
