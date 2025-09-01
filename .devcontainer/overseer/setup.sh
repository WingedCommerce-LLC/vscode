#!/bin/bash

# Manual Overseer Setup Script
# Run this after the devcontainer starts successfully

echo "🚀 Setting up Overseer AI Development Environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install essential system tools
echo "📦 Installing essential system tools..."
sudo apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    vim \
    tree \
    jq

# Upgrade pip
echo "🐍 Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install core Python packages
echo "📦 Installing core Python packages..."
pip install --quiet \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0

# Install TypeScript
echo "📦 Installing TypeScript..."
npm install -g typescript@5.3.0

# Install Python dependencies from requirements.txt
echo "📦 Installing Overseer Python dependencies..."
if [ -f "overseer/requirements.txt" ]; then
    pip install -r overseer/requirements.txt
else
    echo "⚠️  overseer/requirements.txt not found, skipping..."
fi

# Install Node.js dependencies
echo "📦 Installing Overseer Node.js dependencies..."
if [ -f "overseer/package.json" ]; then
    cd overseer && npm install && cd ..
else
    echo "⚠️  overseer/package.json not found, skipping..."
fi

# Set up Git configuration
echo "🔧 Configuring Git..."
git config --global init.defaultBranch main
git config --global pull.rebase false

# Create .env file from template
echo "📝 Setting up environment file..."
if [ -f "overseer/.env.template" ] && [ ! -f "overseer/.env" ]; then
    cp overseer/.env.template overseer/.env
    echo "✅ Created overseer/.env from template"
else
    echo "ℹ️  Environment file already exists or template not found"
fi

# Health check
echo ""
echo "🏥 Environment Health Check:"
echo "Python: $(python --version 2>&1 || echo 'Not available')"
echo "Node: $(node --version 2>&1 || echo 'Not available')"
echo "NPM: $(npm --version 2>&1 || echo 'Not available')"
echo "Git: $(git --version 2>&1 || echo 'Not available')"
echo "Working Directory: $(pwd)"
echo "User: $(whoami)"

echo ""
echo "✅ Overseer development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Edit overseer/.env with your configuration"
echo "  2. Start the API server: cd overseer && python api/main.py"
echo "  3. Or use uvicorn: cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📚 Useful commands:"
echo "  - Run tests: cd overseer && pytest"
echo "  - Format code: black overseer/"
echo "  - Lint code: pylint overseer/"
echo ""
