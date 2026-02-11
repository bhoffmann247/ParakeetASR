# GitHub Actions Setup Guide

## Why Your Workflow Didn't Run

The GitHub Actions workflow is configured to run automatically on:
- Push to `main` or `master` branch
- Push of tags starting with `v` (e.g., `v1.0.0`)
- Manual trigger via `workflow_dispatch`

## Troubleshooting Steps

### 1. Check Your Branch Name

```bash
# Check your current branch
git branch --show-current

# Check all branches
git branch -a
```

**Common issues:**
- Your default branch might be named differently (e.g., `develop`, `trunk`)
- You might be on a feature branch

### 2. Verify the Workflow File Exists in GitHub

The workflow file must be in the repository on GitHub:
```
.github/workflows/build-and-push.yml
```

Check if it's there:
```bash
# Verify file exists locally
ls -la .github/workflows/

# Check if it's committed
git status

# Check if it's pushed to GitHub
git log --oneline origin/main -- .github/workflows/build-and-push.yml
```

### 3. Check GitHub Actions Permissions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Under "Workflow permissions", ensure:
   - ✅ "Read and write permissions" is selected
   - ✅ "Allow GitHub Actions to create and approve pull requests" is checked (optional)

### 4. Check if Actions are Enabled

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. If you see "Workflows have been disabled", click **"I understand my workflows, go ahead and enable them"**

## Quick Fix Options

### Option 1: Push to Main/Master Branch

```bash
# If you're on a different branch, merge to main
git checkout main
git merge your-branch-name
git push origin main
```

### Option 2: Update Workflow to Match Your Branch

If your default branch is named differently (e.g., `develop`):

Edit `.github/workflows/build-and-push.yml`:
```yaml
on:
  push:
    branches: [ main, master, develop ]  # Add your branch name
    tags: [ 'v*' ]
  workflow_dispatch:
```

Then commit and push:
```bash
git add .github/workflows/build-and-push.yml
git commit -m "Update workflow to include develop branch"
git push
```

### Option 3: Manually Trigger the Workflow

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Build and Push to GHCR** workflow
4. Click **Run workflow** button
5. Select your branch
6. Click **Run workflow**

### Option 4: Create a Tag to Trigger Build

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

## Verify Workflow Ran Successfully

### Check Workflow Status

1. Go to GitHub → **Actions** tab
2. You should see your workflow run listed
3. Click on it to see the logs

### Check for Errors

Common errors and solutions:

**Error: "Resource not accessible by integration"**
- Fix: Enable write permissions (see Step 3 above)

**Error: "Dockerfile not found"**
- Fix: Ensure `Dockerfile.sagemaker` exists in repository root

**Error: "denied: permission_denied"**
- Fix: Package visibility or permissions issue
- Solution: Make package public or check token permissions

## After Successful Build

### Find Your Image

1. Go to your repository on GitHub
2. Look for **Packages** in the right sidebar
3. Click on your package
4. Copy the image URI: `ghcr.io/YOUR_USERNAME/YOUR_REPO/parakeet-transcription:latest`

### Make Package Public (Recommended)

1. Go to the package page
2. Click **Package settings**
3. Scroll to "Danger Zone"
4. Click **Change visibility** → **Public**
5. Confirm the change

### Test the Image

```bash
# Pull the image
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/parakeet-transcription:latest

# Test locally
docker run -p 8080:8080 ghcr.io/YOUR_USERNAME/YOUR_REPO/parakeet-transcription:latest
```

## Manual Build (If Workflow Still Doesn't Work)

If you can't get GitHub Actions working, build and push manually:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build the image
docker build -f Dockerfile.sagemaker -t ghcr.io/YOUR_USERNAME/YOUR_REPO/parakeet-transcription:latest .

# Push to GHCR
docker push ghcr.io/YOUR_USERNAME/YOUR_REPO/parakeet-transcription:latest
```

To create a GitHub token:
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Select scopes: `write:packages`, `read:packages`, `delete:packages`
4. Copy the token

## Debugging Checklist

- [ ] Workflow file exists at `.github/workflows/build-and-push.yml`
- [ ] Workflow file is committed and pushed to GitHub
- [ ] Pushing to `main` or `master` branch (or updated workflow for your branch)
- [ ] GitHub Actions are enabled in repository settings
- [ ] Workflow permissions set to "Read and write"
- [ ] Repository is not a fork (forks have limited Actions access)
- [ ] `Dockerfile.sagemaker` exists in repository root

## Common Issues

### Issue: "No workflows found"
**Solution:** The workflow file isn't in the repository or isn't on the branch you're viewing
```bash
git add .github/workflows/build-and-push.yml
git commit -m "Add GitHub Actions workflow"
git push origin main
```

### Issue: Workflow runs but fails at "Build and push"
**Solution:** Check the logs for specific error. Common causes:
- Dockerfile syntax error
- Missing dependencies
- Insufficient disk space on runner

### Issue: "Package not found" when trying to pull
**Solution:** 
- Package might be private - make it public or authenticate
- Image name might be wrong - check exact name in Packages section

## Need Help?

If you're still stuck, check:
1. GitHub Actions logs (Actions tab → Click on workflow run → View logs)
2. Repository settings (Settings → Actions)
3. Package settings (Packages → Your package → Settings)

Or manually build and push the image as shown above.
