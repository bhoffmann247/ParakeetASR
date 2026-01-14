# Docker Quick Start Guide

Get the Parakeet Transcription API running in Docker in 3 steps.

## Prerequisites

1. **Start Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
2. Ensure you have at least 8GB RAM available

## Quick Start

### Option 1: Automated Test (Recommended)

**Windows (PowerShell):**
```powershell
.\test-docker.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x test-docker.sh
./test-docker.sh
```

This script will:
- ✅ Build the Docker image
- ✅ Start the container
- ✅ Run health checks
- ✅ Test the API endpoints
- ✅ Test transcription with diarization

### Option 2: Manual Steps

**1. Build the image:**
```bash
docker build -t parakeet-api .
```

**2. Start the container:**
```bash
docker-compose up -d
```

**3. Check if it's running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### List Models
```bash
curl http://localhost:8000/v1/models
```

### Transcribe Audio (with Speaker Diarization)
```bash
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" \
  -F "model=parakeet-tdt-0.6b-v2" \
  -F "response_format=json" \
  -F "enable_diarization=true"
```

### Interactive API Documentation
Open in your browser:
```
http://localhost:8000/docs
```

## Managing the Container

### View Logs
```bash
docker logs parakeet-api
```

### Follow Logs (Real-time)
```bash
docker logs -f parakeet-api
```

### Stop Container
```bash
docker-compose down
```

### Restart Container
```bash
docker-compose restart
```

### Remove Everything
```bash
docker-compose down
docker rmi parakeet-api
docker volume rm parakeet-transcription-api_model-cache
```

## Troubleshooting

### Docker not running
**Error:** `error during connect: ... cannot find the file specified`

**Solution:** Start Docker Desktop and wait for it to fully initialize (green icon in system tray)

### Container won't start
**Check logs:**
```bash
docker logs parakeet-api
```

**Common issues:**
- Insufficient memory (needs 4GB minimum, 8GB recommended)
- Port 8000 already in use
- Missing dependencies in Dockerfile

### API not responding
**Wait longer:** First startup takes 30-60 seconds to load models

**Check health:**
```bash
curl http://localhost:8000/health
```

**Check container status:**
```bash
docker ps
```

### Slow transcription
This is normal on CPU. Processing time is typically:
- 2-4 minutes for a 6-minute audio file
- GPU deployment will be much faster (see DEPLOYMENT.md)

## Next Steps

- **Production Deployment:** See `docs/DEPLOYMENT.md` for AWS deployment options
- **Configuration:** Edit `config.py` for custom settings
- **API Documentation:** Visit http://localhost:8000/docs for interactive API docs

## File Structure

```
.
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore          # Files to exclude from build
├── test-docker.ps1        # Windows test script
├── test-docker.sh         # Linux/Mac test script
└── docs/
    └── DEPLOYMENT.md      # Full deployment guide
```

## Performance Notes

### Current Setup (CPU)
- Processing time: ~2-4 minutes per 6-minute audio
- Memory usage: 4-6GB
- CPU usage: 100% during processing

### GPU Setup (Future)
For production with high throughput, consider:
- GPU-enabled Docker image (Dockerfile.gpu)
- AWS EC2 g4dn instances
- 10-20x faster processing

See `docs/DEPLOYMENT.md` for GPU deployment instructions.

## Support

- **Logs:** `docker logs parakeet-api`
- **Documentation:** `docs/` directory
- **NeMo Docs:** https://docs.nvidia.com/deeplearning/nemo/
