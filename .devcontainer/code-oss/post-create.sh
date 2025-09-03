#!/bin/bash

# Code-OSS Development Environment Setup Script
echo "🚀 Setting up Code-OSS Development Environment..."

# Set up persistence system
echo "🔧 Setting up dev container persistence..."

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

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm i || echo "⚠️  npm install failed, continuing..."

# Install extensions if they're missing
echo "🔌 Checking extensions..."
if ! code --list-extensions | grep -q "saoudrizwan.claude-dev"; then
    echo "📦 Installing Cline extension..."
    if [ -f "$HOME/.vscode-devcontainer-settings/install-cline.sh" ]; then
        "$HOME/.vscode-devcontainer-settings/install-cline.sh" || echo "⚠️  Extension installation script failed, continuing..."
    else
        echo "⚠️  Extension installation script not found, you may need to install extensions manually"
    fi
else
    echo "✅ Cline extension already installed"
fi

# Build and run electron
echo "🔧 Building and starting Electron..."
npm run electron || echo "⚠️  Electron startup failed, you may need to run it manually"

echo "✅ Code-OSS development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. VS Code should be starting in Electron mode"
echo "  2. Extensions should be available after a few minutes"
echo "  3. Cline contexts are preserved across rebuilds"
echo ""
echo "📚 Useful commands:"
echo "  - Build: npm run compile"
echo "  - Watch: npm run watch"
echo "  - Test: npm test"
echo ""
echo "🔧 Persistence commands:"
echo "  - Backup Cline contexts: ~/.vscode-devcontainer-settings/backup-cline-contexts.sh"
echo "  - Restore contexts: ~/.vscode-devcontainer-settings/restore-cline-contexts.sh"
echo "  - Install extensions: ~/.vscode-devcontainer-settings/install-cline.sh"
echo "  - Help: cat ~/.vscode-devcontainer-settings/README.md"
echo ""
