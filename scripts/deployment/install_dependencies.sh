#!/bin/bash

echo "=== Installing DiscoPilot Dependencies with uv from pyproject.toml ==="

# Change to the discopilot directory
cd /home/botuser/discopilot

# Use the correct path to uv
UV_PATH="/home/botuser/.local/bin/uv"

# Check if uv is available
if [ ! -f "$UV_PATH" ]; then
    echo "❌ uv not found at $UV_PATH"
    echo "Attempting to install uv..."
    
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Check if installation succeeded
    if [ ! -f "$UV_PATH" ]; then
        echo "❌ Failed to install uv. Cannot proceed."
        exit 1
    else
        echo "✅ Successfully installed uv at $UV_PATH"
    fi
else
    echo "✅ Found uv at $UV_PATH"
fi

# Create or update virtual environment
echo "Creating/updating virtual environment..."
"$UV_PATH" venv
echo "✅ Virtual environment created/updated with uv"

# Check for pyproject.toml
if [ -f "pyproject.toml" ]; then
    echo "Installing dependencies from pyproject.toml..."
    "$UV_PATH" pip install -e .
    echo "✅ Dependencies installed from pyproject.toml"
else
    echo "❌ No pyproject.toml found. Cannot proceed."
    exit 1
fi

# Ensure discord.py is installed (in case it's not in pyproject.toml)
echo "Ensuring discord.py is installed..."
"$UV_PATH" pip install discord.py
echo "✅ discord.py installed/verified"

echo "=== Dependency Installation Complete ==="