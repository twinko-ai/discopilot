#!/bin/bash

# AWS Lightsail Launch Script for DiscoPilot
# Copy this script into the "Launch Script" section when creating a Lightsail instance

# Enable debugging and logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Function for printing formatted messages
print_step() {
  echo ""
  echo "================================================================"
  echo "STEP: $1"
  echo "================================================================"
}

print_substep() {
  echo ""
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

print_step "Starting DiscoPilot setup script at $(date)"
set -e  # Exit immediately if a command exits with a non-zero status

# Update system packages
print_step "Updating system packages"
apt-get update
apt-get upgrade -y
print_success "System packages updated"

# Install required packages
print_step "Installing required packages"
print_substep "Installing python3-pip, git, python3-venv, curl"
apt-get install -y python3-pip git python3-venv curl
print_success "Required packages installed"

# Create a dedicated user for the bot
print_step "Creating dedicated user for the bot"
useradd -m -s /bin/bash botuser
if [ ! -d "/home/botuser" ]; then
  print_error "Failed to create home directory for botuser"
  mkdir -p /home/botuser
  chown botuser:botuser /home/botuser
  print_warning "Created home directory manually"
else
  print_success "Botuser created successfully"
fi

# Verify botuser home directory
print_substep "Verifying botuser home directory"
if ls -la /home/botuser > /dev/null 2>&1; then
  print_success "Botuser home directory verified"
else
  print_warning "Cannot list botuser home directory"
fi

# Clone or update the repository
print_step "Setting up DiscoPilot repository"
if [ -d "/home/botuser/discopilot" ]; then
  print_substep "Repository already exists, pulling latest changes"
  if su - botuser -c "cd ~/discopilot && git pull"; then
    print_success "Repository updated successfully"
  else
    print_warning "Failed to pull latest changes, continuing with existing code"
  fi
else
  print_substep "Cloning DiscoPilot repository"
  if su - botuser -c "git clone https://github.com/twinko-ai/discopilot.git ~/discopilot"; then
    print_success "Repository cloned successfully"
  else
    print_error "Failed to clone repository"
    exit 1
  fi
fi

# Verify repository exists
if [ ! -d "/home/botuser/discopilot" ]; then
  print_error "Repository directory not found after cloning/updating"
  exit 1
fi

# After cloning or updating the repository, set executable permissions on all scripts
print_step "Setting executable permissions on scripts"
print_substep "Making deployment scripts executable"
if [ -d "/home/botuser/discopilot/scripts/deployment" ]; then
  find /home/botuser/discopilot/scripts/deployment -name "*.sh" -exec chmod +x {} \;
  chown -R botuser:botuser /home/botuser/discopilot/scripts/deployment
  print_success "All deployment scripts are now executable"
else
  print_warning "Deployment scripts directory not found"
fi

# Install uv for package management
print_step "Installing uv for package management"
if su - botuser -c "curl -LsSf https://astral.sh/uv/install.sh | sh"; then
  print_success "uv installed successfully"
else
  print_warning "uv installation may have issues"
fi

print_substep "Adding uv to botuser's PATH"
echo 'export PATH="/home/botuser/.local/bin:$PATH"' >> /home/botuser/.bashrc
su - botuser -c "source ~/.bashrc"
print_success "PATH updated"

# Run the dependency installation script
print_step "Installing dependencies"
print_substep "Running install_dependencies.sh script"
if su - botuser -c "cd ~/discopilot && bash ./scripts/deployment/install_dependencies.sh"; then
  print_success "Dependencies installed successfully"
else
  print_warning "Dependency installation script may have had issues"
fi

# Create config directory with multiple methods to ensure success
print_step "Setting up configuration"
print_substep "Creating config directory"
if su - botuser -c "mkdir -p ~/.config/discopilot"; then
  print_success "Config directory created by botuser"
else
  print_warning "Failed to create config directory as botuser, trying as root"
  mkdir -p /home/botuser/.config/discopilot
  chown -R botuser:botuser /home/botuser/.config
  print_success "Config directory created by root and ownership transferred"
fi

# Verify config directory exists and has correct permissions
print_substep "Setting permissions on config directory"
if ls -la /home/botuser/.config > /dev/null 2>&1; then
  chmod 700 /home/botuser/.config/discopilot
  chown -R botuser:botuser /home/botuser/.config
  print_success "Config directory permissions set"
else
  print_warning "Cannot list .config directory"
fi

# Check if config file already exists
print_substep "Checking for existing config file"
if [ -f "/home/botuser/.config/discopilot/config.yaml" ]; then
  print_success "Config file already exists, keeping existing configuration"
else
  # Create a template config file with Twitter OAuth 2.0 support
  print_substep "Creating config file template"
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

  # Copy the config file to the correct location and ensure proper ownership
  print_substep "Installing config file as botuser"
  if su - botuser -c "cat > ~/.config/discopilot/config.yaml" < /tmp/discopilot_config.yaml; then
    print_success "Config file created as botuser"
  else
    print_warning "Failed to create config file as botuser, trying as root"
    cp /tmp/discopilot_config.yaml /home/botuser/.config/discopilot/config.yaml
    print_success "Config file copied by root"
  fi
  rm /tmp/discopilot_config.yaml
fi

# Set proper ownership and permissions for the config file
print_substep "Setting permissions on config file"
chmod 600 /home/botuser/.config/discopilot/config.yaml
chown botuser:botuser /home/botuser/.config/discopilot/config.yaml
print_success "Config file permissions set"

# Verify config file exists and has correct ownership
if [ ! -f "/home/botuser/.config/discopilot/config.yaml" ]; then
  print_error "Failed to create config file"
  exit 1
else
  print_success "Config file verified"
fi

# Show the config file ownership
print_substep "Checking config file ownership"
ls -la /home/botuser/.config/discopilot/config.yaml
print_success "Config file ownership verified"

# Check if run script exists in the repository
print_step "Setting up service scripts"
print_substep "Checking for run script in repository"
if [ -f "/home/botuser/discopilot/scripts/deployment/run_discopilot.sh" ]; then
  print_success "Run script found in repository"
else
  print_warning "Run script not found in repository, creating it"
  # Create the directory if it doesn't exist
  mkdir -p /home/botuser/discopilot/scripts/deployment
  
  # Create the run script
  cat > /home/botuser/discopilot/scripts/deployment/run_discopilot.sh << 'RUNSCRIPTEOF'
#!/bin/bash

# Log file
LOG_FILE="/home/botuser/discopilot_wrapper.log"

# Log function
log() {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Start logging
log "Starting DiscoPilot bot using virtual environment"
log "Current directory: $(pwd)"
log "User: $(whoami)"

# Change to the discopilot directory
cd /home/botuser/discopilot
log "Changed directory to: $(pwd)"

# Use the correct path to uv
UV_PATH="/home/botuser/.local/bin/uv"

# Ensure the virtual environment exists
if [ ! -d ".venv" ]; then
    log "Virtual environment not found, creating it..."
    "$UV_PATH" venv
    log "Installing dependencies..."
    "$UV_PATH" pip install -e .
fi

# Run the bot using the virtual environment
log "Running bot with: ./.venv/bin/python -m discopilot.scripts.run_bot"
./.venv/bin/python -m discopilot.scripts.run_bot 2>> "$LOG_FILE"

# Log exit
log "Script exited with code: $?"
RUNSCRIPTEOF

  # Set proper permissions
  chmod +x /home/botuser/discopilot/scripts/deployment/run_discopilot.sh
  chown botuser:botuser /home/botuser/discopilot/scripts/deployment/run_discopilot.sh
  print_success "Run script created"
fi

# Copy the run script to a system location for the service
print_substep "Installing run script to system location"
cp /home/botuser/discopilot/scripts/deployment/run_discopilot.sh /usr/local/bin/run-discopilot.sh
chmod +x /usr/local/bin/run-discopilot.sh
print_success "Run script installed"

# Check for maintenance scripts and create if needed
print_substep "Checking for maintenance scripts"
if [ ! -f "/home/botuser/discopilot/scripts/deployment/update_bot.sh" ]; then
  print_warning "Update script not found, creating it"
  cat > /home/botuser/discopilot/scripts/deployment/update_bot.sh << 'UPDATESCRIPTEOF'
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
if su - botuser -c "cd ~/discopilot && /home/botuser/.local/bin/uv pip install -e ."; then
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
UPDATESCRIPTEOF
  chmod +x /home/botuser/discopilot/scripts/deployment/update_bot.sh
  chown botuser:botuser /home/botuser/discopilot/scripts/deployment/update_bot.sh
  print_success "Update script created"
fi

if [ ! -f "/home/botuser/discopilot/scripts/deployment/restart_bot.sh" ]; then
  print_warning "Restart script not found, creating it"
  cat > /home/botuser/discopilot/scripts/deployment/restart_bot.sh << 'RESTARTSCRIPTEOF'
#!/bin/bash

# Script to restart the DiscoPilot service
# Usage: sudo ./restart-discopilot.sh

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "=== DiscoPilot Restart Script ==="

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
echo "=== Restart Complete ==="
RESTARTSCRIPTEOF
  chmod +x /home/botuser/discopilot/scripts/deployment/restart_bot.sh
  chown botuser:botuser /home/botuser/discopilot/scripts/deployment/restart_bot.sh
  print_success "Restart script created"
fi

# Copy maintenance scripts from the repository to system location
print_substep "Installing maintenance scripts to system location"
cp /home/botuser/discopilot/scripts/deployment/update_bot.sh /usr/local/bin/update-discopilot.sh
cp /home/botuser/discopilot/scripts/deployment/restart_bot.sh /usr/local/bin/restart-discopilot.sh
print_success "Maintenance scripts copied"

# Make scripts executable
chmod +x /usr/local/bin/update-discopilot.sh
chmod +x /usr/local/bin/restart-discopilot.sh
print_success "Scripts made executable"

# Create convenient aliases
print_substep "Creating convenient aliases"
echo 'alias update-bot="sudo /usr/local/bin/update-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias restart-bot="sudo /usr/local/bin/restart-discopilot.sh"' >> /home/ubuntu/.bashrc
echo 'alias bot-logs="sudo journalctl -u discopilot -f"' >> /home/ubuntu/.bashrc
echo 'alias edit-config="sudo nano /home/botuser/.config/discopilot/config.yaml"' >> /home/ubuntu/.bashrc
print_success "Aliases created"

# Create systemd service file
print_step "Setting up systemd service"
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
print_success "Service file created"

# Enable the service but don't start it yet
print_substep "Enabling service"
systemctl daemon-reload
systemctl enable discopilot
print_success "Service enabled (but not started yet)"

# Set up security measures
print_step "Setting up security measures"
print_substep "Installing fail2ban"
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
print_success "fail2ban installed and started"

# Set up automatic security updates
print_substep "Setting up automatic security updates"
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
print_success "Automatic security updates configured"

# Create a README file with instructions
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
print_success "README file created"

# Make the README readable
chmod 644 /home/ubuntu/DISCOPILOT_README.txt

# Final verification
print_step "Performing final verification"
print_substep "Checking bot user home directory"
ls -la /home/botuser
print_substep "Checking config directory"
ls -la /home/botuser/.config/discopilot
print_substep "Checking run script"
ls -la /usr/local/bin/run-discopilot.sh
print_substep "Checking systemd service"
systemctl status discopilot --no-pager

# Print instructions
print_step "INSTALLATION COMPLETE!"
echo "==================================================="
echo "DiscoPilot installation complete!"
echo "Please follow the instructions in /home/ubuntu/DISCOPILOT_README.txt"
echo "to complete the Discord bot setup."
echo "==================================================="
echo "Setup script completed at $(date)" 