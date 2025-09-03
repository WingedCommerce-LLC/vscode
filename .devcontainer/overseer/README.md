# Overseer Devcontainer

This devcontainer provides a minimal, stable environment for developing the Overseer AI platform.

## Quick Start

1. **Open in devcontainer**: Use VS Code's "Reopen in Container" command
2. **Wait for container to start**: The container should start without crashes
3. **Run setup script**: Execute `./.devcontainer/overseer/setup.sh` to install dependencies and fix permissions
4. **Reload VS Code window**: Press `Ctrl+Shift+P` → "Developer: Reload Window" to ensure extensions load properly
5. **Start developing**: Begin working on your Overseer features

## What's Included

### Base Environment
- **Python 3.11** with pip
- **Node.js 22.18.0** with npm
- **Git** for version control
- **VS Code extensions**: Python, Black formatter, JSON, Docker

### Manual Setup (via setup.sh)
- Essential system tools (build-essential, curl, vim, tree, jq)
- PostgreSQL and Redis client tools
- Core Python packages (FastAPI, Uvicorn, Pydantic)
- TypeScript
- Full Overseer dependencies from requirements.txt and package.json
- Environment file setup (.env from template)
- VS Code extensions directory permission fixes
- Cline directory setup and permissions
- Database connection testing and migration setup

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
   ./.devcontainer/overseer/setup.sh
   ```

2. **Reload VS Code window** (important for extensions):
   ```
   Ctrl+Shift+P → "Developer: Reload Window"
   ```

3. **Configure environment**:
   ```bash
   # Edit your environment variables
   code overseer/.env
   ```

4. **Run database migrations**:
   ```bash
   cd overseer
   alembic upgrade head
   ```

5. **Start the API server**:
   ```bash
   cd overseer
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access your application**:
   - API: http://localhost:8000
   - Frontend: http://localhost:3000 (when running)
   - Database: `psql -h postgres -U overseer -d overseer`
   - Redis: `redis-cli -h redis`

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
- Make script executable: `chmod +x .devcontainer/overseer/setup.sh`

### VSCode Extensions Not Loading
- **Most common fix**: Run the setup script first, then reload VS Code window
- Reload the window: Ctrl+Shift+P → "Developer: Reload Window"
- Check extension installation in the Extensions panel
- Verify extensions directory permissions: `ls -la ~/.vscode-server/extensions`
- Some extensions may need manual installation

### Permission Errors
- Run the setup script which includes permission fixes
- Check file ownership: `ls -la ~/.vscode-server/`
- Manually fix permissions if needed:
  ```bash
  sudo chown -R vscode:vscode ~/.vscode-server/extensions
  chmod -R 755 ~/.vscode-server/extensions
  ```

### Database Connection Issues
- Ensure PostgreSQL service is running: `docker ps | grep postgres`
- Test connection: `pg_isready -h postgres -p 5432 -U overseer`
- Check environment variables in `overseer/.env`
- Wait for services to be ready (setup script includes wait logic)

### Cline Extension Issues
- Ensure Cline directory exists: `ls -la ~/.cline`
- Check permissions: `sudo chown -R vscode:vscode ~/.cline`
- Use persistence scripts in `~/.vscode-devcontainer-settings/`

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
