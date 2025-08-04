#!/bin/bash

echo "🔨 Rebuilding Docker image with latest code..."
echo ""

# Stop any running containers
docker compose down

# Rebuild the image
docker compose build --no-cache

echo ""
echo "✅ Docker image rebuilt successfully!"
echo ""
echo "Now you can run:"
echo "  ./docker-prod.sh    # For production mode"
echo "  ./docker-dev.sh     # For development mode"