#!/bin/bash
# Manual build and push to GHCR
# Use this if GitHub Actions isn't working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Manual Build and Push to GHCR"
echo "=========================================="

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable not set${NC}"
    echo ""
    echo "To create a token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Generate new token (classic)"
    echo "3. Select scopes: write:packages, read:packages"
    echo "4. Copy the token"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN=ghp_your_token_here"
    echo "  ./build-and-push-manual.sh"
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}Error: GitHub username is required${NC}"
    exit 1
fi

# Get repository name
REPO_NAME=$(basename $(git rev-parse --show-toplevel))
read -p "Enter repository name [$REPO_NAME]: " INPUT_REPO
REPO_NAME=${INPUT_REPO:-$REPO_NAME}

# Construct image name
IMAGE_NAME="ghcr.io/${GITHUB_USERNAME}/${REPO_NAME}:latest"

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Username: $GITHUB_USERNAME"
echo "  Repository: $REPO_NAME"
echo "  Image: $IMAGE_NAME"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Login to GHCR
echo ""
echo -e "${YELLOW}Logging in to GHCR...${NC}"
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to login to GHCR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Logged in successfully${NC}"

# Build the image
echo ""
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f Dockerfile.sagemaker -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build image${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Image built successfully${NC}"

# Push to GHCR
echo ""
echo -e "${YELLOW}Pushing to GHCR...${NC}"
docker push $IMAGE_NAME

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to push image${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Image pushed successfully${NC}"

# Success message
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Build and Push Complete!${NC}"
echo "=========================================="
echo "Image: $IMAGE_NAME"
echo ""
echo "Next steps:"
echo "1. Make package public (if needed):"
echo "   https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/packages"
echo ""
echo "2. Deploy to SageMaker:"
echo "   cd sagemaker"
echo "   python deploy_simple.py \\"
echo "     --image $IMAGE_NAME \\"
echo "     --role YOUR_ROLE_ARN"
echo ""
echo "3. Test locally:"
echo "   docker run -p 8080:8080 $IMAGE_NAME"
echo "=========================================="
