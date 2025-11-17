#!/bin/bash

# Simple startup script for OriginHub Backend
# This script handles everything: building, starting services, and running migrations

set -e

echo "🚀 Starting OriginHub Backend Services..."
echo ""

# Navigate to docker directory
cd "$(dirname "$0")/docker" || exit 1

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
echo "📦 Building and starting Docker containers..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Services are starting!"
echo ""
echo "📝 To view logs, run:"
echo "   cd docker && docker compose logs -f"
echo ""
echo "🌐 API will be available at:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo ""
echo "💡 The entrypoint script will automatically:"
echo "   1. Wait for PostgreSQL to be ready"
echo "   2. Run database migrations"
echo "   3. Start the FastAPI server"
echo ""
echo "⏱️  Give it a few seconds for migrations to complete..."

