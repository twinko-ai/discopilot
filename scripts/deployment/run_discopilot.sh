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
exec ./.venv/bin/python -m discopilot.scripts.run_bot 2>> "$LOG_FILE"

# This line will never be reached because exec replaces the current process
# log "Script exited with code: $?"