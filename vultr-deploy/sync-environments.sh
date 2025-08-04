#!/bin/bash
# Environment synchronization scripts for Marine Seguros

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to sync data from production to staging
sync_prod_to_staging() {
    echo -e "${YELLOW}⚠️  WARNING: This will overwrite staging data with production data!${NC}"
    echo "Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Sync cancelled."
        return
    fi
    
    echo -e "${GREEN}📦 Creating backup of staging data...${NC}"
    tar -czf /opt/marine-seguros/staging/backup_before_sync_$(date +%Y%m%d_%H%M%S).tar.gz \
        -C /opt/marine-seguros/staging data/
    
    echo -e "${GREEN}🔄 Syncing production data to staging...${NC}"
    
    # Stop staging container
    docker-compose -f /opt/marine-seguros/staging/app/vultr-deploy/docker-compose.staging.yml down
    
    # Copy data
    rsync -av --delete \
        /opt/marine-seguros/data/ \
        /opt/marine-seguros/staging/data/
    
    # Update database names to avoid conflicts
    cd /opt/marine-seguros/staging/data
    if [ -f auth.db ]; then
        cp auth.db auth_staging.db
    fi
    if [ -f dashboard.db ]; then
        cp dashboard.db dashboard_staging.db
    fi
    
    # Restart staging
    cd /opt/marine-seguros/staging/app
    docker-compose -f vultr-deploy/docker-compose.staging.yml up -d
    
    echo -e "${GREEN}✅ Sync complete!${NC}"
}

# Function to promote staging to production
promote_staging_to_prod() {
    echo -e "${RED}🚨 WARNING: This will deploy staging code to production!${NC}"
    echo "Have you thoroughly tested staging? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Promotion cancelled."
        return
    fi
    
    echo -e "${GREEN}📦 Creating production backup...${NC}"
    /opt/marine-seguros/backup.sh
    
    echo -e "${GREEN}🔀 Merging staging branch to main...${NC}"
    cd /opt/marine-seguros/app
    
    # Ensure we're on main branch
    git checkout main
    git pull origin main
    
    # Merge staging
    git merge origin/staging -m "Promote staging to production"
    git push origin main
    
    echo -e "${GREEN}🚀 Deploying to production...${NC}"
    /opt/marine-seguros/deploy-production.sh
}

# Function to copy specific files between environments
copy_file_to_staging() {
    local file=$1
    if [ -z "$file" ]; then
        echo "Usage: copy_file_to_staging <filename>"
        return
    fi
    
    src="/opt/marine-seguros/data/arquivos_enviados/$file"
    dst="/opt/marine-seguros/staging/data/arquivos_enviados/$file"
    
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo -e "${GREEN}✅ Copied $file to staging${NC}"
    else
        echo -e "${RED}❌ File not found: $file${NC}"
    fi
}

# Function to sync environment variables
sync_env_vars() {
    echo "Syncing environment variables from production to staging..."
    
    # Read production env
    prod_api_key=$(grep GEMINI_API_KEY /opt/marine-seguros/.env | cut -d'=' -f2)
    
    # Update staging env
    sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$prod_api_key/" /opt/marine-seguros/staging/.env
    
    echo -e "${GREEN}✅ Environment variables synced${NC}"
}

# Function to show data differences
show_data_diff() {
    echo -e "${YELLOW}📊 Data Comparison${NC}"
    echo "=================="
    
    echo -e "\n${GREEN}Production:${NC}"
    echo "Files: $(find /opt/marine-seguros/data/arquivos_enviados -type f | wc -l)"
    echo "Size: $(du -sh /opt/marine-seguros/data | cut -f1)"
    echo "Auth DB: $(du -sh /opt/marine-seguros/data/auth.db 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "Dashboard DB: $(du -sh /opt/marine-seguros/data/dashboard.db 2>/dev/null | cut -f1 || echo 'N/A')"
    
    echo -e "\n${YELLOW}Staging:${NC}"
    echo "Files: $(find /opt/marine-seguros/staging/data/arquivos_enviados -type f | wc -l)"
    echo "Size: $(du -sh /opt/marine-seguros/staging/data | cut -f1)"
    echo "Auth DB: $(du -sh /opt/marine-seguros/staging/data/auth_staging.db 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "Dashboard DB: $(du -sh /opt/marine-seguros/staging/data/dashboard_staging.db 2>/dev/null | cut -f1 || echo 'N/A')"
}

# Main menu
case "$1" in
    "prod-to-staging")
        sync_prod_to_staging
        ;;
    "promote")
        promote_staging_to_prod
        ;;
    "copy-file")
        copy_file_to_staging "$2"
        ;;
    "sync-env")
        sync_env_vars
        ;;
    "diff")
        show_data_diff
        ;;
    *)
        echo "Marine Seguros Environment Sync Tool"
        echo "===================================="
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  prod-to-staging  - Copy production data to staging"
        echo "  promote         - Promote staging code to production"
        echo "  copy-file <file> - Copy specific file to staging"
        echo "  sync-env        - Sync environment variables"
        echo "  diff            - Show data differences"
        echo ""
        echo "Examples:"
        echo "  $0 prod-to-staging"
        echo "  $0 copy-file 'Resultado Financeiro - 2025.xlsx'"
        echo "  $0 promote"
        ;;
esac