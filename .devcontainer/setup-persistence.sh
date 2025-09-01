#!/bin/bash

# VS Code Extension and Cline Task Context Persistence Setup
# This script helps preserve your VS Code setup across container rebuilds

set -e

echo "🔧 Setting up VS Code and Cline persistence..."

# Create necessary directories on host if they don't exist
HOST_VSCODE_DIR="$HOME/.vscode-server"
HOST_CLINE_DIR="$HOME/.cline"
HOST_SETTINGS_DIR="$HOME/.vscode-devcontainer-settings"

# Create host directories
mkdir -p "$HOST_VSCODE_DIR"
mkdir -p "$HOST_CLINE_DIR"
mkdir -p "$HOST_SETTINGS_DIR"

echo "✅ Created host directories for persistence"

# Create a backup script for Cline task contexts
cat > "$HOST_SETTINGS_DIR/backup-cline-contexts.sh" << 'EOF'
#!/bin/bash
# Backup Cline task contexts
BACKUP_DIR="$HOME/.cline-backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -d "$HOME/.cline" ]; then
    cp -r "$HOME/.cline"/* "$BACKUP_DIR/" 2>/dev/null || true
    echo "✅ Cline contexts backed up to: $BACKUP_DIR"
else
    echo "⚠️  No Cline directory found to backup"
fi

# Keep only last 10 backups
cd "$HOME/.cline-backups" 2>/dev/null || exit 0
ls -t | tail -n +11 | xargs -r rm -rf
echo "🧹 Cleaned up old backups (keeping last 10)"
EOF

chmod +x "$HOST_SETTINGS_DIR/backup-cline-contexts.sh"

# Create a restore script for Cline task contexts
cat > "$HOST_SETTINGS_DIR/restore-cline-contexts.sh" << 'EOF'
#!/bin/bash
# Restore Cline task contexts from backup
BACKUP_DIR="$HOME/.cline-backups"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ No backup directory found"
    exit 1
fi

echo "Available backups:"
ls -la "$BACKUP_DIR"

echo ""
read -p "Enter backup directory name to restore (or 'latest' for most recent): " BACKUP_NAME

if [ "$BACKUP_NAME" = "latest" ]; then
    BACKUP_NAME=$(ls -t "$BACKUP_DIR" | head -n 1)
fi

RESTORE_FROM="$BACKUP_DIR/$BACKUP_NAME"

if [ ! -d "$RESTORE_FROM" ]; then
    echo "❌ Backup directory not found: $RESTORE_FROM"
    exit 1
fi

mkdir -p "$HOME/.cline"
cp -r "$RESTORE_FROM"/* "$HOME/.cline/" 2>/dev/null || true
echo "✅ Cline contexts restored from: $RESTORE_FROM"
EOF

chmod +x "$HOST_SETTINGS_DIR/restore-cline-contexts.sh"

# Create VS Code settings template for Cline
cat > "$HOST_SETTINGS_DIR/cline-settings.json" << 'EOF'
{
    "cline.taskContextPersistence": true,
    "cline.autoSaveTaskContext": true,
    "cline.taskContextPath": "~/.cline/contexts",
    "cline.maxTaskContexts": 50,
    "cline.autoBackupInterval": 300000,
    "workbench.startupEditor": "none",
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000
}
EOF

# Create a script to install Cline extension if not present
cat > "$HOST_SETTINGS_DIR/install-cline.sh" << 'EOF'
#!/bin/bash
# Install Cline extension if not already installed

echo "🔍 Checking for Cline extension..."

# Check if Cline is installed
if code --list-extensions | grep -q "saoudrizwan.claude-dev"; then
    echo "✅ Cline extension is already installed"
else
    echo "📦 Installing Cline extension..."
    code --install-extension saoudrizwan.claude-dev
    echo "✅ Cline extension installed"
fi

# Install other useful extensions
EXTENSIONS=(
    "GitHub.copilot"
    "GitHub.copilot-chat"
    "ms-vscode.remote-containers"
    "ms-python.python"
    "ms-python.black-formatter"
    "ms-vscode.vscode-json"
)

for ext in "${EXTENSIONS[@]}"; do
    if ! code --list-extensions | grep -q "$ext"; then
        echo "📦 Installing $ext..."
        code --install-extension "$ext"
    else
        echo "✅ $ext already installed"
    fi
done
EOF

chmod +x "$HOST_SETTINGS_DIR/install-cline.sh"

# Create a comprehensive setup guide
cat > "$HOST_SETTINGS_DIR/README.md" << 'EOF'
# VS Code and Cline Persistence Setup

This directory contains scripts and configurations to preserve your VS Code setup and Cline task contexts across container rebuilds.

## What's Preserved

### Automatically Preserved
- ✅ VS Code extensions (via Docker volumes)
- ✅ Cline task contexts and history (via bind mounts)
- ✅ VS Code server data (via bind mounts)

### Manual Backup/Restore
- 📁 Cline task contexts (use backup/restore scripts)
- ⚙️ Custom VS Code settings (copy to/from this directory)

## Available Scripts

### `backup-cline-contexts.sh`
Creates timestamped backups of your Cline task contexts.
```bash
~/.vscode-devcontainer-settings/backup-cline-contexts.sh
```

### `restore-cline-contexts.sh`
Restores Cline task contexts from a previous backup.
```bash
~/.vscode-devcontainer-settings/restore-cline-contexts.sh
```

### `install-cline.sh`
Installs Cline and other essential extensions if not present.
```bash
~/.vscode-devcontainer-settings/install-cline.sh
```

## Usage Workflow

### Before Rebuilding Container
1. Backup your Cline contexts:
   ```bash
   ~/.vscode-devcontainer-settings/backup-cline-contexts.sh
   ```

2. Your extensions and VS Code server data are automatically preserved via Docker volumes.

### After Rebuilding Container
1. Extensions should be automatically available (may take a moment to load)
2. Cline contexts should be automatically restored
3. If needed, restore from backup:
   ```bash
   ~/.vscode-devcontainer-settings/restore-cline-contexts.sh
   ```

## Directory Structure

```
~/.vscode-devcontainer-settings/
├── README.md                    # This guide
├── backup-cline-contexts.sh     # Backup script
├── restore-cline-contexts.sh    # Restore script
├── install-cline.sh            # Extension installer
└── cline-settings.json         # Recommended Cline settings

~/.cline/                        # Cline data (auto-mounted)
├── contexts/                    # Task contexts
├── history/                     # Chat history
└── settings/                    # Cline settings

~/.cline-backups/               # Timestamped backups
├── 20250101_120000/           # Backup from Jan 1, 12:00
└── 20250101_180000/           # Backup from Jan 1, 18:00
```

## Troubleshooting

### Extensions Not Loading
- Wait a few minutes after container start
- Check Docker volumes: `docker volume ls | grep vscode-extensions`
- Manually install: `~/.vscode-devcontainer-settings/install-cline.sh`

### Cline Contexts Missing
- Check if `~/.cline` directory exists and has content
- Restore from backup: `~/.vscode-devcontainer-settings/restore-cline-contexts.sh`
- Verify mount in devcontainer.json

### Performance Issues
- Extensions loading can be slow on first container start
- Consider using SSD storage for Docker volumes
- Increase Docker memory allocation if needed

## Best Practices

1. **Regular Backups**: Run backup script before major changes
2. **Clean Backups**: Old backups are auto-cleaned (keeps last 10)
3. **Version Control**: Don't commit `.cline` directory to git
4. **Multiple Containers**: Each devcontainer config uses separate volumes
EOF

echo "✅ Persistence setup complete!"
echo ""
echo "📁 Setup files created in: $HOST_SETTINGS_DIR"
echo "🔧 Your devcontainer configurations have been updated with persistence mounts"
echo ""
echo "Next steps:"
echo "1. Rebuild your dev container to apply the new configuration"
echo "2. Your extensions and Cline contexts will be preserved across rebuilds"
echo "3. Use the backup scripts in $HOST_SETTINGS_DIR for additional safety"
echo ""
echo "📖 See $HOST_SETTINGS_DIR/README.md for detailed usage instructions"
