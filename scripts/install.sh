#!/bin/bash

# Repo Health Analyzer Installation Script
# Cross-platform installation for Python-based RHA tool

set -e

echo "🏥 Installing Repo Health Analyzer..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "📥 Installing Repo Health Analyzer..."
pip install -e .

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install -e ".[dev]"

# Verify installation
echo "🧪 Verifying installation..."
if command -v rha &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "Usage:"
    echo "  rha analyze                    # Analyze current directory"
    echo "  rha analyze /path/to/repo      # Analyze specific repository"
    echo "  rha analyze --visualize        # Generate visualizations"
    echo "  rha validate                   # Validate repository"
    echo "  rha --help                     # Show help"
    echo ""
    echo "🎉 Repo Health Analyzer is ready to use!"
else
    echo "❌ Installation verification failed"
    exit 1
fi
