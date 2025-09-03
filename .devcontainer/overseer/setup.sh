#!/bin/bash

# Manual Overseer Setup Script
# Run this after the devcontainer starts successfully

echo "🚀 Setting up Overseer AI Development Environment..."

# Function to handle errors
handle_error() {
    echo "❌ Error occurred in setup. Continuing with remaining setup..."
    return 0
}

# Set error handling
set -e
trap handle_error ERR

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -qq || echo "⚠️  Package update failed, continuing..."

# Install essential system tools including PostgreSQL and Redis clients
echo "📦 Installing essential system tools..."
sudo apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    vim \
    tree \
    jq \
    postgresql-client \
    redis-tools || echo "⚠️  Some system packages failed to install, continuing..."

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
npm install -g typescript@latest || echo "⚠️  TypeScript installation failed, continuing..."

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

# Fix VS Code extensions directory permissions
echo "🔧 Fixing VS Code extensions directory permissions..."
if [ -d "$HOME/.vscode-server/extensions" ]; then
    sudo chown -R vscode:vscode "$HOME/.vscode-server/extensions" || echo "⚠️  Could not fix extensions permissions, continuing..."
    chmod -R 755 "$HOME/.vscode-server/extensions" || echo "⚠️  Could not set extensions permissions, continuing..."
else
    echo "📁 Creating VS Code extensions directory..."
    mkdir -p "$HOME/.vscode-server/extensions"
    sudo chown -R vscode:vscode "$HOME/.vscode-server/extensions" || echo "⚠️  Could not set extensions ownership, continuing..."
    chmod -R 755 "$HOME/.vscode-server/extensions" || echo "⚠️  Could not set extensions permissions, continuing..."
fi

# Ensure Cline directory exists and has correct permissions
echo "🔧 Setting up Cline directory..."
if [ ! -d "$HOME/.cline" ]; then
    echo "📁 Creating Cline directory..."
    mkdir -p "$HOME/.cline"
fi
sudo chown -R vscode:vscode "$HOME/.cline" || echo "⚠️  Could not set Cline permissions, continuing..."

# Create backup directory for Cline contexts
if [ ! -d "$HOME/.cline-backups" ]; then
    echo "📁 Creating backup directory..."
    mkdir -p "$HOME/.cline-backups"
fi

# Wait for PostgreSQL to be ready
echo "🗄️  Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h postgres -p 5432 -U overseer > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo "⏳ Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Test Redis connection
echo "🔴 Testing Redis connection..."
if redis-cli -h redis ping > /dev/null 2>&1; then
    echo "✅ Redis connection: OK"
else
    echo "❌ Redis connection: Failed"
fi

# Set up database if .env exists
if [ -f "overseer/.env" ]; then
    echo "🗄️  Setting up database..."
    cd overseer || echo "⚠️  Could not change to overseer directory"

    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs) || true

    # Run database migrations if alembic is available
    if command -v alembic &> /dev/null; then
        echo "🔄 Running database migrations..."
        alembic upgrade head || echo "⚠️  Database migration failed, continuing..."
    fi
    cd ..
else
    echo "⚠️  .env file not found. Database setup skipped."
fi

# Health check
echo ""
echo "🏥 Environment Health Check:"
echo "Python: $(python --version 2>&1 || echo 'Not available')"
echo "Node: $(node --version 2>&1 || echo 'Not available')"
echo "NPM: $(npm --version 2>&1 || echo 'Not available')"
echo "Git: $(git --version 2>&1 || echo 'Not available')"
echo "PostgreSQL Client: $(psql --version 2>&1 || echo 'Not available')"
echo "Redis CLI: $(redis-cli --version 2>&1 || echo 'Not available')"
echo "Working Directory: $(pwd)"
echo "User: $(whoami)"

# Test database connection
if command -v psql &> /dev/null; then
    echo "🗄️  Testing PostgreSQL connection..."
    if pg_isready -h postgres -p 5432 -U overseer > /dev/null 2>&1; then
        echo "✅ PostgreSQL connection: OK"
    else
        echo "❌ PostgreSQL connection: Failed"
    fi
fi

echo ""
echo "✅ Overseer development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Edit overseer/.env with your configuration"
echo "  2. Run database migrations: cd overseer && alembic upgrade head"
echo "  3. Start the API server: cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📚 Useful commands:"
echo "  - Run tests: cd overseer && pytest"
echo "  - Format code: black overseer/"
echo "  - Lint code: pylint overseer/"
echo "  - Database shell: psql -h postgres -U overseer -d overseer"
echo "  - Redis shell: redis-cli -h redis"
echo ""
echo "🔧 Persistence commands:"
echo "  - Backup Cline contexts: ~/.vscode-devcontainer-settings/backup-cline-contexts.sh"
echo "  - Restore contexts: ~/.vscode-devcontainer-settings/restore-cline-contexts.sh"
echo "  - Install extensions: ~/.vscode-devcontainer-settings/install-cline.sh"
echo "  - Help: cat ~/.vscode-devcontainer-settings/README.md"
echo ""
