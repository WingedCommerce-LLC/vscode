#!/bin/bash

# Overseer Branch Protection Setup Script
# This script configures GitHub branch protection rules for the Overseer branching strategy

set -e

echo "🔒 Setting up branch protection rules for Overseer repository..."

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub CLI"
    echo "Please run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📍 Repository: $REPO"

echo "🔒 Setting up protection for 'main' branch..."
# Protect main branch - keep it clean for upstream sync
gh api repos/$REPO/branches/main/protection -X PUT --input - <<< '{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}' > /dev/null

echo "✅ Main branch protection configured"

echo "🔒 Setting up protection for 'overseer-main' branch..."
# Protect overseer-main branch - require reviews for production code
# Note: enforce_admins is false to allow repository owners/maintainers to approve their own PRs
gh api repos/$REPO/branches/overseer-main/protection -X PUT --input - <<< '{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}' > /dev/null

echo "✅ Overseer-main branch protection configured"

echo "📋 Branch protection summary:"
echo "  main branch:"
echo "    ✅ Enforce admins"
echo "    ✅ Block force pushes"
echo "    ✅ Block deletions"
echo "    ✅ Allow fork syncing (for upstream updates)"
echo ""
echo "  overseer-main branch:"
echo "    ✅ Require 1 pull request review"
echo "    ✅ Dismiss stale reviews"
echo "    ✅ Require conversation resolution"
echo "    ✅ Allow owner/maintainer self-approval"
echo "    ✅ Block force pushes"
echo "    ✅ Block deletions"

echo "🎉 Branch protection setup completed!"
echo ""
echo "💡 Tips:"
echo "  - Use feature branches for all Overseer development"
echo "  - Never commit directly to main or overseer-main"
echo "  - Create pull requests for code review"
echo "  - Use ./scripts/sync-upstream.sh for upstream updates"
