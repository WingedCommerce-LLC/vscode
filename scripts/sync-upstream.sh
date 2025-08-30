#!/bin/bash

# Overseer Upstream Sync Script
# This script helps sync your main branch with Microsoft's VSCode repository

set -e

echo "🔄 Starting upstream sync process..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if upstream remote exists
if ! git remote get-url upstream > /dev/null 2>&1; then
    echo "❌ Error: 'upstream' remote not found"
    echo "Please add the upstream remote:"
    echo "git remote add upstream git@github.com:microsoft/vscode.git"
    exit 1
fi

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Switch to main branch
echo "🔀 Switching to main branch..."
git checkout main

# Fetch latest changes from upstream
echo "📥 Fetching latest changes from Microsoft's repository..."
git fetch upstream

# Check if there are new commits
BEHIND_COUNT=$(git rev-list --count HEAD..upstream/main)
if [ "$BEHIND_COUNT" -eq 0 ]; then
    echo "✅ Already up to date with upstream"
else
    echo "📊 Found $BEHIND_COUNT new commits from upstream"

    # Show what's new
    echo "🆕 New commits:"
    git log --oneline HEAD..upstream/main | head -10

    # Ask for confirmation
    read -p "Do you want to pull these changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Pull changes from upstream
        echo "⬇️  Pulling changes from upstream..."
        git pull upstream main

        # Push updated main to origin
        echo "⬆️  Pushing updated main to origin..."
        git push origin main

        echo "✅ Main branch successfully synced with upstream"

        # Ask about merging into overseer-main
        read -p "Do you want to merge these changes into overseer-main? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🔀 Switching to overseer-main..."
            git checkout overseer-main

            echo "🔄 Merging main into overseer-main..."
            if git merge main --no-edit; then
                echo "✅ Successfully merged upstream changes into overseer-main"

                # Push updated overseer-main
                read -p "Push updated overseer-main to origin? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    git push origin overseer-main
                    echo "✅ Pushed updated overseer-main to origin"
                fi
            else
                echo "⚠️  Merge conflicts detected!"
                echo "Please resolve conflicts manually, then run:"
                echo "git add ."
                echo "git commit"
                echo "git push origin overseer-main"
                exit 1
            fi
        fi
    else
        echo "⏭️  Skipping upstream sync"
    fi
fi

# Return to original branch
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "overseer-main" ]; then
    echo "🔙 Returning to $CURRENT_BRANCH..."
    git checkout "$CURRENT_BRANCH"
fi

echo "🎉 Upstream sync process completed!"
