# Git Workflow for Staging/Production

## Branch Strategy

```
main (or master)     → Production environment
staging (or develop) → Staging environment  
feature/*           → Feature branches
hotfix/*           → Emergency fixes
```

## Workflow

### 1. Feature Development
```bash
# Create feature branch from staging
git checkout staging
git pull origin staging
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push feature branch
git push origin feature/new-feature
```

### 2. Deploy to Staging
```bash
# Merge feature to staging
git checkout staging
git merge feature/new-feature
git push origin staging

# On server
ssh root@your-server-ip
/opt/marine-seguros/deploy-staging.sh
```

### 3. Test in Staging
- Access: http://staging.your-domain.com
- Test all functionality
- Monitor logs: `docker logs -f marine-seguros-staging`

### 4. Deploy to Production
```bash
# After staging tests pass
git checkout main
git merge staging
git push origin main

# On server
ssh root@your-server-ip
/opt/marine-seguros/deploy-production.sh
```

### 5. Hotfix Process
```bash
# For urgent production fixes
git checkout main
git checkout -b hotfix/critical-fix

# Make fix and test locally
git add .
git commit -m "Fix: critical issue"

# Deploy directly to production
git checkout main
git merge hotfix/critical-fix
git push origin main

# Also merge back to staging
git checkout staging
git merge hotfix/critical-fix
git push origin staging
```

## Environment-Specific Files

### Staging Override
Create `vultr-deploy/.env.staging` for staging-specific configs:
```env
LOG_LEVEL=debug
ENABLE_DEBUG_MODE=true
# Any staging-specific settings
```

### Production Override
Create `vultr-deploy/.env.production` for production-specific configs:
```env
LOG_LEVEL=info
ENABLE_DEBUG_MODE=false
# Any production-specific settings
```

## Automated Deployment with GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Vultr

on:
  push:
    branches:
      - staging
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to Server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.VULTR_HOST }}
        username: ${{ secrets.VULTR_USER }}
        key: ${{ secrets.VULTR_SSH_KEY }}
        script: |
          if [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
            /opt/marine-seguros/deploy-staging.sh
          elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            /opt/marine-seguros/deploy-production.sh
          fi
```

## Quick Commands

### Check Environment Status
```bash
# On server
/opt/marine-seguros/compare-envs.sh
```

### View Logs
```bash
# Staging
docker logs -f marine-seguros-staging

# Production
docker logs -f marine-seguros
```

### Rollback
```bash
# Staging
cd /opt/marine-seguros/staging/app
git checkout HEAD~1
/opt/marine-seguros/deploy-staging.sh

# Production (with caution!)
cd /opt/marine-seguros/app
git checkout HEAD~1
/opt/marine-seguros/deploy-production.sh
```