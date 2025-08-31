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

# Create Overseer-specific directories
echo "📁 Creating Overseer project structure..."
mkdir -p /workspace/overseer/{
    api,
    frontend,
    agents,
    models,
    data,
    scripts,
    tests,
    docs,
    config
}

# Create basic project files if they don't exist
if [ ! -f "/workspace/overseer/requirements.txt" ]; then
    cat > /workspace/overseer/requirements.txt << EOF
# Overseer AI Development Platform Dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
redis>=5.0.0
celery>=5.3.0
pandas>=2.1.0
numpy>=1.24.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
requests>=2.31.0
aiohttp>=3.8.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.9.0
pylint>=2.17.0
mypy>=1.5.0
pre-commit>=3.4.0
EOF
fi

if [ ! -f "/workspace/overseer/package.json" ]; then
    cat > /workspace/overseer/package.json << EOF
{
  "name": "overseer-platform",
  "version": "1.0.0",
  "description": "AI-Enabled Director Platform for Development Teams",
  "main": "index.js",
  "scripts": {
    "dev": "nodemon src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "lint": "eslint src/**/*.ts",
    "format": "prettier --write src/**/*.ts"
  },
  "keywords": ["ai", "development", "management", "overseer"],
  "author": "WingedCommerce LLC",
  "license": "PROPRIETARY",
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "nodemon": "^3.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0",
    "jest": "^29.0.0"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "dotenv": "^16.0.0"
  }
}
EOF
fi

# Set up Git configuration for Overseer development
echo "🔧 Configuring Git for Overseer development..."
git config --global init.defaultBranch main
git config --global pull.rebase false

# Create .env template for Overseer
if [ ! -f "/workspace/overseer/.env.template" ]; then
    cat > /workspace/overseer/.env.template << EOF
# Overseer Development Environment Variables
OVERSEER_ENV=development
DATABASE_URL=postgresql://overseer:password@localhost:5432/overseer_dev
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000

# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Authentication
JWT_SECRET=your_jwt_secret_here
SESSION_SECRET=your_session_secret_here

# Logging
LOG_LEVEL=debug
LOG_FORMAT=json
EOF
fi

# Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
cd /workspace
if [ -f "/workspace/.pre-commit-config.yaml" ]; then
    pre-commit install
fi

# Create basic Overseer API structure
if [ ! -f "/workspace/overseer/api/main.py" ]; then
    mkdir -p /workspace/overseer/api
    cat > /workspace/overseer/api/main.py << EOF
"""
Overseer API - Main FastAPI Application
AI-Enabled Director Platform for Development Teams
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Overseer API",
    description="AI-Enabled Director Platform for Development Teams",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Overseer API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "overseer-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
EOF
fi

# Set proper permissions
chmod +x /workspace/.devcontainer/overseer/post-create.sh

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
