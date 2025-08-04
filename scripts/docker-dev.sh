#!/bin/bash

echo "🔧 Starting Docker in DEVELOPMENT mode..."
echo "✅ Live code editing enabled"
echo "✅ Files stored on local filesystem"
echo "✅ Data persists between restarts"
echo ""

# Use the development compose file
docker compose -f docker-compose.dev.yml up