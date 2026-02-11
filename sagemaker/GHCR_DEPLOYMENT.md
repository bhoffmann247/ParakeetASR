# Deploy to SageMaker using GitHub Container Registry (GHCR)

This guide shows you how to deploy your Parakeet transcription service to AWS SageMaker using a Docker image hosted on GitHub Container Registry (GHCR) - no ECR required!

## Overview

1. Push your code to GitHub
2. GitHub Actions automatically builds and pushes Docker image to GHCR
3. Deploy to SageMaker using the GHCR image

## Prerequisites

- GitHub account
- GitHub repository for this project
- AWS credentials configured
- IAM role for SageMaker

## Step 1: Set Up GitHub Repository

### 1.1 Create GitHub Repository

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 1.2 Make Repository Public (or Configure Access)

**Option A: Public Repository (Easiest)**
- Go to your repo → Settings → Change visibility to Public
- GHCR images from public repos can be pulled without authentication

**Option B: Private Repository**
- Keep repo private
- You'll need to configure SageMaker to authenticate with GHCR (more complex)

## Step 2: Build and Push to GHCR

### Automatic (Recommended)

The GitHub Actions workflow will automatically build and push when you push to main:

```bash
git push origin main
```

Watch the build:
1. Go to your GitHub repo
2. Click "Actions" tab
3. Watch the "Build and Push to GHCR" workflow

### Manual (Alternative)

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build image
docker build -f Dockerfile.sagemaker -t ghcr.io/YOUR_USERNAME/parakeet-transcription:latest .

# Push to GHCR
docker push ghcr.io/YOUR_USERNAME/parakeet-transcription:latest
```

## Step 3: Make GHCR Package Public

1. Go to https://github.com/YOUR_USERNAME?tab=packages
2. Click on "parakeet-transcription"
3. Click "Package settings"
4. Scroll to "Danger Zone"
5. Click "Change visibility" → "Public"

This allows SageMaker to pull the image without authentication.

## Step 4: Deploy to SageMaker

```powershell
cd sagemaker

python deploy_ghcr.py \
  --image ghcr.io/YOUR_USERNAME/parakeet-transcription:latest \
  --role AmazonSageMaker-ExecutionRole-20251022T094938 \
  --instance-type ml.g5.2xlarge \
  --endpoint-name parakeet-transcription
```

Replace:
- `YOUR_USERNAME` with your GitHub username
- Role name with your actual role

## Step 5: Test

```powershell
python test_endpoint.py \
  --endpoint parakeet-transcription \
  --audio ..\tests\Input\ContactCenter\103046_1000780789-21-00-01.wav
```

## Complete Example

```powershell
# 1. Push to GitHub
git add .
git commit -m "Add SageMaker GHCR deployment"
git push origin main

# 2. Wait for GitHub Actions to build (check Actions tab)

# 3. Make package public (see Step 3 above)

# 4. Deploy to SageMaker
python deploy_ghcr.py \
  --image ghcr.io/yourusername/parakeet-transcription:latest \
  --role arn:aws:iam::716828325351:role/service-role/AmazonSageMaker-ExecutionRole-20251022T094938 \
  --instance-type ml.g5.2xlarge

# 5. Test
python test_endpoint.py --endpoint parakeet-transcription --audio test.wav
```

## Updating the Deployment

To update your deployment with new code:

```powershell
# 1. Make changes to your code
# 2. Commit and push
git add .
git commit -m "Update transcription logic"
git push origin main

# 3. Wait for GitHub Actions to build new image

# 4. Redeploy (same endpoint name = update)
python deploy_ghcr.py \
  --image ghcr.io/yourusername/parakeet-transcription:latest \
  --role YourRole \
  --endpoint-name parakeet-transcription
```

## Troubleshooting

### "ImagePullBackOff" or "Cannot pull image"

**Solution**: Make sure the GHCR package is public:
1. Go to https://github.com/YOUR_USERNAME?tab=packages
2. Click your package → Package settings
3. Change visibility to Public

### "Role cannot be assumed"

**Solution**: Check the IAM role has:
- Trust policy allowing `sagemaker.amazonaws.com`
- Permissions to create endpoints

### Build fails in GitHub Actions

**Solution**: Check the Actions tab for error logs. Common issues:
- Missing files referenced in Dockerfile
- Syntax errors in Dockerfile

### Endpoint returns 500 error

**Solution**: Check CloudWatch logs:
```powershell
python check_logs.py parakeet-transcription
```

## Cost

**ml.g5.2xlarge**: $1.52/hour (~$1,095/month if running 24/7)

Remember to delete when not in use:
```powershell
aws sagemaker delete-endpoint --endpoint-name parakeet-transcription --region ca-central-1
```

## Advantages of GHCR Approach

✅ No ECR required
✅ Free hosting on GitHub
✅ Automatic builds with GitHub Actions
✅ Version control for images
✅ Works with your existing Docker setup
✅ No dependency conflicts (uses your exact environment)

## Files Created

- `Dockerfile.sagemaker` - SageMaker-compatible Dockerfile
- `sagemaker/serve.py` - Flask server for SageMaker
- `.github/workflows/build-and-push.yml` - Auto-build workflow
- `sagemaker/deploy_ghcr.py` - Deployment script

## Next Steps

1. Push code to GitHub
2. Wait for build to complete
3. Make GHCR package public
4. Deploy with `deploy_ghcr.py`
5. Test with `test_endpoint.py`

That's it! Your transcription service is now running on SageMaker using GHCR! 🎉
