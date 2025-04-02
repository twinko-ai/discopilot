#!/bin/bash

# AWS Lightsail Launch Script for DiscoPilot
# Copy this script into the "Launch Script" section when creating a Lightsail instance

# Enable debugging and logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting DiscoPilot setup script at $(date)"
set -e  # Exit immediately if a command exits with a non-zero status
set -x  # Print commands and their arguments as they are executed

# Update system packages
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y python3-pip git python3-venv curl

# Create a dedicated user for the bot
useradd -m -s /bin/bash botuser
if [ ! -d "/home/botuser" ]; then
  echo "ERROR: Failed to create home directory for botuser"
  mkdir -p /home/botuser
  chown botuser:botuser /home/botuser
fi

# Verify botuser home directory
ls -la /home/botuser || echo "WARNING: Cannot list botuser home directory"

# Clone the public repository
echo "Cloning DiscoPilot repository..."
su - botuser -c "git clone https://github.com/twinko-ai/discopilot.git ~/discopilot"
if [ ! -d "/home/botuser/discopilot" ]; then
  echo "ERROR: Failed to clone repository"
  exit 1
fi

# Install uv for package management
echo "Installing uv for package management..."
su - botuser -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
echo 'export PATH="/home/botuser/.local/bin:$PATH"' >> /home/botuser/.bashrc
su - botuser -c "source ~/.bashrc"

# Run the dependency installation script
echo "Installing dependencies using the existing script..."
su - botuser -c "cd ~/discopilot && bash ./scripts/deployment/install_dependencies.sh"

# Create config directory with multiple methods to ensure success
echo "Creating config directory..."
sudo -u botuser mkdir -p /home/botuser/.config/discopilot
if [ ! -d "/home/botuser/.config/discopilot" ]; then
  echo "WARNING: Failed to create config directory as botuser, trying as root"
  mkdir -p /home/botuser/.config/discopilot
  chown -R botuser:botuser /home/botuser/.config
fi

# Verify config directory exists and has correct permissions
ls -la /home/botuser/.config || echo "WARNING: Cannot list .config directory"
chmod 700 /home/botuser/.config/discopilot
chown -R botuser:botuser /home/botuser/.config

# Create a template config file with Twitter OAuth 2.0 support
echo "Creating config file..."
cat > /tmp/discopilot_config.yaml << 'CONFIGEOF'
# DiscoPilot Configuration

discord:
  token: "REPLACE_WITH_YOUR_DISCORD_TOKEN"
  server_ids:
    - 0000000000000000  # Replace with your Discord server ID

admin_ids:
  - 0000000000000000  # Replace with your Discord user ID

triggers:
  emoji: "📢"  # The emoji that triggers publishing

twitter:
  # Twitter API v1.1 credentials (for compatibility)
  api_key: "REPLACE_WITH_YOUR_TWITTER_API_KEY"
  api_secret: "REPLACE_WITH_YOUR_TWITTER_API_SECRET"
  access_token: "REPLACE_WITH_YOUR_TWITTER_ACCESS_TOKEN"
  access_secret: "REPLACE_WITH_YOUR_TWITTER_ACCESS_SECRET"
  
  # Twitter API v2 OAuth 2.0 credentials
  client_id: "REPLACE_WITH_YOUR_TWITTER_CLIENT_ID"
  client_secret: "REPLACE_WITH_YOUR_TWITTER_CLIENT_SECRET"
CONFIGEOF

# Copy the config file to the correct location
cp /tmp/discopilot_config.yaml /home/botuser/.config/discopilot/config.yaml
rm /tmp/discopilot_config.yaml

# Set proper ownership and permissions for the config file
chown botuser:botuser /home/botuser/.config/discopilot/config.yaml
chmod 600 /home/botuser/.config/discopilot/config.yaml

# Verify config file exists
if [ ! -f "/home/botuser/.config/discopilot/config.yaml" ]; then
  echo "ERROR: Failed to create config file"
  exit 1
fi

# Show the config file (without sensitive data)
echo "Config file created:"
ls -la /home/botuser/.config/discopilot/config.yaml

# Copy the run script to a system location for the service
echo "Setting up run script..."
cp /home/botuser/discopilot/scripts/deployment/run_discopilot.sh /usr/local/bin/run-discopilot.sh
chmod +x /usr/local/bin/run-discopilot.sh

# Copy maintenance scripts from the repository to system location
echo "Setting up maintenance scripts..."
cp /home/botuser/discopilot/scripts/deployment/update_bot.sh /usr/local/bin/update-discopilot.sh
cp /home/botuser/discopilot/scripts/deployment/restart_bot.sh /usr/local/bin/restart-discopilot.sh

# Make scripts executable
chmod +x /usr/local/bin/update-discopilot.sh
chmod +x /usr/local/bin/restart-discopilot.sh

# Create convenient aliases
echo 'alias update-bot="sudo /usr/local/bin/update-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias restart-bot="sudo /usr/local/bin/restart-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias bot-logs="sudo journalctl -u discopilot -f"' >> /home/ubuntu/.bashrc
echo 'alias edit-config="sudo nano /home/botuser/.config/discopilot/config.yaml"' >> /home/ubuntu/.bashrc

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/discopilot.service << 'EOF'
[Unit]
Description=DiscoPilot Discord Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/home/botuser/discopilot
ExecStart=/usr/local/bin/run-discopilot.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable the service but don't start it yet
systemctl daemon-reload
systemctl enable discopilot

# Set up security measures
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Set up automatic security updates
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create a README file with instructions
cat > /home/ubuntu/DISCOPILOT_README.txt << 'EOF'
=================================================
DISCOPILOT SETUP INSTRUCTIONS
=================================================

Your DiscoPilot bot has been installed but needs configuration.

1. Edit the configuration file:
   edit-config
   or
   sudo nano /home/botuser/.config/discopilot/config.yaml

2. Replace the placeholder values with your actual credentials:
   - Discord token
   - Discord server ID
   - Admin user ID
   - Twitter API credentials:
     * API key and secret (v1.1)
     * Access token and secret (v1.1)
     * Client ID and secret (OAuth 2.0)

3. Start the service:
   sudo systemctl start discopilot

4. Check the status:
   sudo systemctl status discopilot

5. View logs:
   bot-logs
   or
   sudo journalctl -u discopilot -f

USEFUL COMMANDS:
---------------
edit-config : Edit the bot configuration file
update-bot  : Update the bot from GitHub and restart
restart-bot : Restart the bot without updating
bot-logs    : View the bot's logs in real-time

=================================================
EOF

# Make the README readable
chmod 644 /home/ubuntu/DISCOPILOT_README.txt

# Final verification
echo "Verifying installation..."
echo "Bot user home directory:"
ls -la /home/botuser
echo "Config directory:"
ls -la /home/botuser/.config/discopilot
echo "Systemd service:"
systemctl status discopilot --no-pager

# Print instructions
echo "==================================================="
echo "DiscoPilot installation complete!"
echo "Please follow the instructions in /home/ubuntu/DISCOPILOT_README.txt"
echo "to complete the Discord bot setup."
echo "==================================================="
echo "Setup script completed at $(date)" 