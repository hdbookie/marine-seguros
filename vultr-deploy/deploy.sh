#!/bin/bash
# Deployment script to run on Vultr server
# This script deploys/updates the Marine Seguros application

set -e

DEPLOY_DIR="/opt/marine-seguros/app"
REPO_URL="https://github.com/YOUR_USERNAME/marine-seguros.git"  # Update this
BRANCH="main"  # Update if using different branch

echo "🚀 Starting Marine Seguros deployment..."

# Function to check if using Docker or systemd
check_deployment_type() {
    if docker ps | grep -q marine-seguros; then
        echo "docker"
    elif systemctl is-active --quiet marine-seguros; then
        echo "systemd"
    else
        echo "none"
    fi
}

DEPLOY_TYPE=$(check_deployment_type)

# Pull latest code
echo "📥 Pulling latest code..."
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "Cloning repository..."
    git clone $REPO_URL $DEPLOY_DIR
    cd $DEPLOY_DIR
else
    echo "Updating repository..."
    cd $DEPLOY_DIR
    git fetch origin
    git reset --hard origin/$BRANCH
fi

# Copy environment file if it doesn't exist in app directory
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp /opt/marine-seguros/.env $DEPLOY_DIR/.env
fi

# Deploy based on deployment type
if [ "$DEPLOY_TYPE" == "docker" ]; then
    echo "🐳 Deploying with Docker..."
    
    # Build new image
    docker-compose -f vultr-deploy/docker-compose.vultr.yml build
    
    # Stop old container
    docker-compose -f vultr-deploy/docker-compose.vultr.yml down
    
    # Start new container
    docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d
    
    # Clean up old images
    docker image prune -f
    
elif [ "$DEPLOY_TYPE" == "systemd" ]; then
    echo "⚙️ Deploying with systemd..."
    
    # Install/update Python dependencies
    pip3 install -r requirements.txt
    
    # Restart service
    systemctl restart marine-seguros
    
else
    echo "❓ No deployment type detected. Please run initial setup first."
    exit 1
fi

# Run migrations if needed (placeholder for future database migrations)
# echo "🔄 Running migrations..."
# python3 migrate.py

# Health check
echo "🏥 Performing health check..."
sleep 10  # Give app time to start

if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! Application is healthy."
else
    echo "❌ Health check failed. Check logs:"
    if [ "$DEPLOY_TYPE" == "docker" ]; then
        echo "Run: docker logs marine-seguros"
    else
        echo "Run: journalctl -u marine-seguros -n 50"
    fi
    exit 1
fi

echo "🎉 Deployment complete!"