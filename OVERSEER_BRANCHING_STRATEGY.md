# Overseer Product Branching Strategy

This document outlines the branching strategy for developing the Overseer product based on the VSCode open source repository while maintaining the ability to sync with upstream changes and contribute back selectively.

## Repository Structure

### Remotes
- **origin**: `git@github.com:WingedCommerce-LLC/vscode.git` (Your private fork)
- **upstream**: `git@github.com:microsoft/vscode.git` (Microsoft's source repository)

### Branch Structure

#### Core Branches

**main**
- Purpose: Clean mirror of Microsoft's upstream repository
- Contains: Only upstream VSCode changes, no Overseer modifications
- Usage: Source for upstream sync and base for contribution branches
- Protection: Never commit Overseer-specific code directly to this branch

**overseer-main**
- Purpose: Primary development branch for Overseer product
- Contains: All Overseer-specific features and customizations
- Usage: Base for feature branches, source for releases
- Protection: Stable codebase for Overseer product

#### Development Branches

**Feature Branches** (from overseer-main)
- Naming: `feature/overseer-[feature-name]`
- Examples: `feature/overseer-dashboard`, `feature/overseer-enhanced-debugger`
- Purpose: Active development of new Overseer features
- Lifecycle: Create → Develop → Test → Merge to overseer-main → Delete

**Contribution Branches** (from main)
- Naming: `contrib/[feature-name]`
- Purpose: Clean branches for contributing back to Microsoft
- Lifecycle: Create from main → Develop → PR to upstream → Delete after merge

## Workflows

### 1. Upstream Sync Workflow

When you want to pull in new changes from Microsoft's repository:

```bash
# Switch to main branch
git checkout main

# Pull latest changes from Microsoft
git pull upstream main

# Push updated main to your fork
git push origin main

# Now decide when/how to integrate into overseer-main
# Option A: Merge upstream changes into overseer-main
git checkout overseer-main
git merge main

# Option B: Rebase overseer-main onto updated main (cleaner history)
git checkout overseer-main
git rebase main
```

### 2. Feature Development Workflow

For developing new Overseer features:

```bash
# Start from overseer-main
git checkout overseer-main
git pull origin overseer-main

# Create feature branch
git checkout -b feature/overseer-new-feature

# Develop your feature
# ... make changes ...
git add .
git commit -m "feat: add new overseer feature"

# Push feature branch
git push -u origin feature/overseer-new-feature

# Create PR to merge into overseer-main
# After review and merge, delete feature branch
git branch -d feature/overseer-new-feature
git push origin --delete feature/overseer-new-feature
```

### 3. Contributing Back to Microsoft

For contributing improvements back to the open source project:

```bash
# Start from clean main (mirrors upstream)
git checkout main
git pull upstream main

# Create contribution branch
git checkout -b contrib/fix-some-issue

# Make your changes (ensure they're generic, not Overseer-specific)
# ... make changes ...
git add .
git commit -m "fix: resolve issue with [description]"

# Push to your fork
git push -u origin contrib/fix-some-issue

# Create PR to Microsoft's repository
# After Microsoft merges, clean up
git branch -d contrib/fix-some-issue
git push origin --delete contrib/fix-some-issue
```

## Privacy and Security

### Repository Privacy
- Your entire fork can be set to private in GitHub settings
- All Overseer branches (overseer-main, feature/*) remain private to your organization
- Only the main branch mirrors the public upstream repository

### Access Control
- Grant repository access only to authorized team members
- Use GitHub's branch protection rules for overseer-main
- Consider requiring PR reviews for merges to overseer-main

## Branch Protection Rules (Recommended)

For **overseer-main** branch:
- Require pull request reviews before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Restrict pushes that create merge conflicts

## Release Management

### Versioning Strategy
- Tag releases from overseer-main branch
- Use semantic versioning: `overseer-v1.0.0`, `overseer-v1.1.0`, etc.
- Maintain release notes documenting Overseer-specific changes

### Release Process
```bash
# From overseer-main
git checkout overseer-main
git pull origin overseer-main

# Tag the release
git tag -a overseer-v1.0.0 -m "Overseer v1.0.0 release"
git push origin overseer-v1.0.0
```

## Best Practices

1. **Keep main clean**: Never commit Overseer code to main branch
2. **Regular upstream sync**: Periodically sync with Microsoft's updates
3. **Feature isolation**: Develop each feature in its own branch
4. **Code review**: Use PRs for all merges to overseer-main
5. **Documentation**: Document Overseer-specific changes and decisions
6. **Testing**: Ensure all features work with latest upstream changes

## Troubleshooting

### Merge Conflicts During Upstream Sync
If conflicts occur when merging upstream changes:
```bash
git checkout overseer-main
git merge main
# Resolve conflicts in your editor
git add .
git commit -m "resolve: merge conflicts with upstream changes"
```

### Accidentally Committed to Main
If you accidentally commit Overseer code to main:
```bash
# Reset main to match upstream
git checkout main
git reset --hard upstream/main
git push origin main --force

# Cherry-pick your changes to overseer-main
git checkout overseer-main
git cherry-pick <commit-hash>
```

## Automation Scripts

The Overseer branching strategy includes several automation scripts to streamline common operations:

### 1. Upstream Sync Script (`scripts/sync-upstream.sh`)

Interactive script for syncing with Microsoft's VSCode repository:

```bash
./scripts/sync-upstream.sh
```

**Features:**
- Automatically fetches latest changes from upstream
- Shows preview of new commits before applying
- Offers to merge changes into overseer-main
- Handles error cases and provides guidance
- Returns to your original branch when complete

**Usage scenarios:**
- Weekly/monthly upstream synchronization
- Before starting major new features
- When you want to incorporate latest VSCode improvements

### 2. Branch Protection Setup (`scripts/setup-branch-protection.sh`)

Automated GitHub branch protection configuration:

```bash
./scripts/setup-branch-protection.sh
```

**Configures:**
- **main branch**: Prevents accidental commits, allows upstream sync
- **overseer-main branch**: Requires PR reviews, enforces quality gates

**Protection rules applied:**
- Enforce admin compliance
- Block force pushes and deletions
- Require pull request reviews (overseer-main only)
- Require conversation resolution (overseer-main only)
- Dismiss stale reviews automatically

### 3. Quick Setup Commands

For common development tasks:

```bash
# Start new feature
git checkout overseer-main && git pull origin overseer-main
git checkout -b feature/overseer-your-feature

# Sync with upstream
./scripts/sync-upstream.sh

# Setup repository protection (run once)
./scripts/setup-branch-protection.sh

# Create contribution branch
git checkout main && git pull upstream main
git checkout -b contrib/your-fix
```

### Script Requirements

- **Git**: Repository operations
- **GitHub CLI (gh)**: Branch protection and API operations
- **Bash**: Script execution environment

Install GitHub CLI if not available:
```bash
# macOS
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Other platforms: https://cli.github.com/
```

## Summary

This branching strategy provides:
- ✅ Clean separation between upstream and Overseer code
- ✅ Manual control over upstream integration
- ✅ Private development environment
- ✅ Ability to contribute back to open source
- ✅ Scalable feature development workflow
- ✅ Protection of intellectual property
- ✅ Automated scripts for common operations
- ✅ GitHub branch protection enforcement

Remember: Your main branch stays synchronized with Microsoft's repository, while all Overseer development happens in overseer-main and feature branches, keeping your proprietary code private and secure.
