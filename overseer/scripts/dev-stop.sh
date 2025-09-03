#!/bin/bash

# Overseer Development Environment Stop Script
# This script stops the development environment

set -e

echo "🛑 Stopping Overseer Development Environment..."

# Stop and remove containers
docker-compose -f docker-compose.dev.yml down

echo "✅ Development environment stopped."
echo ""
echo "💡 To start again, run: ./scripts/dev-start.sh"
