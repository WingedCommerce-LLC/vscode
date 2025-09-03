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

# Install essential system dependencies including PostgreSQL client
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

# Upgrade pip quietly
echo "🐍 Upgrading pip..."
python -m pip install --upgrade pip --quiet --no-warn-script-location || echo "⚠️  Pip upgrade failed, continuing..."

# Navigate to overseer directory and install Python dependencies
echo "📦 Installing Overseer Python dependencies..."
cd /workspaces/vscode/overseer || cd /workspaces/*/overseer || {
    echo "⚠️  Could not find overseer directory, skipping Python deps installation"
    exit 0
}

# Install Python dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet --no-warn-script-location || echo "⚠️  Some Python packages failed to install, continuing..."
else
    echo "⚠️  requirements.txt not found, installing core packages..."
    pip install --quiet --no-warn-script-location \
        fastapi==0.104.1 \
        uvicorn==0.24.0 \
        pydantic==2.5.0 \
        sqlalchemy \
        alembic \
        psycopg2-binary \
        python-jose[cryptography] \
        passlib[bcrypt] \
        python-multipart || echo "⚠️  Some Python packages failed to install, continuing..."
fi

# Install core Node.js tools
echo "📦 Installing core Node.js tools..."
npm install -g --silent typescript@5.3.0 || echo "⚠️  TypeScript installation failed, continuing..."

# Set up basic Git configuration
echo "🔧 Configuring Git..."
git config --global init.defaultBranch main || true
git config --global pull.rebase false || true

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

# Set up database if .env exists
if [ -f ".env" ]; then
    echo "🗄️  Setting up database..."
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs) || true

    # Run database migrations
    if command -v alembic &> /dev/null; then
        echo "🔄 Running database migrations..."
        alembic upgrade head || echo "⚠️  Database migration failed, continuing..."
    fi
else
    echo "⚠️  .env file not found. Please copy .env.template to .env and configure your environment"
fi

# Create a health check script
cat > /tmp/overseer-health.sh << 'EOF'
#!/bin/bash
echo "🏥 Overseer Health Check"
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

# Test Redis connection
if command -v redis-cli &> /dev/null; then
    echo "🔴 Testing Redis connection..."
    if redis-cli -h redis ping > /dev/null 2>&1; then
        echo "✅ Redis connection: OK"
    else
        echo "❌ Redis connection: Failed"
    fi
fi

echo "✅ Environment health check complete!"
EOF

chmod +x /tmp/overseer-health.sh
/tmp/overseer-health.sh

# Set up persistence system
echo "🔧 Setting up dev container persistence..."

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

# Ensure Cline directory exists on host
if [ ! -d "$HOME/.cline" ]; then
    echo "📁 Creating Cline directory..."
    mkdir -p "$HOME/.cline"
fi

# Create backup directory
if [ ! -d "$HOME/.cline-backups" ]; then
    echo "📁 Creating backup directory..."
    mkdir -p "$HOME/.cline-backups"
fi

# Install extensions if they're missing
echo "🔌 Checking and installing required extensions..."

# List of required extensions
REQUIRED_EXTENSIONS=(
    "saoudrizwan.claude-dev"
    "ms-vscode.npm-scripts"
    "ms-python.python"
    "ms-python.black-formatter"
    "ms-vscode.vscode-json"
    "ms-vscode.vscode-docker"
    "ms-python.pylint"
    "ms-python.flake8"
    "GitHub.copilot"
    "GitHub.copilot-chat"
    "ms-vscode.remote-containers"
    "ms-vscode.remote-ssh"
    "ms-vscode.remote-wsl"
)

# Install missing extensions
for extension in "${REQUIRED_EXTENSIONS[@]}"; do
    if ! code --list-extensions | grep -q "$extension"; then
        echo "📦 Installing extension: $extension"
        code --install-extension "$extension" --force || echo "⚠️  Failed to install $extension, continuing..."
    else
        echo "✅ Extension already installed: $extension"
    fi
done

# Run the Cline installation script if available
if [ -f "$HOME/.vscode-devcontainer-settings/install-cline.sh" ]; then
    echo "🔧 Running Cline installation script..."
    "$HOME/.vscode-devcontainer-settings/install-cline.sh" || echo "⚠️  Extension installation script failed, continuing..."
fi

echo "✅ Overseer development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Copy .env.template to .env: cp .env.template .env"
echo "  2. Update .env with your configuration"
echo "  3. Run database migrations: alembic upgrade head"
echo "  4. Start the API server: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📚 Useful commands:"
echo "  - Health check: /tmp/overseer-health.sh"
echo "  - Database shell: psql -h postgres -U overseer -d overseer"
echo "  - Redis shell: redis-cli -h redis"
echo "  - Run tests: pytest"
echo ""
echo "🔧 Persistence commands:"
echo "  - Backup Cline contexts: ~/.vscode-devcontainer-settings/backup-cline-contexts.sh"
echo "  - Restore contexts: ~/.vscode-devcontainer-settings/restore-cline-contexts.sh"
echo "  - Install extensions: ~/.vscode-devcontainer-settings/install-cline.sh"
echo "  - Help: cat ~/.vscode-devcontainer-settings/README.md"
echo ""
