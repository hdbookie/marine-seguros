# Marine Seguros - Vultr Deployment Guide

This guide helps you deploy Marine Seguros on a Vultr VPS instance.

## Prerequisites

- Vultr account with a VPS instance (Ubuntu 22.04 or 24.04 recommended)
- Domain name (optional but recommended for SSL)
- GitHub repository with your Marine Seguros code
- Gemini API key

## Quick Start

1. **Create a Vultr VPS**
   - Choose Ubuntu 22.04 or 24.04
   - Minimum specs: 2 vCPU, 4GB RAM, 80GB SSD
   - Enable IPv6 and Auto Backups (recommended)

2. **SSH into your server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Download and run setup script**
   ```bash
   wget https://raw.githubusercontent.com/YOUR_USERNAME/marine-seguros/main/vultr-deploy/setup-vultr.sh
   chmod +x setup-vultr.sh
   ./setup-vultr.sh
   ```

4. **Configure environment**
   ```bash
   nano /opt/marine-seguros/.env
   # Add your GEMINI_API_KEY
   ```

5. **Deploy the application**
   ```bash
   cd /opt/marine-seguros/app
   git clone https://github.com/YOUR_USERNAME/marine-seguros.git .
   
   # Option A: Deploy with Docker (recommended)
   docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d
   
   # Option B: Deploy with systemd
   pip3 install -r requirements.txt
   systemctl start marine-seguros
   systemctl enable marine-seguros
   ```

## Deployment Options

### Option A: Docker Deployment (Recommended)

Advantages:
- Isolated environment
- Easy updates and rollbacks
- Consistent across environments

```bash
# Deploy
docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d

# View logs
docker logs -f marine-seguros

# Update
docker-compose -f vultr-deploy/docker-compose.vultr.yml pull
docker-compose -f vultr-deploy/docker-compose.vultr.yml up -d
```

### Option B: Systemd Deployment

Advantages:
- Lower resource usage
- Direct system integration
- Simpler debugging

```bash
# Start service
systemctl start marine-seguros

# View logs
journalctl -u marine-seguros -f

# Update
git pull
pip3 install -r requirements.txt
systemctl restart marine-seguros
```

## SSL Certificate Setup

After pointing your domain to the server:

```bash
certbot --nginx -d your-domain.com
```

## File Structure

```
/opt/marine-seguros/
├── app/              # Application code
├── data/             # Persistent data storage
│   ├── arquivos_enviados/
│   ├── auth.db
│   └── dashboard.db
├── logs/             # Application logs
├── backups/          # Automated backups
├── .env              # Environment configuration
├── backup.sh         # Backup script
├── monitor.sh        # Monitoring script
└── healthcheck.sh    # Health check script
```

## Monitoring

1. **Real-time monitoring**
   ```bash
   /opt/marine-seguros/monitor.sh
   ```

2. **Check application health**
   ```bash
   curl http://localhost:8501/_stcore/health
   ```

3. **View logs**
   ```bash
   # Docker
   docker logs -f marine-seguros
   
   # Systemd
   journalctl -u marine-seguros -f
   ```

## Backup Strategy

Automatic daily backups are configured:
- Runs at 2 AM daily
- Keeps last 7 days of backups
- Backs up data directory and databases

Manual backup:
```bash
/opt/marine-seguros/backup.sh
```

## Updates and Maintenance

1. **Update application**
   ```bash
   cd /opt/marine-seguros/app
   ./vultr-deploy/deploy.sh
   ```

2. **System updates**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Docker cleanup** (if using Docker)
   ```bash
   docker system prune -a
   ```

## Troubleshooting

1. **Application won't start**
   - Check logs: `docker logs marine-seguros` or `journalctl -u marine-seguros`
   - Verify .env file has correct API key
   - Check port 8501 is not in use: `netstat -tlnp | grep 8501`

2. **Can't access from browser**
   - Check firewall: `ufw status`
   - Verify nginx is running: `systemctl status nginx`
   - Check nginx config: `nginx -t`

3. **High resource usage**
   - Monitor with: `htop` or `/opt/marine-seguros/monitor.sh`
   - Check disk space: `df -h`
   - Review logs for errors

## Security Recommendations

1. **Use a non-root user**
   ```bash
   adduser marine
   usermod -aG sudo marine
   ```

2. **Set up SSH key authentication**
   ```bash
   ssh-copy-id marine@your-server-ip
   ```

3. **Disable password authentication**
   ```bash
   nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   systemctl restart sshd
   ```

4. **Regular updates**
   - Enable unattended-upgrades for security patches
   - Regularly update application dependencies

## Cost Optimization

- Use Vultr's snapshot feature before major updates
- Consider Vultr's Object Storage for backups
- Monitor bandwidth usage to avoid overages
- Use Vultr's DDoS protection if available

## Support

For issues specific to:
- Vultr infrastructure: Contact Vultr support
- Application bugs: Check the GitHub repository
- Deployment issues: Review logs and this guide