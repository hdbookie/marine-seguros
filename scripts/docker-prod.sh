#!/bin/bash

echo "🚀 Starting Docker in PRODUCTION mode..."
echo "✅ Persistent volumes enabled (like Railway)"
echo "📁 Data stored in Docker volumes"
echo "🔒 Production environment settings"
echo ""

# Use the production compose file with volumes
# --build flag ensures we rebuild the image with latest code changes
docker compose -f docker-compose.prod.yml up --build