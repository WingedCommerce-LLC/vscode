# VSCode Development Containers

This project supports multiple development container configurations to accommodate different development workflows.

## Available Configurations

### 1. Code - OSS (`code-oss/`)
The original VSCode development environment for working on the core VSCode codebase.

**Use this for:**
- VSCode core development
- Contributing to upstream VSCode
- Working on general VSCode features

**Features:**
- Full VSCode build environment
- Rust toolchain for CLI development
- Desktop environment with VNC
- 9GB memory allocation
- All necessary VSCode development tools

### 2. Overseer (`overseer/`)
AI-focused development environment optimized for the Overseer project - an AI-enabled director platform for development teams.

**Use this for:**
- Overseer feature development
- AI/ML development workflows
- API and frontend development
- Team management tool development

**Features:**
- Python 3.11 with AI/ML libraries
- Node.js 18 for frontend development
- Docker-in-Docker support
- 16GB memory allocation for AI workloads
- Pre-configured AI development tools
- Jupyter Lab support
- Database and Redis connectivity

## How to Use Multiple Devcontainers

### Method 1: VSCode Command Palette
1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type "Dev Containers: Reopen in Container"
3. Select the desired configuration:
   - `code-oss` for VSCode development
   - `overseer` for AI/Overseer development

### Method 2: VSCode UI
1. Click the green remote indicator in the bottom-left corner
2. Select "Reopen in Container"
3. Choose your desired configuration

### Method 3: Direct Configuration Selection
When VSCode detects multiple devcontainer configurations, it will prompt you to choose which one to use.

## Configuration Details

### Code - OSS Configuration
```json
{
  "name": "Code - OSS",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "desktop-lite": {},
    "rust": {}
  },
  "hostRequirements": { "memory": "9gb" }
}
```

### Overseer Configuration
```json
{
  "name": "Overseer - AI Development Platform",
  "image": "mcr.microsoft.com/devcontainers/python:3.11-bullseye",
  "features": {
    "node": { "version": "18" },
    "docker-in-docker": {},
    "git": {},
    "github-cli": {}
  },
  "hostRequirements": {
    "memory": "16gb",
    "storage": "32gb"
  }
}
```

## Port Forwarding

### Code - OSS Ports
- `6080`: VNC web client (noVNC)
- `5901`: VNC TCP port

### Overseer Ports
- `3000`: Frontend Dev Server
- `8000`: API Server
- `8080`: Alternative Web Server
- `8888`: Jupyter Notebook
- `5432`: PostgreSQL
- `3306`: MySQL
- `6379`: Redis

## Getting Started

### For VSCode Development (Code - OSS)
1. Select the `code-oss` configuration
2. Wait for container to build and start
3. Run `npm install` to install dependencies
4. Use `npm run watch` to start development

### For Overseer Development
1. Select the `overseer` configuration
2. Wait for container to build and post-create script to complete
3. Navigate to the `overseer/` directory
4. Copy `.env.template` to `.env` and configure
5. Start development:
   ```bash
   # API Development
   cd overseer && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

   # Jupyter Lab
   jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
   ```

## Switching Between Configurations

You can switch between configurations at any time:

1. **Save your work** in the current container
2. Use Command Palette → "Dev Containers: Reopen in Container"
3. Select the new configuration
4. VSCode will rebuild/restart with the new environment

## Troubleshooting

### Container Won't Start
- Check Docker is running
- Ensure you have sufficient memory (9GB for Code-OSS, 16GB for Overseer)
- Try rebuilding: Command Palette → "Dev Containers: Rebuild Container"

### Port Conflicts
- Check if ports are already in use on your host system
- Modify port forwarding in the respective `devcontainer.json`

### Performance Issues
- Increase Docker memory allocation in Docker Desktop settings
- Close unused applications to free up system resources
- Consider using volume mounts for better performance

## Customization

Each configuration can be customized by editing the respective `devcontainer.json` file:

- **Extensions**: Add/remove VSCode extensions
- **Settings**: Modify VSCode settings
- **Features**: Add/remove dev container features
- **Ports**: Change port forwarding configuration
- **Environment**: Modify environment variables

## Contributing

When contributing to this project:

1. **For VSCode core changes**: Use the `code-oss` configuration
2. **For Overseer features**: Use the `overseer` configuration
3. **For devcontainer improvements**: Test changes in both configurations

## Support

If you encounter issues with the development containers:

1. Check this README for common solutions
2. Review the specific configuration files
3. Check Docker and VSCode logs
4. Rebuild the container if necessary

---

**Note**: These configurations are designed to be completely separate environments. Choose the one that matches your current development focus.
