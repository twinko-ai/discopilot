#!/bin/bash

# DiscoPilot Cleanup Script
# This script removes all DiscoPilot-related files, packages, and configurations
# WARNING: This will completely remove the bot and all its data!

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== DiscoPilot Complete Cleanup Script ===${NC}"
echo -e "${RED}WARNING: This will completely remove DiscoPilot and all its data!${NC}"
echo -e "${RED}This action cannot be undone.${NC}"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cleanup cancelled."
    exit 1
fi

# Stop and disable the service
echo -e "\n${YELLOW}Stopping and disabling DiscoPilot service...${NC}"
if systemctl is-active --quiet discopilot; then
    sudo systemctl stop discopilot
    echo -e "${GREEN}Service stopped.${NC}"
else
    echo -e "${YELLOW}Service was not running.${NC}"
fi

if systemctl is-enabled --quiet discopilot 2>/dev/null; then
    sudo systemctl disable discopilot
    echo -e "${GREEN}Service disabled.${NC}"
else
    echo -e "${YELLOW}Service was not enabled.${NC}"
fi

# Remove service file
echo -e "\n${YELLOW}Removing service file...${NC}"
if [ -f /etc/systemd/system/discopilot.service ]; then
    sudo rm /etc/systemd/system/discopilot.service
    sudo systemctl daemon-reload
    echo -e "${GREEN}Service file removed.${NC}"
else
    echo -e "${YELLOW}Service file not found.${NC}"
fi

# Remove scripts from /usr/local/bin
echo -e "\n${YELLOW}Removing scripts from /usr/local/bin...${NC}"
for script in restart-bot update-bot bot-logs update-discopilot-scripts.sh update_discopilot.sh run_discopilot.sh; do
    if [ -f /usr/local/bin/$script ]; then
        sudo rm /usr/local/bin/$script
        echo -e "${GREEN}Removed /usr/local/bin/$script${NC}"
    else
        echo -e "${YELLOW}Script /usr/local/bin/$script not found.${NC}"
    fi
done

# Remove botuser home directory
echo -e "\n${YELLOW}Removing botuser home directory...${NC}"
if [ -d /home/botuser ]; then
    sudo rm -rf /home/botuser
    echo -e "${GREEN}Removed /home/botuser directory.${NC}"
else
    echo -e "${YELLOW}Directory /home/botuser not found.${NC}"
fi

# Remove configuration directory
echo -e "\n${YELLOW}Removing configuration directory...${NC}"
if [ -d /home/botuser/.config/discopilot ]; then
    sudo rm -rf /home/botuser/.config/discopilot
    echo -e "${GREEN}Removed configuration directory.${NC}"
else
    echo -e "${YELLOW}Configuration directory not found.${NC}"
fi

# Remove any DiscoPilot files in ubuntu user's home
echo -e "\n${YELLOW}Checking for DiscoPilot files in ubuntu user's home...${NC}"
if [ -d /home/ubuntu/discopilot ]; then
    sudo rm -rf /home/ubuntu/discopilot
    echo -e "${GREEN}Removed /home/ubuntu/discopilot directory.${NC}"
else
    echo -e "${YELLOW}Directory /home/ubuntu/discopilot not found.${NC}"
fi

# Remove log files
echo -e "\n${YELLOW}Removing log files...${NC}"
sudo rm -f /var/log/discopilot*.log 2>/dev/null
echo -e "${GREEN}Removed log files.${NC}"

# Remove the botuser account
echo -e "\n${YELLOW}Removing botuser account...${NC}"
if id "botuser" &>/dev/null; then
    sudo userdel -r botuser 2>/dev/null
    echo -e "${GREEN}Removed botuser account.${NC}"
else
    echo -e "${YELLOW}User botuser does not exist.${NC}"
fi

# Clean up Python cache files
echo -e "\n${YELLOW}Cleaning up Python cache files...${NC}"
sudo find / -name "__pycache__" -type d -path "*/discopilot*" -exec rm -rf {} + 2>/dev/null || true
sudo find / -name "*.pyc" -path "*/discopilot*" -exec rm -f {} + 2>/dev/null || true
echo -e "${GREEN}Cleaned up Python cache files.${NC}"

# Remove any global pip installations
echo -e "\n${YELLOW}Checking for global pip installations...${NC}"
if pip3 list | grep -q discopilot; then
    sudo pip3 uninstall -y discopilot
    echo -e "${GREEN}Uninstalled global discopilot package.${NC}"
else
    echo -e "${YELLOW}No global discopilot package found.${NC}"
fi

# Remove any uv installations
echo -e "\n${YELLOW}Checking for uv installations...${NC}"
if [ -f /home/ubuntu/.local/bin/uv ]; then
    sudo rm /home/ubuntu/.local/bin/uv
    echo -e "${GREEN}Removed uv from ubuntu user.${NC}"
fi

if [ -f /home/botuser/.local/bin/uv ]; then
    sudo rm /home/botuser/.local/bin/uv
    echo -e "${GREEN}Removed uv from botuser.${NC}"
fi

# Clean up systemd journal logs
echo -e "\n${YELLOW}Cleaning up systemd journal logs for discopilot...${NC}"
sudo journalctl --vacuum-time=1s --unit=discopilot
echo -e "${GREEN}Cleaned up journal logs.${NC}"

echo -e "\n${GREEN}=== DiscoPilot cleanup complete! ===${NC}"
echo -e "${YELLOW}The server has been cleaned of all DiscoPilot-related files and configurations.${NC}"
echo -e "${YELLOW}You may need to reboot the server to ensure all processes are terminated.${NC}"
echo -e "${YELLOW}Recommended: sudo reboot${NC}"