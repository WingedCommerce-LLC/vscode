#!/bin/bash

# Overseer Development Environment Setup Script
echo "🚀 Setting up Overseer AI Development Environment..."

# Update system packages
sudo apt-get update

# Install additional system dependencies for AI development
sudo apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    jq \
    sqlite3 \
    postgresql-client \
    redis-tools

# Install Python AI/ML packages
echo "📦 Installing Python AI/ML packages..."
pip install --upgrade pip
pip install \
    fastapi \
    uvicorn \
    pydantic \
    sqlalchemy \
    alembic \
    psycopg2-binary \
    redis \
    celery \
    pandas \
    numpy \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyter \
    jupyterlab \
    notebook \
    requests \
    aiohttp \
    pytest \
    pytest-asyncio \
    black \
    pylint \
    mypy \
    pre-commit

# Install Node.js packages for frontend development
echo "📦 Installing Node.js packages..."
npm install -g \
    typescript \
    ts-node \
    nodemon \
    pm2 \
    @types/node \
    eslint \
    prettier

# Overseer project structure already exists in the repository
echo "📁 Overseer project structure found..."

# Set up Git configuration for Overseer development
echo "🔧 Configuring Git for Overseer development..."
git config --global init.defaultBranch main
git config --global pull.rebase false

# Install Python dependencies from requirements.txt
echo "📦 Installing Overseer Python dependencies..."
if [ -f "overseer/requirements.txt" ]; then
    pip install -r overseer/requirements.txt
fi

# Install Node.js dependencies
echo "📦 Installing Overseer Node.js dependencies..."
if [ -f "overseer/package.json" ]; then
    cd overseer && npm install && cd ..
fi

# Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
fi

# Set proper permissions
chmod +x .devcontainer/overseer/post-create.sh

echo "✅ Overseer development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Copy .env.template to .env and configure your environment variables"
echo "  2. Start the API server: cd overseer && python api/main.py"
echo "  3. Access Jupyter Lab: jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
echo "  4. Begin developing your AI-enabled director features!"
echo ""
echo "📚 Useful commands:"
echo "  - API development: cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Install Python deps: pip install -r overseer/requirements.txt"
echo "  - Install Node deps: cd overseer && npm install"
echo "  - Run tests: cd overseer && pytest"
echo ""
