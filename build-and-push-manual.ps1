# Manual build and push to GHCR (PowerShell version)
# Use this if GitHub Actions isn't working

param(
    [string]$GitHubUsername,
    [string]$GitHubToken,
    [string]$RepositoryName
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Manual Build and Push to GHCR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check for GitHub token
if (-not $GitHubToken) {
    $GitHubToken = $env:GITHUB_TOKEN
}

if (-not $GitHubToken) {
    Write-Host "`nError: GitHub token not provided" -ForegroundColor Red
    Write-Host "`nTo create a token:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/settings/tokens"
    Write-Host "2. Generate new token (classic)"
    Write-Host "3. Select scopes: write:packages, read:packages"
    Write-Host "4. Copy the token"
    Write-Host "`nThen run:" -ForegroundColor Yellow
    Write-Host '  $env:GITHUB_TOKEN = "ghp_your_token_here"' -ForegroundColor White
    Write-Host "  .\build-and-push-manual.ps1" -ForegroundColor White
    Write-Host "`nOr pass as parameter:" -ForegroundColor Yellow
    Write-Host "  .\build-and-push-manual.ps1 -GitHubToken ghp_your_token" -ForegroundColor White
    exit 1
}

# Get GitHub username
if (-not $GitHubUsername) {
    $GitHubUsername = Read-Host "Enter your GitHub username"
}

if (-not $GitHubUsername) {
    Write-Host "Error: GitHub username is required" -ForegroundColor Red
    exit 1
}

# Get repository name
if (-not $RepositoryName) {
    try {
        $gitRoot = git rev-parse --show-toplevel 2>$null
        $RepositoryName = Split-Path -Leaf $gitRoot
    } catch {
        $RepositoryName = Split-Path -Leaf (Get-Location)
    }
    
    $input = Read-Host "Enter repository name [$RepositoryName]"
    if ($input) {
        $RepositoryName = $input
    }
}

# Construct image name
$ImageName = "ghcr.io/$GitHubUsername/$RepositoryName`:latest"

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  Username: $GitHubUsername"
Write-Host "  Repository: $RepositoryName"
Write-Host "  Image: $ImageName"
Write-Host ""

$confirmation = Read-Host "Continue? (y/n)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Login to GHCR
Write-Host "`nLogging in to GHCR..." -ForegroundColor Yellow
$GitHubToken | docker login ghcr.io -u $GitHubUsername --password-stdin

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to login to GHCR" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Logged in successfully" -ForegroundColor Green

# Build the image
Write-Host "`nBuilding Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.sagemaker -t $ImageName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build image" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Image built successfully" -ForegroundColor Green

# Push to GHCR
Write-Host "`nPushing to GHCR..." -ForegroundColor Yellow
docker push $ImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to push image" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Image pushed successfully" -ForegroundColor Green

# Success message
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "✓ Build and Push Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Image: $ImageName" -ForegroundColor White
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Make package public (if needed):"
Write-Host "   https://github.com/$GitHubUsername/$RepositoryName/packages"
Write-Host ""
Write-Host "2. Deploy to SageMaker:"
Write-Host "   cd sagemaker"
Write-Host "   python deploy_simple.py \"
Write-Host "     --image $ImageName \"
Write-Host "     --role YOUR_ROLE_ARN"
Write-Host ""
Write-Host "3. Test locally:"
Write-Host "   docker run -p 8080:8080 $ImageName"
Write-Host "==========================================" -ForegroundColor Cyan
