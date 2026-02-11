# SageMaker Deployment via GitHub Container Registry (GHCR)

Deploy your Parakeet transcription service to AWS SageMaker using GitHub Container Registry - **no ECR required!**

## Quick Start

See **[GHCR_QUICKSTART.md](GHCR_QUICKSTART.md)** for 5-step deployment guide.

## Files in This Directory

### Deployment Scripts
- **deploy_ghcr.py** - Deploy to SageMaker from GHCR image
- **serve.py** - Flask server for SageMaker endpoints
- **test_endpoint.py** - Test deployed endpoints
- **example_client.py** - Python client library
- **check_logs.py** - View CloudWatch logs

### Documentation
- **GHCR_QUICKSTART.md** - 5-step quick start guide ⭐ Start here!
- **GHCR_DEPLOYMENT.md** - Complete deployment guide
- **README.md** - This file

## How It Works

1. **Push code to GitHub** → GitHub Actions builds Docker image
2. **Image stored in GHCR** → Free, public container registry  
3. **Deploy to SageMaker** → Pull image from GHCR
4. **Transcribe audio** → GPU-powered endpoint ready!

## Prerequisites

- GitHub account and repository
- AWS account with SageMaker access
- IAM role for SageMaker
- AWS credentials configured

## Deployment Steps

```powershell
# 1. Push to GitHub (triggers auto-build)
git push origin main

# 2. Make GHCR package public
# (See GHCR_QUICKSTART.md Step 3)

# 3. Deploy to SageMaker
python deploy_ghcr.py \
  --image ghcr.io/YOUR_USERNAME/parakeet-transcription:latest \
  --role YOUR_SAGEMAKER_ROLE

# 4. Test
python test_endpoint.py --endpoint ENDPOINT_NAME --audio test.wav
```

## Cost

**ml.g5.2xlarge**: $1.52/hour (~$1,095/month if running 24/7)

Delete when not in use:
```powershell
aws sagemaker delete-endpoint --endpoint-name ENDPOINT_NAME --region ca-central-1
```

## Advantages

✅ No ECR required - uses GitHub Container Registry  
✅ No dependency conflicts - uses your working Docker setup  
✅ Automatic builds - GitHub Actions handles it  
✅ Free hosting - GHCR is free  
✅ Version control - track image versions  

## Support

- **Quick start**: [GHCR_QUICKSTART.md](GHCR_QUICKSTART.md)
- **Full guide**: [GHCR_DEPLOYMENT.md](GHCR_DEPLOYMENT.md)
- **Check logs**: `python check_logs.py ENDPOINT_NAME`
- **Test endpoint**: `python test_endpoint.py --endpoint ENDPOINT_NAME --audio file.wav`

## Architecture

```
GitHub Repo
    ↓ (push)
GitHub Actions
    ↓ (build)
GitHub Container Registry (GHCR)
    ↓ (pull)
AWS SageMaker Endpoint (GPU)
    ↓ (invoke)
Transcription Results
```

## Next Steps

1. Read [GHCR_QUICKSTART.md](GHCR_QUICKSTART.md)
2. Push code to GitHub
3. Deploy to SageMaker
4. Start transcribing!
