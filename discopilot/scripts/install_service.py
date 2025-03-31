#!/usr/bin/env python3
import os
import sys
import argparse
import getpass
import platform

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

def main():
    parser = argparse.ArgumentParser(description="Install DiscoPilot as a system service")
    parser.add_argument("--working-dir", default=os.getcwd(), help="Working directory for the service")
    args = parser.parse_args()
    
    system = platform.system()
    username = getpass.getuser()
    
    if system == "Linux":
        service_path = "/etc/systemd/system/discopilot.service"
        service_content = create_systemd_service(username, args.working_dir)
        
        print(f"To install as a systemd service, run the following commands:")
        print(f"sudo bash -c 'cat > {service_path} << EOL\n{service_content}EOL'")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable discopilot")
        print("sudo systemctl start discopilot")
        print("\nTo check status:")
        print("sudo systemctl status discopilot")
        
    elif system == "Darwin":  # macOS
        plist_path = f"/Users/{username}/Library/LaunchAgents/com.user.discopilot.plist"
        plist_content = create_launchd_plist(username, args.working_dir)
        
        print(f"To install as a launchd service, run the following commands:")
        print(f"cat > {plist_path} << EOL\n{plist_content}EOL")
        print(f"launchctl load {plist_path}")
        print("\nTo check status:")
        print("launchctl list | grep discopilot")
        
    elif system == "Windows":
        print("For Windows, you can use Task Scheduler or NSSM (Non-Sucking Service Manager).")
        print("NSSM installation example:")
        print("1. Download NSSM from https://nssm.cc/")
        print("2. Run: nssm.exe install DiscoPilot")
        print(f"3. Set the path to: {sys.executable}")
        print("4. Set arguments to: -m discopilot.scripts.run_bot")
        print(f"5. Set working directory to: {args.working_dir}")
        
    else:
        print(f"Unsupported operating system: {system}")
        sys.exit(1)

if __name__ == "__main__":
    main() 