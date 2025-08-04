#!/bin/bash

echo "🚀 Starting Docker in PRODUCTION mode..."
echo "⚡ Simulating Railway's ephemeral filesystem"
echo "📁 Files stored in database (not filesystem)"
echo "❌ No live code editing"
echo ""

# Clean up to simulate fresh deployment
echo "🗑️  Clearing ephemeral data..."
rm -rf data/arquivos_enviados/*

# Use the production compose file
docker compose up