#!/bin/bash

# Overseer Development Environment Reset Script
# This script resets the development environment (removes volumes and rebuilds)

set -e

echo "🔄 Resetting Overseer Development Environment..."
echo "⚠️  This will remove all data in the development database!"
echo ""

# Ask for confirmation
read -p "Are you sure you want to reset the development environment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Reset cancelled."
    exit 1
fi

# Stop containers
echo "🛑 Stopping containers..."
docker-compose -f docker-compose.dev.yml down

# Remove volumes
echo "🗑️  Removing volumes..."
docker-compose -f docker-compose.dev.yml down -v

# Remove images
echo "🗑️  Removing images..."
docker-compose -f docker-compose.dev.yml down --rmi local

# Clean up any dangling images
echo "🧹 Cleaning up..."
docker system prune -f

echo ""
echo "✅ Development environment reset complete!"
echo "💡 Start fresh with: ./scripts/dev-start.sh"
