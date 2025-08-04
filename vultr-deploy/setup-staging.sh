#!/bin/bash
# Staging Environment Setup for Marine Seguros on Vultr
# Run this after the main setup script

set -e

echo "🚀 Setting up Staging Environment for Marine Seguros..."

# Create staging directories
echo "📁 Creating staging directories..."
mkdir -p /opt/marine-seguros/staging/{data,logs,app}
mkdir -p /opt/marine-seguros/staging/data/arquivos_enviados

# Create staging environment file
echo "🔐 Creating staging environment configuration..."
cat > /opt/marine-seguros/staging/.env << EOF
# Marine Seguros Staging Environment Configuration
GEMINI_API_KEY=your_gemini_api_key_here
RAILWAY_ENVIRONMENT=staging
DATA_PATH=/data
PORT=8501

# Staging-specific settings
LOG_LEVEL=debug
ENABLE_DEBUG_MODE=true
GIT_BRANCH=staging

# Database paths (separate from production)
AUTH_DB_PATH=/data/auth_staging.db
DASHBOARD_DB_PATH=/data/dashboard_staging.db

# Optional configurations
SESSION_TIMEOUT_MINUTES=60
MAX_FILE_SIZE_MB=50
EOF

# Copy production API key if exists
if [ -f /opt/marine-seguros/.env ]; then
    prod_key=$(grep GEMINI_API_KEY /opt/marine-seguros/.env | cut -d'=' -f2)
    if [ ! -z "$prod_key" ] && [ "$prod_key" != "your_gemini_api_key_here" ]; then
        sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$prod_key/" /opt/marine-seguros/staging/.env
        echo "✅ Copied API key from production environment"
    fi
fi

# Create nginx configuration for staging
echo "🌐 Setting up Nginx for staging environment..."
cat > /etc/nginx/sites-available/marine-seguros-staging << 'EOF'
server {
    listen 80;
    server_name staging.your-domain.com;  # Replace with your staging subdomain
    
    location / {
        proxy_pass http://localhost:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        
        # Add staging header
        proxy_set_header X-Environment "staging";
    }
    
    # Streamlit specific
    location /_stcore/stream {
        proxy_pass http://localhost:8502/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable staging site
ln -sf /etc/nginx/sites-available/marine-seguros-staging /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Create staging deployment script
cat > /opt/marine-seguros/deploy-staging.sh << 'EOF'
#!/bin/bash
# Deploy to staging environment

set -e

STAGING_DIR="/opt/marine-seguros/staging/app"
STAGING_BRANCH="staging"  # or "develop" based on your workflow

echo "🚧 Deploying to STAGING environment..."

cd $STAGING_DIR

# Check current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$STAGING_BRANCH" ]; then
    echo "Switching to $STAGING_BRANCH branch..."
    git checkout $STAGING_BRANCH
fi

# Pull latest changes
echo "📥 Pulling latest changes from $STAGING_BRANCH..."
git pull origin $STAGING_BRANCH

# Copy staging env file
cp /opt/marine-seguros/staging/.env .env

# Deploy with Docker
echo "🐳 Deploying staging with Docker..."
docker-compose -f vultr-deploy/docker-compose.staging.yml down
docker-compose -f vultr-deploy/docker-compose.staging.yml build
docker-compose -f vultr-deploy/docker-compose.staging.yml up -d

# Health check
echo "🏥 Checking staging health..."
sleep 10

if curl -f http://localhost:8502/_stcore/health > /dev/null 2>&1; then
    echo "✅ Staging deployment successful!"
    echo "🌐 Access staging at: http://staging.your-domain.com"
else
    echo "❌ Staging health check failed!"
    docker logs marine-seguros-staging
    exit 1
fi
EOF

chmod +x /opt/marine-seguros/deploy-staging.sh

# Create production deployment script
cat > /opt/marine-seguros/deploy-production.sh << 'EOF'
#!/bin/bash
# Deploy to production environment

set -e

PROD_DIR="/opt/marine-seguros/app"
PROD_BRANCH="main"  # or "master"

echo "🚀 Deploying to PRODUCTION environment..."
echo "⚠️  This will affect live users. Continue? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

cd $PROD_DIR

# Check current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$PROD_BRANCH" ]; then
    echo "Switching to $PROD_BRANCH branch..."
    git checkout $PROD_BRANCH
fi

# Pull latest changes
echo "📥 Pulling latest changes from $PROD_BRANCH..."
git pull origin $PROD_BRANCH

# Backup before deployment
echo "💾 Creating backup..."
/opt/marine-seguros/backup.sh

# Deploy with Docker
echo "🐳 Deploying production with Docker..."
docker-compose -f vultr-deploy/docker-compose.vultr.yml down
docker-compose -f vultr-deploy/docker-compose.vultr.yml build
docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d

# Health check
echo "🏥 Checking production health..."
sleep 10

if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Production deployment successful!"
else
    echo "❌ Production health check failed! Rolling back..."
    docker-compose -f vultr-deploy/docker-compose.vultr.yml down
    docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d
    exit 1
fi
EOF

chmod +x /opt/marine-seguros/deploy-production.sh

# Create environment comparison script
cat > /opt/marine-seguros/compare-envs.sh << 'EOF'
#!/bin/bash
# Compare staging and production environments

echo "📊 Environment Comparison"
echo "========================="
echo ""

echo "🐳 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "📁 Data Directories:"
echo "Production: $(du -sh /opt/marine-seguros/data 2>/dev/null | cut -f1)"
echo "Staging: $(du -sh /opt/marine-seguros/staging/data 2>/dev/null | cut -f1)"
echo ""

echo "🔀 Git Branches:"
echo -n "Production: "
cd /opt/marine-seguros/app && git rev-parse --abbrev-ref HEAD
echo -n "Staging: "
cd /opt/marine-seguros/staging/app && git rev-parse --abbrev-ref HEAD
echo ""

echo "📝 Recent Commits:"
echo "Production:"
cd /opt/marine-seguros/app && git log --oneline -5
echo ""
echo "Staging:"
cd /opt/marine-seguros/staging/app && git log --oneline -5
EOF

chmod +x /opt/marine-seguros/compare-envs.sh

echo "✅ Staging environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository to staging:"
echo "   cd /opt/marine-seguros/staging/app"
echo "   git clone -b staging https://github.com/YOUR_USERNAME/marine-seguros.git ."
echo ""
echo "2. Configure staging subdomain DNS:"
echo "   Point staging.your-domain.com to this server"
echo ""
echo "3. Deploy to staging:"
echo "   /opt/marine-seguros/deploy-staging.sh"
echo ""
echo "4. Access staging at:"
echo "   http://staging.your-domain.com (port 8502)"