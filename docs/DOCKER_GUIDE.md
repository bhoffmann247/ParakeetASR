# Docker Guide

## Quick Start

### 1. Start Docker Desktop

### 2. Run the container
```powershell
.\run-docker.ps1
```

### 3. Test it
```powershell
curl http://localhost:8000/health
```

That's it! API is at http://localhost:8000/docs

---

## Commands

```powershell
.\run-docker.ps1           # Start
.\run-docker.ps1 -Status   # Check status
.\run-docker.ps1 -Logs     # View logs
.\run-docker.ps1 -Restart  # Restart
.\run-docker.ps1 -Stop     # Stop
```

---

## Testing

Run the test suite:
```powershell
.\test-api.ps1
```

Or test manually:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=json" `
  -F "diarize=true"
```

---

## Manual Docker Commands

If you prefer not to use the script:

```powershell
# Build
docker build -t parakeet-api .

# Run
docker run -d --name parakeet-api -p 8000:8000 parakeet-api

# Stop
docker stop parakeet-api
docker rm parakeet-api
```

---

## Troubleshooting

### Container won't start
```powershell
docker logs parakeet-api
```

### Port already in use
```powershell
netstat -ano | findstr :8000
.\run-docker.ps1 -Stop
```

### Server not responding
Wait 2-3 minutes for model to load on first run (downloads ~600MB).

### Out of memory
```powershell
docker run -d --name parakeet-api -p 8000:8000 --memory=4g parakeet-api
```

---

## What to Expect

**First run:**
- Build: 5-10 minutes
- Model download: ~600MB
- Startup: 2-3 minutes

**Subsequent runs:**
- Startup: 30-60 seconds (model cached)

**Processing speed (CPU):**
- Transcription: ~5x real-time
- With diarization: ~10x real-time
- Example: 5-second audio = 25-50 seconds

**With GPU:** 50-100x faster

---

## API Usage

See [RESPONSE_FORMATS.md](RESPONSE_FORMATS.md) for all output formats.

**Basic transcription:**
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=json"
```

**With speaker diarization:**
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=json" `
  -F "diarize=true"
```

**SRT subtitles:**
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=srt"
```

**API Documentation:** http://localhost:8000/docs
