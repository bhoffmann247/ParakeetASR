# Security Checklist Before Making Repository Public

## ✅ Fixed Issues

- [x] Removed AWS account ID from `sagemaker/GHCR_DEPLOYMENT.md`
- [x] Updated `.gitignore` to prevent future secret commits

## ⚠️ Items to Review (Your Decision)

### Company-Specific Information

The following company-specific references exist in the codebase. Decide if you want to keep or remove them:

1. **Company Name: "IntouchCX"**
   - `README.md` line 131: Response message `"Parakeet API - IntouchCX"`
   - `README.md` line 357: License section `Internal use - IntouchCX`
   - `app/api/home_controller.py` line 8: API response

   **Recommendation:** Change to generic name or remove if making fully open source

2. **Internal Infrastructure References**
   - `deployment/base/kustomization.yaml`: `nexus-docker.shared.intouchcx.cloud`
   - `deployment/base/deployment_service.yaml`: `nexus-cred` secret reference
   - `buildAgent.yaml`: Internal Jenkins configuration
   - Namespace: `superpunch`

   **Recommendation:** These are Kubernetes configs for your internal deployment. Consider:
   - Keep them as examples but add note they're company-specific
   - Move to a separate private repo
   - Replace with generic examples

### Safe Files (Placeholders Only)

- ✅ `app/client_secrets.json` - Contains only placeholder values, safe to publish

## 🔒 Additional Security Recommendations

### Before Publishing:

1. **Review Git History**
   ```bash
   # Check if any secrets were committed in the past
   git log --all --full-history --source -- '*secret*' '*credential*' '*.pem' '*.key'
   ```

2. **Scan for Secrets**
   ```bash
   # Use git-secrets or similar tool
   git secrets --scan
   
   # Or use gitleaks
   gitleaks detect --source . --verbose
   ```

3. **Remove Sensitive History (if needed)**
   ```bash
   # If you find secrets in git history, use BFG Repo-Cleaner or git-filter-repo
   # WARNING: This rewrites history
   git filter-repo --path app/client_secrets.json --invert-paths
   ```

### After Publishing:

1. **Add Security Policy**
   - Create `SECURITY.md` with vulnerability reporting instructions
   - Add contact information for security issues

2. **Enable GitHub Security Features**
   - Enable Dependabot alerts
   - Enable secret scanning
   - Enable code scanning (CodeQL)

3. **Monitor for Exposed Secrets**
   - Set up alerts for exposed credentials
   - Regularly audit dependencies

4. **Document Security Practices**
   - Add authentication requirements to README
   - Document secure deployment practices
   - Include security best practices in deployment guides

## 📝 Recommended Changes Before Publishing

### Option 1: Make Fully Generic (Open Source)

```bash
# Remove company-specific references
sed -i 's/IntouchCX/YourCompany/g' README.md app/api/home_controller.py
sed -i 's/Internal use - IntouchCX/MIT License/g' README.md

# Add generic Kubernetes examples
# Move internal configs to deployment/examples/
```

### Option 2: Keep Company References (Internal Tool Made Public)

Add a note to README:
```markdown
## Note

This is an internal tool developed by IntouchCX and made available as open source.
The Kubernetes deployment configurations are specific to our infrastructure and 
should be adapted for your environment.
```

### Option 3: Separate Public and Private Configs

```bash
# Move internal configs to a separate private repo
mkdir ../parakeet-internal-configs
mv deployment/ ../parakeet-internal-configs/
mv buildAgent.yaml ../parakeet-internal-configs/

# Create generic examples in this repo
mkdir deployment-examples/
# Add generic Kubernetes configs
```

## ✅ Final Checklist

Before making the repository public:

- [ ] Fixed AWS account ID exposure
- [ ] Decided on company name references (keep/remove/genericize)
- [ ] Reviewed internal infrastructure references
- [ ] Scanned git history for secrets
- [ ] Updated LICENSE file
- [ ] Added SECURITY.md
- [ ] Reviewed all documentation for sensitive info
- [ ] Tested that placeholder configs work
- [ ] Added contributing guidelines (if accepting contributions)
- [ ] Set up GitHub security features

## 🚨 If You Find Exposed Secrets

If you discover that secrets were already committed:

1. **Immediately rotate the exposed credentials**
   - AWS keys
   - GitHub tokens
   - OIDC client secrets
   - Any API keys

2. **Clean git history** (before making public)
   ```bash
   # Use BFG Repo-Cleaner
   bfg --delete-files client_secrets.json
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **Force push cleaned history**
   ```bash
   git push --force --all
   ```

## 📞 Questions?

If you're unsure about any item, err on the side of caution:
- Remove it
- Make it generic
- Keep the repo private until resolved
