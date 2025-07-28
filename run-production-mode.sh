#!/bin/bash

echo "🚀 Running in production-like mode locally..."
echo "📁 Files will be stored in database (not filesystem)"
echo "⚡ This simulates Railway's ephemeral filesystem"
echo ""

# Clear ephemeral data (like Railway does on each deploy)
echo "🗑️  Clearing ephemeral data..."
rm -rf data/arquivos_enviados/*

# Set production-like environment variables
export RAILWAY_ENVIRONMENT=production
export PORT=8501

# Run with production start script
bash start.sh