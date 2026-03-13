#!/bin/bash

# K3s-Sentinel Setup Script

set -e

echo "Setting up K3s-Sentinel..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1)
if [ "$python_version" -lt 3 ]; then
    echo "Error: Python 3.9+ required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config directory
mkdir -p config

# Copy example config if not exists
if [ ! -f config/settings.py ]; then
    cp config/settings.example.py config/settings.py 2>/dev/null || true
fi

# Create data directory
mkdir -p data

echo ""
echo "K3s-Sentinel setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your settings in config/settings.py"
echo "2. Set LLM_API_KEY environment variable"
echo "3. Run: python main.py"
echo ""
