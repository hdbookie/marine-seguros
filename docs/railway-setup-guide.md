# Railway Setup Guide for Marine Seguros

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository connected
- Railway CLI (optional): `npm install -g @railway/cli`

## Initial Setup

### 1. Create Railway Project
1. Login to Railway Dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `marine-seguros` repository
5. Name the project: `marine-seguros`

### 2. Create Environments
Railway will create a production environment by default. Add staging:
1. In your project, click "Settings" → "Environments"
2. Click "New Environment"
3. Name it "staging"

### 3. Configure Branch Connections
**Production Environment:**
- Go to Settings → General
- Set "Branch" to `main`
- Enable "Auto Deploy"

**Staging Environment:**
- Switch to staging environment (dropdown at top)
- Go to Settings → General
- Set "Branch" to `staging`
- Enable "Auto Deploy"

## Volume Configuration

### For BOTH Production and Staging Environments:

**Volume 1: Database Storage**
1. Go to your service → Variables → Volumes
2. Click "New Volume"
3. Name: `data-volume`
4. Mount path: `/data`
5. Size: 1GB

**Volume 2: File Uploads**
1. Click "New Volume" again
2. Name: `uploads-volume`
3. Mount path: `/data/arquivos_enviados`
4. Size: 5GB

## Environment Variables

Set these in BOTH environments (Variables tab):

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DATA_PATH=/data

# Railway provides automatically
PORT=<provided by Railway>

# Optional
LOG_LEVEL=info
ENABLE_DEBUG_MODE=false
```

### Generating JWT Secret Key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## GitHub Secrets Setup

In your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add these secrets:
   - `RAILWAY_TOKEN_PRODUCTION`: Your production Railway API token
   - `RAILWAY_TOKEN_STAGING`: Your staging Railway API token

### Getting Railway Tokens:
1. In Railway, go to Account Settings → Tokens
2. Create token named "GitHub Actions Production"
3. Create token named "GitHub Actions Staging"
4. Copy each token to GitHub secrets

## Deployment Workflow

### Automatic Deployments:
- Push to `main` → Deploys to production
- Push to `staging` → Deploys to staging

### Manual Deployment:
```bash
# Using Railway CLI
railway login
railway link [project-id]

# Deploy to staging
railway up -e staging

# Deploy to production
railway up -e production
```

## Monitoring & Logs

### View Logs:
1. In Railway dashboard, click on your service
2. Go to "Logs" tab

### Health Checks:
- Production: `https://your-prod-domain.railway.app/_stcore/health`
- Staging: `https://your-staging-domain.railway.app/_stcore/health`

## Domain Configuration

### Default Domains:
Railway provides default domains:
- Production: `marine-seguros-production.up.railway.app`
- Staging: `marine-seguros-staging.up.railway.app`

### Custom Domain (Optional):
1. Go to service → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

## Troubleshooting

### Database Not Persisting:
- Verify volume is mounted at `/data`
- Check `DATA_PATH` environment variable is set

### File Uploads Not Working:
- Verify uploads volume is mounted at `/data/arquivos_enviados`
- Check directory permissions in Dockerfile

### Deployment Failures:
- Check build logs in Railway dashboard
- Verify all environment variables are set
- Ensure GitHub Actions secrets are correct

## Backup Strategy

Railway volumes are persistent but consider:
1. Regular database exports
2. Scheduled volume snapshots (Railway feature)
3. Store critical backups externally

## Cost Estimation

- Hobby plan: $5/month (includes $5 usage)
- Additional usage: ~$5-10/month for your app
- Total: ~$5-10/month for both environments

## Support

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- GitHub Issues: For app-specific problems