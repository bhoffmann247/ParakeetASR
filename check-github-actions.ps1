# Diagnostic script to check GitHub Actions setup (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "GitHub Actions Diagnostic" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
try {
    git rev-parse --git-dir 2>$null | Out-Null
    Write-Host "✓ In a git repository" -ForegroundColor Green
} catch {
    Write-Host "❌ Not in a git repository" -ForegroundColor Red
    exit 1
}

# Check current branch
$currentBranch = git branch --show-current
Write-Host "✓ Current branch: $currentBranch" -ForegroundColor Green

# Check if workflow file exists
if (Test-Path ".github/workflows/build-and-push.yml") {
    Write-Host "✓ Workflow file exists" -ForegroundColor Green
} else {
    Write-Host "❌ Workflow file not found at .github/workflows/build-and-push.yml" -ForegroundColor Red
    exit 1
}

# Check if workflow file is committed
try {
    git ls-files --error-unmatch .github/workflows/build-and-push.yml 2>$null | Out-Null
    Write-Host "✓ Workflow file is committed" -ForegroundColor Green
} catch {
    Write-Host "❌ Workflow file is not committed" -ForegroundColor Red
    Write-Host "   Run: git add .github/workflows/build-and-push.yml; git commit -m 'Add workflow'" -ForegroundColor Yellow
    exit 1
}

# Check if Dockerfile exists
if (Test-Path "Dockerfile.sagemaker") {
    Write-Host "✓ Dockerfile.sagemaker exists" -ForegroundColor Green
} else {
    Write-Host "❌ Dockerfile.sagemaker not found" -ForegroundColor Red
    exit 1
}

# Check if Dockerfile is committed
try {
    git ls-files --error-unmatch Dockerfile.sagemaker 2>$null | Out-Null
    Write-Host "✓ Dockerfile.sagemaker is committed" -ForegroundColor Green
} catch {
    Write-Host "❌ Dockerfile.sagemaker is not committed" -ForegroundColor Red
    Write-Host "   Run: git add Dockerfile.sagemaker; git commit -m 'Add Dockerfile'" -ForegroundColor Yellow
}

# Check remote
$remoteUrl = git config --get remote.origin.url
if ($remoteUrl) {
    Write-Host "✓ Remote: $remoteUrl" -ForegroundColor Green
} else {
    Write-Host "❌ No remote repository configured" -ForegroundColor Red
    exit 1
}

# Check if changes are pushed
$localCommit = git rev-parse HEAD
$remoteCommit = git rev-parse "origin/$currentBranch" 2>$null

if ($localCommit -eq $remoteCommit) {
    Write-Host "✓ Local and remote are in sync" -ForegroundColor Green
} else {
    Write-Host "⚠️  Local and remote are out of sync" -ForegroundColor Yellow
    Write-Host "   Run: git push origin $currentBranch" -ForegroundColor Yellow
}

# Check workflow triggers
Write-Host "`nWorkflow will trigger on:" -ForegroundColor Yellow
$workflowContent = Get-Content ".github/workflows/build-and-push.yml" -Raw
if ($workflowContent -match "branches:\s*\n\s*-\s*(.+)") {
    Write-Host "  Branches: $($matches[1])" -ForegroundColor White
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "`nTo trigger the workflow:" -ForegroundColor Yellow
Write-Host ""

Write-Host "Option 1: Push to a trigger branch" -ForegroundColor White
if ($currentBranch -match "^(main|master|develop)$") {
    Write-Host "  ✓ You're on $currentBranch (will trigger)" -ForegroundColor Green
    Write-Host "  Run: git push origin $currentBranch" -ForegroundColor White
} else {
    Write-Host "  ⚠️  You're on $currentBranch (won't trigger)" -ForegroundColor Yellow
    Write-Host "  Switch to main: git checkout main; git push" -ForegroundColor White
}

Write-Host "`nOption 2: Create a tag" -ForegroundColor White
Write-Host "  git tag v1.0.0" -ForegroundColor Gray
Write-Host "  git push origin v1.0.0" -ForegroundColor Gray

Write-Host "`nOption 3: Manual trigger" -ForegroundColor White
$repoPath = $remoteUrl -replace '.*github\.com[:/](.*)\.git', '$1'
Write-Host "  Go to: https://github.com/$repoPath/actions" -ForegroundColor Gray
Write-Host "  Click 'Build and Push to GHCR' → 'Run workflow'" -ForegroundColor Gray

Write-Host "`nOption 4: Build manually" -ForegroundColor White
Write-Host "  .\build-and-push-manual.ps1" -ForegroundColor Gray

Write-Host "`n==========================================" -ForegroundColor Cyan
