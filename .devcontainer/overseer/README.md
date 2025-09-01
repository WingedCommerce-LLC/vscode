# Overseer Devcontainer

This devcontainer provides a minimal, stable environment for developing the Overseer AI platform.

## Quick Start

1. **Open in devcontainer**: Use VS Code's "Reopen in Container" command
2. **Wait for container to start**: The container should start without crashes
3. **Run setup script**: Execute `./devcontainer/overseer/setup.sh` to install dependencies
4. **Start developing**: Begin working on your Overseer features

## What's Included

### Base Environment
- **Python 3.11** with pip
- **Node.js 22.18.0** with npm
- **Git** for version control
- **VS Code extensions**: Python, Black formatter, JSON, Docker

### Manual Setup (via setup.sh)
- Essential system tools (build-essential, curl, vim, tree, jq)
- Core Python packages (FastAPI, Uvicorn, Pydantic)
- TypeScript
- Full Overseer dependencies from requirements.txt and package.json
- Environment file setup (.env from template)

## Why This Approach?

The previous devcontainer configuration was causing crashes due to:
- Resource-intensive post-create commands
- Complex volume mounts and permissions
- Too many features loaded simultaneously
- VSCode server settings conflicts

This simplified approach:
- ✅ Starts reliably without crashes
- ✅ Provides core development tools immediately
- ✅ Allows manual dependency installation when ready
- ✅ Eliminates permission and volume mount issues

## Usage

### After Container Starts

1. **Run the setup script**:
   ```bash
   ./devcontainer/overseer/setup.sh
   ```

2. **Configure environment**:
   ```bash
   # Edit your environment variables
   code overseer/.env
   ```

3. **Start the API server**:
   ```bash
   cd overseer
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access your application**:
   - API: http://localhost:8000
   - Frontend: http://localhost:3000 (when running)

### Development Commands

```bash
# Install dependencies
pip install -r overseer/requirements.txt
cd overseer && npm install

# Run tests
cd overseer && pytest

# Format code
black overseer/

# Lint code
pylint overseer/

# Start development servers
cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Container Won't Start
- Ensure Docker has sufficient resources (8GB+ RAM recommended)
- Try rebuilding the container: "Dev Containers: Rebuild Container"
- Check Docker logs for specific error messages

### Setup Script Fails
- Run individual commands from the script manually
- Check internet connectivity for package downloads
- Verify file permissions: `ls -la .devcontainer/overseer/setup.sh`

### VSCode Extensions Not Loading
- Reload the window: Ctrl+Shift+P → "Developer: Reload Window"
- Check extension installation in the Extensions panel
- Some extensions may need manual installation

## Configuration Files

- `devcontainer.json`: Minimal container configuration
- `setup.sh`: Manual dependency installation script
- `post-create.sh`: Legacy script (not used in current setup)

## Next Steps

Once the basic container is working:
1. You can gradually add more features to devcontainer.json
2. Consider adding back Docker-in-Docker if needed
3. Add more VS Code extensions as required
4. Customize the setup script for your specific needs

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Docker and VS Code logs
3. Try the manual setup approach
4. Consider using the code-oss devcontainer as an alternative
