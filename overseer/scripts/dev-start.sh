#!/bin/bash

# Overseer Development Environment Startup Script
# This script starts the complete development environment with Docker Compose

set -e

echo "🚀 Starting Overseer Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ .env file created. Please review and update as needed."
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.dev.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U overseer -d overseer_dev > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.dev.yml exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Check API health
echo "🔍 Checking API health..."
sleep 5
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is ready"
else
    echo "❌ API is not ready"
fi

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📋 Available services:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: ./scripts/dev-logs.sh"
echo "   • Stop services: ./scripts/dev-stop.sh"
echo "   • Run tests: ./scripts/dev-test.sh"
echo "   • Access API container: docker-compose -f docker-compose.dev.yml exec api bash"
echo ""
