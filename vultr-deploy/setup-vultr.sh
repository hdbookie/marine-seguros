#!/bin/bash
# Vultr VPS Setup Script for Marine Seguros
# Run this on a fresh Ubuntu 22.04 or 24.04 Vultr instance

set -e

echo "🚀 Starting Marine Seguros Vultr Setup..."

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    ufw \
    fail2ban

# Enable Docker
systemctl enable docker
systemctl start docker

# Create application directory
echo "📁 Creating application directories..."
mkdir -p /opt/marine-seguros/{data,logs,app}
mkdir -p /opt/marine-seguros/data/arquivos_enviados

# Set up firewall
echo "🔒 Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8501/tcp  # Streamlit (temporary, remove after nginx setup)
ufw --force enable

# Create environment file
echo "🔐 Creating environment configuration..."
cat > /opt/marine-seguros/.env << EOF
# Marine Seguros Environment Configuration
GEMINI_API_KEY=your_gemini_api_key_here
RAILWAY_ENVIRONMENT=production
DATA_PATH=/data
PORT=8501

# Optional configurations
LOG_LEVEL=info
ENABLE_DEBUG_MODE=false
EOF

echo "⚠️  IMPORTANT: Edit /opt/marine-seguros/.env to add your GEMINI_API_KEY"

# Create systemd service for non-Docker deployment
cat > /etc/systemd/system/marine-seguros.service << EOF
[Unit]
Description=Marine Seguros Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/marine-seguros/app
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/marine-seguros/.env
ExecStart=/usr/local/bin/streamlit run app_refactored.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
echo "🌐 Setting up Nginx reverse proxy..."
cat > /etc/nginx/sites-available/marine-seguros << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Streamlit specific
    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/marine-seguros /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Create backup script
echo "💾 Creating backup script..."
cat > /opt/marine-seguros/backup.sh << 'EOF'
#!/bin/bash
# Backup script for Marine Seguros data

BACKUP_DIR="/opt/marine-seguros/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="marine_backup_${TIMESTAMP}"

mkdir -p ${BACKUP_DIR}

# Backup data directory
tar -czf ${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz -C /opt/marine-seguros data/

# Backup databases
cp /opt/marine-seguros/data/*.db ${BACKUP_DIR}/ 2>/dev/null || true

# Keep only last 7 days of backups
find ${BACKUP_DIR} -name "marine_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_NAME}"
EOF

chmod +x /opt/marine-seguros/backup.sh

# Add cron job for daily backups
echo "0 2 * * * /opt/marine-seguros/backup.sh >> /opt/marine-seguros/logs/backup.log 2>&1" | crontab -

# Create deployment instructions
cat > /opt/marine-seguros/DEPLOY.md << 'EOF'
# Marine Seguros Deployment Instructions

## Initial Setup

1. Clone your repository:
   ```bash
   cd /opt/marine-seguros/app
   git clone https://github.com/YOUR_USERNAME/marine-seguros.git .
   ```

2. Set up environment variables:
   ```bash
   nano /opt/marine-seguros/.env
   # Add your GEMINI_API_KEY
   ```

3. Deploy with Docker:
   ```bash
   cd /opt/marine-seguros/app
   docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d
   ```

   OR deploy without Docker:
   ```bash
   cd /opt/marine-seguros/app
   pip3 install -r requirements.txt
   systemctl start marine-seguros
   systemctl enable marine-seguros
   ```

## SSL Certificate Setup (after pointing domain)

1. Install SSL certificate:
   ```bash
   certbot --nginx -d your-domain.com
   ```

## Monitoring

- Check logs: `docker logs marine-seguros` or `journalctl -u marine-seguros`
- Check status: `docker ps` or `systemctl status marine-seguros`

## Updates

1. Pull latest code:
   ```bash
   cd /opt/marine-seguros/app
   git pull
   ```

2. Restart:
   ```bash
   docker-compose -f vultr-deploy/docker-compose.vultr.yml restart
   # OR
   systemctl restart marine-seguros
   ```
EOF

echo "✅ Vultr setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/marine-seguros/.env to add your GEMINI_API_KEY"
echo "2. Clone your repository to /opt/marine-seguros/app"
echo "3. Choose Docker or systemd deployment (see /opt/marine-seguros/DEPLOY.md)"
echo "4. Point your domain to this server's IP"
echo "5. Run certbot for SSL: certbot --nginx -d your-domain.com"