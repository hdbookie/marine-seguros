# Setting Up GitHub Actions for Railway Deployments

## Prerequisites

1. Railway account with services set up
2. GitHub repository access

## Step 1: Get Railway Token

1. **Go to Railway Dashboard**
2. **Click on your profile (top right)**
3. **Go to "Account Settings"**
4. **Navigate to "Tokens"**
5. **Click "Create Token"**
6. **Name it: `GitHub Actions Deploy`**
7. **Copy the token** (you'll see it only once!)

## Step 2: Add Token to GitHub Secrets

1. **Go to your GitHub repository**
2. **Settings → Secrets and variables → Actions**
3. **Click "New repository secret"**
4. **Add:**
   - Name: `RAILWAY_TOKEN`
   - Value: *paste your Railway token*
5. **Click "Add secret"**

## Step 3: Create Staging Branch (if needed)

```bash
git checkout -b staging
git push -u origin staging
```

## Step 4: Configure Branch Protection (Optional but Recommended)

### For main/master branch:
1. **Settings → Branches**
2. **Add rule for `main` or `master`**
3. **Enable:**
   - Require pull request before merging
   - Require status checks (deploy-staging)
   - Require branches to be up to date

### For staging branch:
1. **Add rule for `staging`**
2. **Enable:**
   - Require status checks to pass (test job)

## How It Works

### Staging Workflow:
1. Push to `staging` branch
2. GitHub Actions runs tests
3. If tests pass, deploys to Railway staging
4. View at: `https://marine-seguros-staging.up.railway.app`

### Production Workflow:
1. Push to `main` branch
2. GitHub Actions runs tests
3. If tests pass, deploys to Railway production
4. View at: `https://marine-seguros.up.railway.app`

## Workflow Features

- **Automated Testing**: Runs linting and import checks
- **Dependency Caching**: Speeds up builds
- **Conditional Deployment**: Only deploys on push, not PR
- **Environment Isolation**: Separate workflows for staging/production

## Monitoring Deployments

1. **GitHub Actions Tab**: View workflow runs
2. **Railway Dashboard**: See deployment status
3. **Email Notifications**: Get alerts on failures

## Troubleshooting

### If deployment fails:

1. **Check GitHub Actions logs**:
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Verify Railway token**:
   - Ensure token hasn't expired
   - Check it has deployment permissions

3. **Check Railway service names**:
   - `marine-seguros` for production
   - `marine-seguros-staging` for staging

### Common Issues:

- **"Service not found"**: Check service name in workflow matches Railway
- **"Invalid token"**: Regenerate and update Railway token
- **"Build failed"**: Check logs for Python errors

## Best Practices

1. **Test locally first**: `docker-compose -f docker-compose.dev.yml up`
2. **Use pull requests**: Merge feature → staging → main
3. **Monitor both environments**: Set up alerts
4. **Keep secrets secure**: Never commit tokens
5. **Regular token rotation**: Update tokens periodically