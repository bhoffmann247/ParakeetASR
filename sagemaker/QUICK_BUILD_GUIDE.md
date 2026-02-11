# Quick Build Guide - Get Your Container to GHCR

## 🚀 Fastest Way: Run Diagnostic

**Windows:**
```powershell
.\check-github-actions.ps1
```

**Linux/Mac:**
```bash
chmod +x check-github-actions.sh
./check-github-actions.sh
```

This will tell you exactly what's wrong and how to fix it.

## 🔧 Common Issues & Quick Fixes

### Issue 1: Workflow Didn't Run

**Check your branch:**
```bash
git branch --show-current
```

**If not on main/master/develop:**
```bash
# Option A: Merge to main
git checkout main
git merge your-branch
git push origin main

# Option B: Push directly to main
git push origin your-branch:main
```

### Issue 2: Files Not Committed/Pushed

```bash
# Check status
git status

# Add and commit workflow files
git add .github/workflows/build-and-push.yml
git add Dockerfile.sagemaker
git add sagemaker/
git commit -m "Add SageMaker deployment files"

# Push to GitHub
git push origin main
```

### Issue 3: GitHub Actions Not Enabled

1. Go to your repo on GitHub
2. Click **Actions** tab
3. If disabled, click **"I understand my workflows, go ahead and enable them"**

### Issue 4: Permission Issues

1. Go to repo **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - Select **"Read and write permissions"**
   - Click **Save**

## 🎯 Three Ways to Build

### Method 1: Automatic (GitHub Actions) ⭐ Recommended

**Trigger by pushing to main:**
```bash
git push origin main
```

**Trigger by creating a tag:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

**Trigger manually:**
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
2. Click **"Build and Push to GHCR"**
3. Click **"Run workflow"** button
4. Select branch and click **"Run workflow"**

### Method 2: Manual Script (If Actions Don't Work)

**Windows:**
```powershell
# Set your GitHub token
$env:GITHUB_TOKEN = "ghp_your_token_here"

# Run the script
.\build-and-push-manual.ps1
```

**Linux/Mac:**
```bash
# Set your GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# Run the script
chmod +x build-and-push-manual.sh
./build-and-push-manual.sh
```

### Method 3: Pure Docker Commands

```bash
# 1. Create GitHub token at: https://github.com/settings/tokens
#    Scopes needed: write:packages, read:packages

# 2. Login to GHCR
echo YOUR_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 3. Build
docker build -f Dockerfile.sagemaker -t ghcr.io/YOUR_USERNAME/YOUR_REPO:latest .

# 4. Push
docker push ghcr.io/YOUR_USERNAME/YOUR_REPO:latest
```

## ✅ Verify Build Success

### Check GitHub Actions (Method 1)
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
2. Look for green checkmark ✓
3. Click on the workflow run to see logs

### Check Packages
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/packages`
2. You should see your package listed
3. Click on it to see details

### Test Locally
```bash
# Pull the image
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO:latest

# Run it
docker run -p 8080:8080 ghcr.io/YOUR_USERNAME/YOUR_REPO:latest

# Test health endpoint
curl http://localhost:8080/ping
```

## 📦 Make Package Public

After building, make your package public so SageMaker can pull it without authentication:

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/packages`
2. Click on your package
3. Click **"Package settings"** (bottom right)
4. Scroll to **"Danger Zone"**
5. Click **"Change visibility"** → **"Public"**
6. Type the repository name to confirm
7. Click **"I understand, change package visibility"**

## 🎉 Ready to Deploy!

Once your image is built and public:

```bash
cd sagemaker

python deploy_simple.py \
  --image ghcr.io/YOUR_USERNAME/YOUR_REPO:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole
```

## 🆘 Still Not Working?

Run the diagnostic script to see exactly what's wrong:

**Windows:**
```powershell
.\check-github-actions.ps1
```

**Linux/Mac:**
```bash
./check-github-actions.sh
```

Or check the detailed troubleshooting guide: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)

## 📝 Quick Checklist

- [ ] Workflow file exists: `.github/workflows/build-and-push.yml`
- [ ] Dockerfile exists: `Dockerfile.sagemaker`
- [ ] Files are committed: `git status` shows clean
- [ ] Files are pushed: `git push origin main`
- [ ] On correct branch: `main`, `master`, or `develop`
- [ ] GitHub Actions enabled in repo settings
- [ ] Workflow permissions set to "Read and write"
- [ ] Workflow ran successfully (check Actions tab)
- [ ] Package is public (or you have token for private)

## 🔗 Useful Links

- **Your Actions**: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
- **Your Packages**: `https://github.com/YOUR_USERNAME/YOUR_REPO/packages`
- **Create Token**: `https://github.com/settings/tokens`
- **Repo Settings**: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings`
