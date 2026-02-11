# GHCR Deployment - Quick Start

Deploy to SageMaker using GitHub Container Registry in 5 steps.

## Step 1: Push to GitHub (2 minutes)

```bash
# If not already a git repo
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

## Step 2: Wait for Build (5 minutes)

1. Go to your GitHub repo
2. Click "Actions" tab
3. Watch "Build and Push to GHCR" workflow complete

## Step 3: Make Package Public (30 seconds)

1. Go to https://github.com/YOUR_USERNAME?tab=packages
2. Click "parakeet-transcription"
3. Package settings → Change visibility → Public

## Step 4: Deploy to SageMaker (10 minutes)

```powershell
cd sagemaker

python deploy_ghcr.py \
  --image ghcr.io/YOUR_USERNAME/parakeet-transcription:latest \
  --role AmazonSageMaker-ExecutionRole-20251022T094938
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 5: Test (30 seconds)

```powershell
python test_endpoint.py \
  --endpoint parakeet-ghcr-TIMESTAMP \
  --audio ..\tests\Input\ContactCenter\103046_1000780789-21-00-01.wav
```

## Done! 🎉

Your transcription service is live on SageMaker!

## What Just Happened?

1. ✅ GitHub Actions built your Docker image
2. ✅ Image pushed to GitHub Container Registry
3. ✅ SageMaker pulled image from GHCR
4. ✅ Endpoint deployed with GPU support
5. ✅ Ready to transcribe audio!

## Cost

**ml.g5.2xlarge**: $1.52/hour

Delete when done:
```powershell
aws sagemaker delete-endpoint --endpoint-name parakeet-ghcr-TIMESTAMP --region ca-central-1
```

## Troubleshooting

**Can't pull image?**
→ Make sure GHCR package is public (Step 3)

**Build failed?**
→ Check GitHub Actions logs

**Endpoint error?**
→ Run: `python check_logs.py parakeet-ghcr-TIMESTAMP`

## Full Guide

See [GHCR_DEPLOYMENT.md](GHCR_DEPLOYMENT.md) for complete documentation.
