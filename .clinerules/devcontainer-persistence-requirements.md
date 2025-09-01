## Brief overview
Global requirements for implementing VS Code extension and Cline task context persistence in all new development projects using dev containers. This ensures consistent development environment setup and prevents loss of extensions and task contexts across container rebuilds.

## Dev container configuration requirements
- Always include Docker volume mounts for VS Code extensions using project-specific volume names (e.g., `{project-name}-vscode-extensions`)
- Include bind mounts for Cline data directory (`~/.cline`) to preserve task contexts and chat history
- Add bind mount for VS Code server data (`~/.vscode-server`) to maintain settings and workspace state
- Configure separate extension volumes for each devcontainer configuration in multi-container projects

## Required extensions in devcontainer.json
- Always include `saoudrizwan.claude-dev` (Cline) in the extensions list
- Include essential development extensions: `GitHub.copilot`, `GitHub.copilot-chat`, `ms-vscode.remote-containers`
- Add project-specific extensions based on tech stack (Python, Node.js, Docker, etc.)
- Configure Cline-specific settings: `cline.taskContextPersistence: true`, `cline.autoSaveTaskContext: true`

## Persistence setup automation
- Create a `setup-persistence.sh` script in `.devcontainer/` directory for each new project
- Script must create host directories for persistence (`~/.vscode-server`, `~/.cline`, `~/.vscode-devcontainer-settings`)
- Generate backup and restore scripts for Cline contexts with timestamped backups
- Include extension installation script as fallback for missing extensions
- Provide comprehensive README with troubleshooting guide in `~/.vscode-devcontainer-settings/`

## Project documentation requirements
- Include `DEVCONTAINER_PERSISTENCE.md` in project root explaining the persistence setup
- Document the specific volume names and mount points used for the project
- Provide clear instructions for rebuilding containers and verifying persistence
- Include troubleshooting section for common issues (extensions not loading, contexts missing)

## Backup and recovery workflow
- Implement automatic backup system that keeps last 10 timestamped backups
- Provide manual backup script that can be run before major changes or container rebuilds
- Include restore functionality with option to restore from latest or specific backup
- Ensure backup scripts are executable and properly documented

## Multi-container project considerations
- Use separate Docker volumes for each devcontainer configuration
- Share Cline data directory across all containers in the same project
- Name volumes descriptively to avoid conflicts between projects
- Document container-specific extensions and their purposes
