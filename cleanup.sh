#!/bin/bash

# Cleanup script for Data-Visualization-Agentic-Application
# Removes temporary and unnecessary files

echo "🧹 Cleaning up temporary files..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".eggs" -exec rm -rf {} + 2>/dev/null

# Remove macOS system files
echo "Removing .DS_Store files..."
find . -type f -name ".DS_Store" -delete 2>/dev/null
find .. -maxdepth 1 -type f -name ".DS_Store" -delete 2>/dev/null

# Remove Jupyter notebook checkpoints
echo "Removing Jupyter checkpoints..."
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null

# Remove IDE/editor files
echo "Removing IDE cache files..."
find . -type d -name ".idea" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".vscode" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.swp" -delete 2>/dev/null
find . -type f -name "*.swo" -delete 2>/dev/null
find . -type f -name "*~" -delete 2>/dev/null

# Remove log files
echo "Removing log files..."
find . -type f -name "*.log" -delete 2>/dev/null

# Remove coverage reports
echo "Removing coverage reports..."
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null
find . -type f -name ".coverage" -delete 2>/dev/null

# Remove build artifacts
echo "Removing build artifacts..."
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null

echo "✅ Cleanup complete!"

# Show git status
echo ""
echo "📋 Git status:"
git status --short
