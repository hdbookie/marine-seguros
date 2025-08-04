#!/bin/bash
# Monitoring setup for Marine Seguros on Vultr

set -e

echo "📊 Setting up monitoring for Marine Seguros..."

# Install monitoring tools
apt-get install -y htop iotop nethogs

# Create monitoring script
cat > /opt/marine-seguros/monitor.sh << 'EOF'
#!/bin/bash
# Marine Seguros Monitoring Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo "=== Marine Seguros Monitoring Dashboard ==="
echo "Time: $(date)"
echo ""

# Check if service is running
check_service() {
    if docker ps | grep -q marine-seguros; then
        echo -e "Service Status: ${GREEN}Running (Docker)${NC}"
        docker stats marine-seguros --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    elif systemctl is-active --quiet marine-seguros; then
        echo -e "Service Status: ${GREEN}Running (systemd)${NC}"
        systemctl status marine-seguros --no-pager | head -n 3
    else
        echo -e "Service Status: ${RED}Not Running${NC}"
    fi
}

# Check disk usage
check_disk() {
    echo -e "\n📁 Disk Usage:"
    df -h | grep -E "^/dev|Filesystem"
    echo ""
    echo "Data directory size:"
    du -sh /opt/marine-seguros/data 2>/dev/null || echo "No data directory"
}

# Check memory
check_memory() {
    echo -e "\n💾 Memory Usage:"
    free -h
}

# Check recent logs
check_logs() {
    echo -e "\n📜 Recent Logs:"
    if docker ps | grep -q marine-seguros; then
        docker logs marine-seguros --tail 10 2>&1
    else
        journalctl -u marine-seguros -n 10 --no-pager 2>&1 || echo "No systemd logs found"
    fi
}

# Network connections
check_network() {
    echo -e "\n🌐 Network Connections:"
    netstat -tlnp | grep -E ":8501|:80|:443" 2>/dev/null || ss -tlnp | grep -E ":8501|:80|:443"
}

# Main monitoring loop
while true; do
    clear
    echo "=== Marine Seguros Monitoring Dashboard ==="
    echo "Time: $(date)"
    echo "Press Ctrl+C to exit"
    echo ""
    
    check_service
    check_disk
    check_memory
    check_network
    
    sleep 5
done
EOF

chmod +x /opt/marine-seguros/monitor.sh

# Create log rotation config
cat > /etc/logrotate.d/marine-seguros << 'EOF'
/opt/marine-seguros/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    postrotate
        if docker ps | grep -q marine-seguros; then
            docker restart marine-seguros > /dev/null 2>&1 || true
        fi
    endscript
}
EOF

# Create health check endpoint script
cat > /opt/marine-seguros/healthcheck.sh << 'EOF'
#!/bin/bash
# Health check script for monitoring services

HEALTH_URL="http://localhost:8501/_stcore/health"
SLACK_WEBHOOK_URL=""  # Add your Slack webhook URL if desired
EMAIL_TO=""  # Add email for notifications

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
    
    if [ "$response" != "200" ]; then
        message="⚠️ Marine Seguros health check failed! Response code: $response"
        echo "$(date): $message" >> /opt/marine-seguros/logs/health.log
        
        # Send Slack notification if configured
        if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"$message\"}" \
                $SLACK_WEBHOOK_URL
        fi
        
        # Send email if configured
        if [ ! -z "$EMAIL_TO" ]; then
            echo "$message" | mail -s "Marine Seguros Health Check Failed" $EMAIL_TO
        fi
        
        # Attempt to restart service
        if docker ps | grep -q marine-seguros; then
            docker restart marine-seguros
        else
            systemctl restart marine-seguros
        fi
    else
        echo "$(date): Health check passed" >> /opt/marine-seguros/logs/health.log
    fi
}

check_health
EOF

chmod +x /opt/marine-seguros/healthcheck.sh

# Add health check to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/marine-seguros/healthcheck.sh") | crontab -

echo "✅ Monitoring setup complete!"
echo ""
echo "Available monitoring commands:"
echo "- Real-time monitoring: /opt/marine-seguros/monitor.sh"
echo "- View logs: docker logs marine-seguros -f"
echo "- System stats: htop"
echo "- Disk I/O: iotop"
echo "- Network usage: nethogs"