#!/bin/bash

# AWS Lightsail Launch Script for DiscoPilot
# This script can be used either as a launch script or standalone

# Function for printing formatted messages
print_step() {
  echo "================================================================"
  echo "STEP: $1"
  echo "================================================================"
}

print_substep() {
  echo ">> $1"
}

print_success() {
  echo "✅ $1"
}

print_warning() {
  echo "⚠️ $1"
}

print_error() {
  echo "❌ $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  print_error "Please run as root (use sudo)"
  exit 1
fi

print_step "Starting DiscoPilot setup script"

# Update system packages
print_step "Updating system packages"
apt-get update
apt-get upgrade -y
print_success "System packages updated"

# Install required packages
print_step "Installing required packages"
apt-get install -y python3-pip git python3-venv curl
print_success "Required packages installed"

# Create a dedicated user for the bot
print_step "Creating dedicated user for the bot"
if ! id botuser &>/dev/null; then
  useradd -m -s /bin/bash botuser
  print_success "Botuser created"
else
  print_success "Botuser already exists"
fi

# Ensure home directory exists
mkdir -p /home/botuser
chown botuser:botuser /home/botuser
chmod 755 /home/botuser

# Clone the repository
print_step "Setting up repository"
if [ ! -d "/home/botuser/discopilot" ]; then
  print_substep "Cloning repository"
  sudo -u botuser git clone https://github.com/twinko-ai/discopilot.git /home/botuser/discopilot
  if [ $? -ne 0 ]; then
    print_error "Failed to clone repository"
    exit 1
  fi
  print_success "Repository cloned"
else
  print_substep "Updating repository"
  cd /home/botuser/discopilot && sudo -u botuser git pull
  print_success "Repository updated"
fi

# Make scripts executable
print_step "Setting up scripts"
find /home/botuser/discopilot/scripts/deployment -name "*.sh" -exec chmod +x {} \;

# Copy scripts to /usr/local/bin
mkdir -p /usr/local/bin

# Create a script to update the scripts in /usr/local/bin
cat > /usr/local/bin/update-discopilot-scripts.sh << 'EOF'
#!/bin/bash

# Script to update the DiscoPilot scripts in /usr/local/bin
echo "Updating DiscoPilot scripts in /usr/local/bin..."

# Copy run script
if [ -f "/home/botuser/discopilot/scripts/deployment/run_discopilot.sh" ]; then
  cp /home/botuser/discopilot/scripts/deployment/run_discopilot.sh /usr/local/bin/run_discopilot.sh
  chmod +x /usr/local/bin/run_discopilot.sh
  echo "✅ Updated run_discopilot.sh"
else
  echo "⚠️ run_discopilot.sh not found in repository"
fi

# Copy update script
if [ -f "/home/botuser/discopilot/scripts/deployment/update_discopilot.sh" ]; then
  cp /home/botuser/discopilot/scripts/deployment/update_discopilot.sh /usr/local/bin/update_discopilot.sh
  chmod +x /usr/local/bin/update_discopilot.sh
  echo "✅ Updated update_discopilot.sh"
else
  echo "⚠️ update_discopilot.sh not found in repository"
fi

# Copy restart script
if [ -f "/home/botuser/discopilot/scripts/deployment/restart_discopilot.sh" ]; then
  cp /home/botuser/discopilot/scripts/deployment/restart_discopilot.sh /usr/local/bin/restart_discopilot.sh
  chmod +x /usr/local/bin/restart_discopilot.sh
  echo "✅ Updated restart_discopilot.sh"
else
  echo "⚠️ restart_discopilot.sh not found in repository"
fi

echo "Scripts update complete"
EOF
chmod +x /usr/local/bin/update-discopilot-scripts.sh

# Run the script to copy the scripts
/usr/local/bin/update-discopilot-scripts.sh

print_success "Scripts installed"

# Install uv
print_step "Installing uv"
sudo -u botuser curl -LsSf https://astral.sh/uv/install.sh | sudo -u botuser sh
print_success "uv installed"

# Create config directory
print_step "Setting up configuration"
mkdir -p /home/botuser/.config/discopilot
chown -R botuser:botuser /home/botuser/.config
chmod 700 /home/botuser/.config/discopilot

# Create config file if it doesn't exist
if [ ! -f "/home/botuser/.config/discopilot/config.yaml" ]; then
  cat > /home/botuser/.config/discopilot/config.yaml << 'EOF'
# DiscoPilot Configuration

discord:
  token: "REPLACE_WITH_YOUR_DISCORD_TOKEN"
  server_ids:
    - 0000000000000000  # Replace with your Discord server ID

admin_ids:
  - 0000000000000000  # Replace with your Discord user ID

triggers:
  emoji: "📢"  # The emoji that triggers publishing
EOF
  chmod 600 /home/botuser/.config/discopilot/config.yaml
  chown botuser:botuser /home/botuser/.config/discopilot/config.yaml
  print_success "Config file created"
else
  print_success "Config file already exists"
fi

# Create systemd service
print_step "Setting up systemd service"
cat > /etc/systemd/system/discopilot.service << 'EOF'
[Unit]
Description=DiscoPilot Discord Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/home/botuser/discopilot
ExecStart=/usr/local/bin/run_discopilot.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable service
systemctl daemon-reload
systemctl enable discopilot
print_success "Service enabled"

# Create aliases
print_step "Creating aliases"
echo 'alias update-bot="sudo /usr/local/bin/update_discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias restart-bot="sudo /usr/local/bin/restart_discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias bot-logs="sudo journalctl -u discopilot -f"' >> /home/ubuntu/.bashrc
echo 'alias edit-config="sudo nano /home/botuser/.config/discopilot/config.yaml"' >> /home/ubuntu/.bashrc
print_success "Aliases created"

# Create README
print_step "Creating documentation"
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
chmod 644 /home/ubuntu/DISCOPILOT_README.txt
print_success "README created"

# Final verification
print_step "Performing final verification"
ls -la /home/botuser
ls -la /usr/local/bin/run_discopilot.sh
ls -la /etc/systemd/system/discopilot.service

print_step "INSTALLATION COMPLETE!"
echo "Please follow the instructions in /home/ubuntu/DISCOPILOT_README.txt"
echo "to complete the Discord bot setup." 