#!/bin/bash

# Overseer Development Environment Logs Script
# This script shows logs from the development environment

set -e

echo "📋 Showing Overseer Development Environment Logs..."
echo "Press Ctrl+C to exit"
echo ""

# Show logs from all services, following them
docker-compose -f docker-compose.dev.yml logs -f
