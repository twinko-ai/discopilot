#!/bin/bash

# Script to update DiscoPilot from GitHub and restart the service
# Usage: sudo ./update-discopilot.sh

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "=== DiscoPilot Update Script ==="
echo "Updating from GitHub repository..."

# Pull latest code from GitHub
if su - botuser -c "cd ~/discopilot && git pull"; then
  echo "✅ Successfully pulled latest code"
else
  echo "❌ Failed to pull from GitHub"
  echo "Checking for git conflicts..."
  su - botuser -c "cd ~/discopilot && git status"
  echo "You may need to resolve conflicts manually."
  exit 1
fi

# Reinstall dependencies with uv
echo "Reinstalling dependencies with uv..."
if su - botuser -c "cd ~/discopilot && bash scripts/deployment/install_dependencies.sh"; then
  echo "✅ Successfully installed dependencies"
else
  echo "❌ Failed to install dependencies"
  exit 1
fi

# Restart the service
echo "Restarting DiscoPilot service..."
if systemctl restart discopilot; then
  echo "✅ Successfully restarted DiscoPilot"
else
  echo "❌ Failed to restart service"
  exit 1
fi

# Check service status
echo "Checking service status..."
systemctl status discopilot --no-pager

echo ""
echo "To view logs, run: sudo journalctl -u discopilot -f"
echo "=== Update Complete ===" 