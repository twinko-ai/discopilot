# discopilot

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
| `admin_ids` | List of Discord user IDs that can trigger publishing | Yes |
| `triggers.emoji` | The emoji that triggers publishing | No (default: 📢) |
| ... | ... | ... |
