# Overseer Features

This directory contains Overseer-specific enhancements to VSCode.

## Sample Feature

This is a test feature to demonstrate the branching strategy workflow.

### Features Added
- Sample Overseer functionality
- Demonstrates private development workflow
- Shows how to isolate Overseer code from upstream

### Development Notes
- This feature was developed in the `feature/overseer-sample-test` branch
- It will be merged into `overseer-main` after review
- This code remains private to WingedCommerce-LLC

## Architecture

Overseer features are organized under `src/vs/workbench/contrib/overseer/` to:
1. Keep them separate from core VSCode functionality
2. Make it easy to identify Overseer-specific code
3. Minimize conflicts during upstream merges
4. Maintain clear ownership of intellectual property
