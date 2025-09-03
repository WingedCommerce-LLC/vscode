#!/bin/bash

# Overseer Development Environment Test Script
# This script runs tests in the development environment

set -e

echo "🧪 Running Overseer Tests..."

# Check if development environment is running
if ! docker-compose -f docker-compose.dev.yml ps | grep -q "overseer-api-dev"; then
    echo "❌ Development environment is not running."
    echo "💡 Start it first with: ./scripts/dev-start.sh"
    exit 1
fi

# Run tests with coverage
echo "🔍 Running tests with coverage..."
docker-compose -f docker-compose.dev.yml exec api python -m pytest --cov=. --cov-report=term-missing -v

echo ""
echo "✅ Tests completed!"
