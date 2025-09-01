#!/bin/bash

# Overseer Development Environment Setup Script
echo "🚀 Setting up Overseer AI Development Environment..."

# Function to handle errors
handle_error() {
    echo "❌ Error occurred in setup. Continuing with basic setup..."
    return 0
}

# Set error handling
set -e
trap handle_error ERR

# Update system packages (minimal)
echo "📦 Updating system packages..."
sudo apt-get update -qq || echo "⚠️  Package update failed, continuing..."

# Install only essential system dependencies
echo "📦 Installing essential system tools..."
sudo apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    vim \
    tree \
    jq || echo "⚠️  Some system packages failed to install, continuing..."

# Upgrade pip quietly
echo "🐍 Upgrading pip..."
python -m pip install --upgrade pip --quiet --no-warn-script-location || echo "⚠️  Pip upgrade failed, continuing..."

# Install only core Python packages (minimal set)
echo "📦 Installing core Python packages..."
pip install --quiet --no-warn-script-location \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 || echo "⚠️  Some Python packages failed to install, continuing..."

# Install core Node.js tools
echo "📦 Installing core Node.js tools..."
npm install -g --silent typescript@5.3.0 || echo "⚠️  TypeScript installation failed, continuing..."

# Set up basic Git configuration
echo "🔧 Configuring Git..."
git config --global init.defaultBranch main || true
git config --global pull.rebase false || true

# Create basic directories if they don't exist
echo "📁 Ensuring directory structure..."
mkdir -p /workspaces || true
mkdir -p ~/.vscode-server || true

# Set proper permissions
chmod +x .devcontainer/overseer/post-create.sh || true

# Create a simple health check script
cat > /tmp/overseer-health.sh << 'EOF'
#!/bin/bash
echo "🏥 Overseer Health Check"
echo "Python: $(python --version 2>&1 || echo 'Not available')"
echo "Node: $(node --version 2>&1 || echo 'Not available')"
echo "NPM: $(npm --version 2>&1 || echo 'Not available')"
echo "Git: $(git --version 2>&1 || echo 'Not available')"
echo "Working Directory: $(pwd)"
echo "User: $(whoami)"
echo "✅ Basic environment ready!"
EOF

chmod +x /tmp/overseer-health.sh
/tmp/overseer-health.sh

echo "✅ Overseer development environment setup complete!"
echo ""
echo "🎯 Manual setup steps (run these after container starts):"
echo "  1. Install full Python deps: pip install -r overseer/requirements.txt"
echo "  2. Install Node deps: cd overseer && npm install"
echo "  3. Copy .env.template to .env and configure your environment"
echo "  4. Start the API server: cd overseer && python api/main.py"
echo ""
echo "📚 Useful commands:"
echo "  - Health check: /tmp/overseer-health.sh"
echo "  - API development: cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Run tests: cd overseer && pytest"
echo ""
