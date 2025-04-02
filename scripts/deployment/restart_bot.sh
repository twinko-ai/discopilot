#!/bin/bash

# Script to restart the DiscoPilot service
# Usage: sudo ./restart-discopilot.sh

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "=== DiscoPilot Restart Script ==="

# Stop the service
echo "Stopping DiscoPilot service..."
if systemctl stop discopilot; then
  echo "✅ Successfully stopped DiscoPilot"
else
  echo "❌ Failed to stop service"
  exit 1
fi

# Small delay to ensure clean shutdown
sleep 2

# Start the service
echo "Starting DiscoPilot service..."
if systemctl start discopilot; then
  echo "✅ Successfully started DiscoPilot"
else
  echo "❌ Failed to start service"
  exit 1
fi

# Check service status
echo "Checking service status..."
systemctl status discopilot --no-pager

echo ""
echo "To view logs, run: sudo journalctl -u discopilot -f"
echo "=== Restart Complete ===" 