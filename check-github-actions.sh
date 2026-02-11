#!/bin/bash
# Diagnostic script to check GitHub Actions setup

echo "=========================================="
echo "GitHub Actions Diagnostic"
echo "=========================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi
echo "✓ In a git repository"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "✓ Current branch: $CURRENT_BRANCH"

# Check if workflow file exists
if [ -f ".github/workflows/build-and-push.yml" ]; then
    echo "✓ Workflow file exists"
else
    echo "❌ Workflow file not found at .github/workflows/build-and-push.yml"
    exit 1
fi

# Check if workflow file is committed
if git ls-files --error-unmatch .github/workflows/build-and-push.yml > /dev/null 2>&1; then
    echo "✓ Workflow file is committed"
else
    echo "❌ Workflow file is not committed"
    echo "   Run: git add .github/workflows/build-and-push.yml && git commit -m 'Add workflow'"
    exit 1
fi

# Check if Dockerfile exists
if [ -f "Dockerfile.sagemaker" ]; then
    echo "✓ Dockerfile.sagemaker exists"
else
    echo "❌ Dockerfile.sagemaker not found"
    exit 1
fi

# Check if Dockerfile is committed
if git ls-files --error-unmatch Dockerfile.sagemaker > /dev/null 2>&1; then
    echo "✓ Dockerfile.sagemaker is committed"
else
    echo "❌ Dockerfile.sagemaker is not committed"
    echo "   Run: git add Dockerfile.sagemaker && git commit -m 'Add Dockerfile'"
fi

# Check remote
REMOTE_URL=$(git config --get remote.origin.url)
if [ -z "$REMOTE_URL" ]; then
    echo "❌ No remote repository configured"
    exit 1
fi
echo "✓ Remote: $REMOTE_URL"

# Check if changes are pushed
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/$CURRENT_BRANCH 2>/dev/null)

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo "✓ Local and remote are in sync"
else
    echo "⚠️  Local and remote are out of sync"
    echo "   Run: git push origin $CURRENT_BRANCH"
fi

# Check workflow triggers
echo ""
echo "Workflow will trigger on:"
grep -A 10 "^on:" .github/workflows/build-and-push.yml | grep -E "branches:|tags:" | sed 's/^/  /'

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "To trigger the workflow:"
echo ""
echo "Option 1: Push to a trigger branch"
if [[ "$CURRENT_BRANCH" =~ ^(main|master|develop)$ ]]; then
    echo "  ✓ You're on $CURRENT_BRANCH (will trigger)"
    echo "  Run: git push origin $CURRENT_BRANCH"
else
    echo "  ⚠️  You're on $CURRENT_BRANCH (won't trigger)"
    echo "  Switch to main: git checkout main && git push"
fi
echo ""
echo "Option 2: Create a tag"
echo "  git tag v1.0.0"
echo "  git push origin v1.0.0"
echo ""
echo "Option 3: Manual trigger"
echo "  Go to: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo "  Click 'Build and Push to GHCR' → 'Run workflow'"
echo ""
echo "Option 4: Build manually"
echo "  ./build-and-push-manual.sh"
echo ""
echo "=========================================="
