# Branch Setup for Marine Seguros

## Current Branch Structure

- **Production**: `devStaging` branch → Railway production
- **Staging**: `staging` branch → Railway staging (to be created)
- **Development**: feature branches → Local development

## Create Staging Branch

Since you're currently on `environmentStuff` branch with the staging setup changes:

```bash
# First, commit your current changes
git add .
git commit -m "Add staging environment setup"

# Create and push staging branch from current work
git checkout -b staging
git push -u origin staging

# Push your environment changes to devStaging for production
git checkout devStaging
git pull origin devStaging
git merge environmentStuff
git push origin devStaging
```

## Configure Railway Services

### Production Service (existing):
- Branch: `devStaging`
- Service name: `marine-seguros`
- Auto-deploy: ON

### Staging Service (new):
1. Create new service in Railway
2. Set branch to: `staging`
3. Service name: `marine-seguros-staging`
4. Auto-deploy: ON

## Recommended Workflow

```
feature branch → staging → devStaging
     ↓             ↓           ↓
Local testing   Staging    Production
```

### Example:
```bash
# 1. Work on feature
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "Add new feature"

# 2. Test in staging
git checkout staging
git merge feature/new-feature
git push origin staging
# Auto-deploys to staging

# 3. After testing, deploy to production
git checkout devStaging
git merge staging
git push origin devStaging
# Auto-deploys to production
```

## GitHub Actions Summary

- **Staging deployment**: Triggers on push to `staging` branch
- **Production deployment**: Triggers on push to `devStaging` branch

Both include automated testing before deployment.