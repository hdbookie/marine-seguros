#!/bin/bash

echo "🚀 Starting production-like environment..."
echo "This simulates Railway's ephemeral filesystem"
echo ""

# Clean up any existing containers
docker compose down

# Remove local data to simulate fresh deployment
echo "🗑️  Removing local data directory to simulate fresh deployment..."
rm -rf data/arquivos_enviados/*
rm -rf data/*.db

# Build and start the container
echo "🔨 Building Docker image..."
docker compose build

echo "🏃 Starting container..."
docker compose up

# To test with persistent volumes (more like local dev), run:
# docker compose -f docker-compose.yml up