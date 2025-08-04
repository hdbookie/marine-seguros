# Setting Up Staging Environment in Railway

This guide walks you through setting up a complete staging environment with persistent storage.

## Step 1: Create New Railway Service for Staging

1. **Go to your Railway project dashboard**
2. **Click "New Service" button**
3. **Select "GitHub Repo"**
4. **Choose your repository: `hdbookie/marine-seguros`**
5. **Name the service: `marine-seguros-staging`**

## Step 2: Configure Environment Variables

In the staging service settings, add these environment variables:

```bash
RAILWAY_ENVIRONMENT=staging
DATA_PATH=/data
PORT=8501
GEMINI_API_KEY=<your-api-key>
```

## Step 3: Set Up Persistent Volume for Staging

1. **In the staging service, go to "Settings"**
2. **Scroll to "Volumes"**
3. **Click "Add Volume"**
4. **Configure:**
   - Mount path: `/data`
   - Name: `marine-data-staging`
   - Size: 1GB
5. **Click "Create Volume"**

## Step 4: Configure Deployment Settings

1. **In "Settings" → "Deploy"**
2. **Set:**
   - Branch: `staging` (or create a staging branch)
   - Auto Deploy: ON
   - Healthcheck Path: `/_stcore/health`
   - Healthcheck Timeout: 300

## Step 5: Set Up Production Volume (if not already done)

Repeat Step 3 for your production service:
1. **Go to your production service**
2. **Add Volume:**
   - Mount path: `/data`
   - Name: `marine-data-prod`
   - Size: 1GB (or more for production)

## Step 6: Create Staging Branch (Optional)

```bash
git checkout -b staging
git push origin staging
```

## Deployment Workflow

### For Staging:
```bash
# Work on feature branch
git checkout -b feature/my-feature

# Test locally
docker-compose -f docker-compose.dev.yml up

# Merge to staging
git checkout staging
git merge feature/my-feature
git push origin staging
# Auto-deploys to staging
```

### For Production:
```bash
# After testing in staging
git checkout main
git merge staging
git push origin main
# Auto-deploys to production
```

## Verify Setup

1. **Check Staging:**
   - Visit: `https://marine-seguros-staging.up.railway.app`
   - Upload test data
   - Verify data persists after redeployment

2. **Check Production:**
   - Visit: `https://marine-seguros.up.railway.app`
   - Ensure production data is isolated from staging

## Environment-Specific Features

The app now recognizes three environments:
- `development`: Local development with file system storage
- `staging`: Railway staging with persistent volume
- `production`: Railway production with persistent volume

## Data Management

- **Staging data** is isolated in `/data` on staging volume
- **Production data** is isolated in `/data` on production volume
- **No data sharing** between environments
- **Regular backups recommended** for production

## Monitoring

In Railway dashboard you can:
- View logs separately for each service
- Monitor resource usage
- Set up alerts
- View deployment history

## Rollback Strategy

If issues occur:
1. **In Railway dashboard → Deployments**
2. **Find last working deployment**
3. **Click "Rollback"**
4. **Volumes persist** - data is safe

## Best Practices

1. **Always test in staging first**
2. **Use environment-specific API keys**
3. **Monitor both environments**
4. **Set up alerts for failures**
5. **Regular backups of production volume**
6. **Document any environment-specific configs**