#!/bin/bash

# AWS Lightsail Launch Script for DiscoPilot
# Copy this script into the "Launch Script" section when creating a Lightsail instance

# Update system packages
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y python3-pip git python3-venv curl

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Create a dedicated user for the bot
useradd -m -s /bin/bash botuser

# Add Poetry to PATH for all users
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/home/botuser/.local/bin:$PATH"' >> /home/botuser/.bashrc
source /root/.bashrc

# Clone the public repository
su - botuser -c "git clone https://github.com/twinko-ai/discopilot.git ~/discopilot"

# Install dependencies with Poetry
cd /home/botuser/discopilot
su - botuser -c "cd ~/discopilot && ~/.local/bin/poetry install"

# Create config directory
mkdir -p /home/botuser/.config/discopilot
chown -R botuser:botuser /home/botuser/.config
chmod 700 /home/botuser/.config/discopilot

# Create a template config file
cat > /home/botuser/.config/discopilot/config.yaml << 'CONFIGEOF'
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
  api_key: "REPLACE_WITH_YOUR_TWITTER_API_KEY"
  api_secret: "REPLACE_WITH_YOUR_TWITTER_API_SECRET"
  access_token: "REPLACE_WITH_YOUR_TWITTER_ACCESS_TOKEN"
  access_secret: "REPLACE_WITH_YOUR_TWITTER_ACCESS_SECRET"
CONFIGEOF

# Set proper ownership and permissions for the config file
chown botuser:botuser /home/botuser/.config/discopilot/config.yaml
chmod 600 /home/botuser/.config/discopilot/config.yaml

# Copy maintenance scripts from the repository to system location
cp /home/botuser/discopilot/scripts/deployment/update_bot.sh /usr/local/bin/update-discopilot.sh
cp /home/botuser/discopilot/scripts/deployment/restart_bot.sh /usr/local/bin/restart-discopilot.sh
chmod +x /usr/local/bin/update-discopilot.sh
chmod +x /usr/local/bin/restart-discopilot.sh

# Create convenient aliases
echo 'alias update-bot="sudo /usr/local/bin/update-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias restart-bot="sudo /usr/local/bin/restart-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias bot-logs="sudo journalctl -u discopilot -f"' >> /home/ubuntu/.bashrc

# Create systemd service file
cat > /etc/systemd/system/discopilot.service << 'EOF'
[Unit]
Description=DiscoPilot Discord Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/home/botuser/discopilot
ExecStart=/home/botuser/.local/bin/poetry run python -m discopilot
Restart=always
RestartSec=10

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

# Print instructions
echo "==================================================="
echo "Instance setup complete!"
echo "Please SSH into your instance and configure your bot."
echo "===================================================" 