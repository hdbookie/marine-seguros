# Staging Environment Guide for Vultr

## Overview

Your Vultr setup now includes both **staging** and **production** environments on the same server:

- **Production**: `your-domain.com` (port 8501)
- **Staging**: `staging.your-domain.com` (port 8502)

## Key Differences

| Feature | Production | Staging |
|---------|------------|---------|
| URL | your-domain.com | staging.your-domain.com |
| Port | 8501 | 8502 |
| Git Branch | main | staging |
| Debug Mode | Disabled | Enabled |
| Log Level | info | debug |
| Data Directory | /opt/marine-seguros/data | /opt/marine-seguros/staging/data |
| Container Name | marine-seguros | marine-seguros-staging |
| Hot Reload | No | Yes (code mounted) |

## Setup Instructions

1. **Initial Setup** (after main setup):
   ```bash
   ./setup-staging.sh
   ```

2. **Clone Staging Repository**:
   ```bash
   cd /opt/marine-seguros/staging/app
   git clone -b staging https://github.com/YOUR_USERNAME/marine-seguros.git .
   ```

3. **Configure DNS**:
   - Add A record for `staging.your-domain.com` pointing to your server IP

4. **Deploy Staging**:
   ```bash
   /opt/marine-seguros/deploy-staging.sh
   ```

## Workflow

### 1. Development Cycle

```bash
# Local development
git checkout staging
git pull origin staging
# Make changes
git add .
git commit -m "Feature: description"
git push origin staging

# Auto-deploy to staging (or manual)
ssh root@your-server
/opt/marine-seguros/deploy-staging.sh
```

### 2. Live Editing (Hot Reload)

Since staging mounts the code directory, you can edit directly on the server:

```bash
# SSH to server
cd /opt/marine-seguros/staging/app
nano app_refactored.py
# Changes appear immediately!
```

### 3. Testing in Staging

- Access: http://staging.your-domain.com
- Debug mode shows detailed errors
- Monitor logs: `docker logs -f marine-seguros-staging`

### 4. Promote to Production

After testing in staging:

```bash
# Option 1: Manual
git checkout main
git merge staging
git push origin main
/opt/marine-seguros/deploy-production.sh

# Option 2: Using sync script
/opt/marine-seguros/sync-environments.sh promote
```

## Data Management

### Copy Production Data to Staging
```bash
/opt/marine-seguros/sync-environments.sh prod-to-staging
```

### Copy Specific Files
```bash
/opt/marine-seguros/sync-environments.sh copy-file "Resultado Financeiro - 2025.xlsx"
```

### Compare Environments
```bash
/opt/marine-seguros/compare-envs.sh
```

## Monitoring

### View Both Environments
```bash
docker ps
```

### Staging Logs
```bash
docker logs -f marine-seguros-staging
```

### Production Logs
```bash
docker logs -f marine-seguros
```

## Security

### Optional: Password Protect Staging
```bash
# Create password file
htpasswd -c /etc/nginx/.htpasswd-staging staginguser

# Uncomment auth lines in nginx config
nano /etc/nginx/sites-available/marine-seguros-staging
# Uncomment:
# auth_basic "Staging Environment";
# auth_basic_user_file /etc/nginx/.htpasswd-staging;

nginx -t && systemctl reload nginx
```

## Quick Commands Cheat Sheet

```bash
# Deploy to staging
/opt/marine-seguros/deploy-staging.sh

# Deploy to production
/opt/marine-seguros/deploy-production.sh

# Sync data prod → staging
/opt/marine-seguros/sync-environments.sh prod-to-staging

# Compare environments
/opt/marine-seguros/compare-envs.sh

# View staging logs
docker logs -f marine-seguros-staging

# Restart staging
docker restart marine-seguros-staging

# SSH to staging container
docker exec -it marine-seguros-staging bash
```

## Troubleshooting

1. **Port conflicts**: Ensure nothing else uses ports 8501 or 8502
2. **Staging not updating**: Check if code is properly mounted in docker-compose.staging.yml
3. **Data not syncing**: Verify directory permissions and paths
4. **SSL issues**: Run certbot separately for staging subdomain