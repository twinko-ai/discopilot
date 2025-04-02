#!/usr/bin/env python3
import os
import subprocess
import sys


def create_systemd_service(username, working_dir):
    """Create a systemd service file for Linux"""
    service_content = f"""[Unit]
Description=DiscoPilot Discord Bot
After=network.target

[Service]
User={username}
WorkingDirectory={working_dir}
ExecStart={sys.executable} -m discopilot.scripts.run_bot
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=discopilot

[Install]
WantedBy=multi-user.target
"""
    return service_content


def create_launchd_plist(username, working_dir):
    """Create a launchd plist file for macOS"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.discopilot</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>discopilot.scripts.run_bot</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>StandardOutPath</key>
    <string>{working_dir}/discopilot.log</string>
    <key>StandardErrorPath</key>
    <string>{working_dir}/discopilot.log</string>
</dict>
</plist>
"""
    return plist_content


def install_service():
    """Install the DiscoPilot service."""
    # Get the current Python executable
    python_path = sys.executable

    # Get the package directory
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create service file content
    service_content = f"""[Unit]
Description=DiscoPilot Discord Bot
After=network.target

[Service]
ExecStart={python_path} -m discopilot.scripts.run_bot
WorkingDirectory={os.path.expanduser('~')}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    # Write service file
    service_path = "/etc/systemd/system/discopilot.service"
    try:
        with open(service_path, "w") as f:
            f.write(service_content)
        print(
            f"Service file created at {service_path}. "
            "You can now start the service with 'sudo systemctl start discopilot'"
        )
    except PermissionError:
        print("Error: You need root privileges to create the service file.")
        print("Try running this script with sudo.")
        return False

    # Reload systemd
    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
    except subprocess.CalledProcessError:
        print(
            "Error reloading systemd. Please run 'sudo systemctl daemon-reload' manually."
        )
        return False

    # Enable service
    try:
        subprocess.run(["systemctl", "enable", "discopilot"], check=True)
        print("Service enabled. It will start automatically on boot.")
    except subprocess.CalledProcessError:
        print(
            "Error enabling service. Please run 'sudo systemctl enable discopilot' manually."
        )
        return False

    # Start service
    try:
        subprocess.run(["systemctl", "start", "discopilot"], check=True)
        print(
            "Service started. " "Check status with 'sudo systemctl status discopilot'"
        )
    except subprocess.CalledProcessError:
        print(
            "Error starting service. Please run 'sudo systemctl start discopilot' manually."
        )
        return False

    # Create aliases
    bashrc_path = os.path.expanduser("~/.bashrc")
    aliases = """
# DiscoPilot aliases
alias discopilot-status="systemctl status discopilot"
alias discopilot-restart="systemctl restart discopilot"
alias discopilot-logs="journalctl -u discopilot -f"
"""

    try:
        with open(bashrc_path, "a") as f:
            f.write(aliases)
        print(
            "Created aliases in ~/.bashrc. "
            "Please restart your shell or run 'source ~/.bashrc' to use them."
        )
    except Exception as e:
        print(f"Error creating aliases: {e}")

    return True


def main():
    """Main function."""
    if os.geteuid() != 0:
        print("This script must be run as root (sudo).")
        sys.exit(1)

    if install_service():
        print("DiscoPilot service installed successfully!")
    else:
        print("Failed to install DiscoPilot service.")
        sys.exit(1)


if __name__ == "__main__":
    main()
