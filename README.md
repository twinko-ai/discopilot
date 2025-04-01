# discopilot

A Discord bot that monitors channels and publishes content to social media platforms.

## Features

- 🤖 Monitor Discord channels for specific emoji reactions
- 📢 Publish messages to Twitter (X) and other social media platforms
- 🔄 Smart rate limiting to prevent API throttling
- 🧙‍♂️ Named after Hedwig from Harry Potter - your magical messenger

## Installation

### From PyPI

```
pip install discopilot
```

### From Source

```
git clone https://github.com/yourusername/discopilot.git
cd discopilot
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Configuration

DiscoPilot requires a configuration file to run. You can set up your configuration in one of these ways:

1. **Automatic setup**:
   ```
   discopilot-setup
   ```
   This will create a configuration file at `~/.config/discopilot/config.yaml`.

2. **Manual setup**:
   - Copy the example configuration from `examples/config.example.yaml`
   - Place it in one of these locations:
     - The current working directory as `config.yaml`
     - Your home directory at `~/.config/discopilot/config.yaml`
   - Edit the file with your Discord token and other settings

3. **Environment variable**:
   - Set the `DISCOPILOT_CONFIG` environment variable to the path of your config file
   ```
   export DISCOPILOT_CONFIG=/path/to/your/config.yaml
   ```

### Configuration Options

| Option | Description | Required |
|--------|-------------|----------|
| `discord.token` | Your Discord bot token | Yes |
| `discord.server_ids` | List of server IDs the bot should listen to (empty = all servers) | No |
| `admin_ids` | List of Discord user IDs that can trigger publishing | Yes |
| `triggers.emoji` | The emoji that triggers publishing | No (default: 📢) |
| `twitter.api_key` | Twitter API key | Yes (for Twitter) |
| `twitter.api_secret` | Twitter API secret | Yes (for Twitter) |
| `twitter.access_token` | Twitter access token | Yes (for Twitter) |
| `twitter.access_secret` | Twitter access token secret | Yes (for Twitter) |
| `twitter.bearer_token` | Twitter bearer token | Yes (for Twitter) |

## Usage

1. **Invite your bot** to your Discord server using the OAuth2 URL from the Discord Developer Portal.

2. **Send a message** in any channel where the bot has access.

3. **React to the message** with the configured emoji (default: 📢). Note: Only users listed in `admin_ids` can trigger publishing.

4. **The bot will publish** the message to configured social media platforms and reply with the results.

## Running on a Server (24/7)

### Using Systemd (Linux)

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/discopilot.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=DiscoPilot Discord Bot
   After=network.target

   [Service]
   User=yourusername
   WorkingDirectory=/path/to/working/directory
   ExecStart=/path/to/python -m discopilot.scripts.run_bot
   Restart=always
   RestartSec=10
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=discopilot

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable discopilot
   sudo systemctl start discopilot
   ```

### Using Docker

1. Create a Dockerfile:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY . .
   RUN pip install -e .
   
   CMD ["python", "-m", "discopilot.scripts.run_bot"]
   ```

2. Build and run:
   ```bash
   docker build -t discopilot .
   docker run -d --name discopilot --restart unless-stopped \
     -v /path/to/config.yaml:/root/.config/discopilot/config.yaml discopilot
   ```

## Extending

### Adding New Social Media Platforms

1. Create a new publisher class in `discopilot/publishers/`
2. Implement the `publish()` and `check_rate_limit()` methods
3. Add your publisher to the bot's `setup_publishers()` method

## Development

### Running Tests

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=discopilot
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.


