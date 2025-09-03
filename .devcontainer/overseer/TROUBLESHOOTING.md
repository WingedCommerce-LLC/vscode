# Overseer Devcontainer Troubleshooting Guide

This guide addresses common issues encountered when starting the Overseer devcontainer, particularly the permission errors seen in the dev container logs.

## Common Issues and Solutions

### 1. VS Code Extensions Permission Errors

**Symptoms:**
```
Failed to create default profile extensions manifest in extensions installation folder.
file:///home/vscode/.vscode-server/extensions Unable to write file
'/home/vscode/.vscode-server/extensions/extensions.json'
(NoPermissions (FileSystemError): Error: EACCES: permission denied, open
'/home/vscode/.vscode-server/extensions/extensions.json')
```

**Solution:**
1. Run the setup script which includes permission fixes:
   ```bash
   ./.devcontainer/overseer/setup.sh
   ```

2. If the issue persists, manually fix permissions:
   ```bash
   sudo chown -R vscode:vscode ~/.vscode-server/extensions
   chmod -R 755 ~/.vscode-server/extensions
   ```

3. Reload VS Code window:
   ```
   Ctrl+Shift+P → "Developer: Reload Window"
   ```

### 2. Container Starts But Post-Create Script Skipped

**Symptoms:**
- Container starts successfully
- VS Code server runs but extensions have permission issues
- Log shows `--skip-post-create` flag was used

**Solution:**
This is expected behavior with the current minimal devcontainer setup. The post-create script is intentionally skipped to prevent startup crashes. Instead:

1. **Run the manual setup script** after container starts:
   ```bash
   ./.devcontainer/overseer/setup.sh
   ```

2. **Reload VS Code window** to ensure extensions load properly

### 3. Database Connection Issues

**Symptoms:**
- Cannot connect to PostgreSQL
- `pg_isready` commands fail

**Solution:**
1. Wait for services to start (the setup script includes wait logic)
2. Check if PostgreSQL container is running:
   ```bash
   docker ps | grep postgres
   ```
3. Test connection manually:
   ```bash
   pg_isready -h postgres -p 5432 -U overseer
   ```

### 4. TypeScript Installation Fails

**Symptoms:**
```
npm error code ETARGET
npm error notarget No matching version found for typescript@5.3.0.
npm error notarget In most cases you or one of your dependencies are requesting
npm error notarget a package version that doesn't exist.
```

**Solution:**
This is fixed in the updated setup script, but if you encounter it:
```bash
npm install -g typescript@latest
# or install a specific version that exists
npm install -g typescript@5.3.3
```

### 5. Environment Variables Not Loading (JWT_SECRET Error)

**Symptoms:**
```
ValueError: JWT_SECRET environment variable is required
```
API server fails to start even though `.env` file exists with `JWT_SECRET` set.

**Solution:**
This happens when the application doesn't load the `.env` file. The issue has been fixed by:

1. **Quick fix**: Run the installation and test script:
   ```bash
   cd overseer
   ./install_and_test.sh
   ```

2. **Manual fix**: Install python-dotenv and test:
   ```bash
   pip install python-dotenv>=1.0.0
   cd overseer
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify environment loading**:
   ```bash
   python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('JWT_SECRET:', os.getenv('JWT_SECRET')[:10] + '...' if os.getenv('JWT_SECRET') else 'Not found')"
   ```

### 6. Email Validator Missing Error

**Symptoms:**
```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
ModuleNotFoundError: No module named 'email_validator'
```

**Solution:**
This happens when Pydantic models use email validation but the email-validator package isn't installed:

1. **Quick fix**: Run the updated installation script:
   ```bash
   cd overseer
   ./install_and_test.sh
   ```

2. **Manual fix**: Install the missing dependency:
   ```bash
   pip install email-validator>=2.0.0
   # or install pydantic with email support
   pip install pydantic[email]>=2.4.0
   ```

### 7. Module Import Error (Wrong Working Directory)

**Symptoms:**
```
ModuleNotFoundError: No module named 'api'
```
API server fails to start with module import errors.

**Solution:**
This happens when running uvicorn from the wrong directory. The command must be run from within the `overseer` directory:

1. **Quick fix**: Use the installation script which handles this automatically:
   ```bash
   cd /workspaces/overseer
   ./install_and_test.sh
   ```

2. **Manual fix**: Change to the correct directory first:
   ```bash
   cd /workspaces/overseer
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify you're in the right directory**:
   ```bash
   pwd  # Should show /workspaces/overseer
   ls api/main.py  # Should exist
   ```

### 8. Cline Extension Not Working

**Symptoms:**
- Cline extension not loading
- Context persistence issues

**Solution:**
1. Ensure Cline directory exists and has correct permissions:
   ```bash
   ls -la ~/.cline
   sudo chown -R vscode:vscode ~/.cline
   ```

2. Use the persistence scripts:
   ```bash
   ~/.vscode-devcontainer-settings/install-cline.sh
   ~/.vscode-devcontainer-settings/backup-cline-contexts.sh
   ```

## Step-by-Step Recovery Process

If you encounter multiple issues, follow this recovery process:

### Step 1: Run Setup Script
```bash
./.devcontainer/overseer/setup.sh
```

### Step 2: Check Script Output
Look for any error messages and address them individually.

### Step 3: Reload VS Code
```
Ctrl+Shift+P → "Developer: Reload Window"
```

### Step 4: Verify Extensions
Check that required extensions are loaded in the Extensions panel.

### Step 5: Test Database Connection
```bash
pg_isready -h postgres -p 5432 -U overseer
```

### Step 6: Test Redis Connection
```bash
redis-cli -h redis ping
```

## Manual Permission Fixes

If the setup script doesn't resolve permission issues:

### Fix VS Code Server Permissions
```bash
sudo chown -R vscode:vscode ~/.vscode-server
chmod -R 755 ~/.vscode-server
```

### Fix Extensions Directory
```bash
sudo chown -R vscode:vscode ~/.vscode-server/extensions
chmod -R 755 ~/.vscode-server/extensions
```

### Fix Cline Directory
```bash
sudo chown -R vscode:vscode ~/.cline
chmod -R 755 ~/.cline
```

## Debugging Commands

### Check Container Status
```bash
docker ps
docker logs overseer-app-1
docker logs overseer-postgres-1
docker logs overseer-redis-1
```

### Check File Permissions
```bash
ls -la ~/.vscode-server/
ls -la ~/.vscode-server/extensions/
ls -la ~/.cline/
```

### Check Service Connectivity
```bash
pg_isready -h postgres -p 5432 -U overseer
redis-cli -h redis ping
```

### Check Environment
```bash
whoami
pwd
env | grep -E "(DATABASE|REDIS|NODE|OVERSEER)"
```

## Prevention

To avoid these issues in the future:

1. **Always run the setup script** after container starts
2. **Reload VS Code window** after running setup
3. **Don't modify volume mount configurations** without understanding the implications
4. **Use the provided persistence scripts** for Cline contexts

## Getting Help

If issues persist:

1. Check the main README: `.devcontainer/overseer/README.md`
2. Review Docker and VS Code logs
3. Try rebuilding the container: "Dev Containers: Rebuild Container"
4. Consider using the alternative code-oss devcontainer

## Log Analysis

When analyzing dev container logs, look for:

- **Permission errors**: Usually indicate ownership/permission issues
- **Service startup failures**: Check if PostgreSQL/Redis are healthy
- **Extension loading failures**: Often resolved by reloading VS Code window
- **Volume mount issues**: May require container rebuild

The key insight is that the current setup intentionally skips post-create scripts to ensure reliable container startup, requiring manual setup script execution instead.
