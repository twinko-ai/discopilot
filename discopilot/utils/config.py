import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file. If None, will try to find it.

    Returns:
        Dict: Configuration dictionary

    Raises:
        FileNotFoundError: If no configuration file is found
        yaml.YAMLError: If the configuration file is invalid
    """
    # If config_path is provided, use it
    if config_path:
        logger.info(f"Loading configuration from specified path: {config_path}")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    # Check environment variable
    if "DISCOPILOT_CONFIG" in os.environ:
        env_path = os.environ["DISCOPILOT_CONFIG"]
        logger.info(
            f"Loading configuration from environment variable DISCOPILOT_CONFIG: "
            f"{env_path}"
        )
        with open(env_path, "r") as f:
            return yaml.safe_load(f)

    # Check common locations
    config_paths = [
        Path.cwd() / "config.yaml",
        Path.home() / ".config" / "discopilot" / "config.yaml",
    ]

    logger.info(
        f"Checking for configuration file in current directory and user config directory: "
        f"{[str(p) for p in config_paths]}"
    )

    for path in config_paths:
        if path.exists():
            logger.info(f"Found configuration file at {path}")
            with open(path, "r") as f:
                return yaml.safe_load(f)

    # No configuration file found
    logger.error("No configuration file found")
    raise FileNotFoundError(
        "No configuration file found. Please create a config.yaml file or "
        "set the DISCOPILOT_CONFIG environment variable."
    )


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def __init__(self, config_path=None):
        self.config = {}
        self._load_config(config_path)
        self._process_config()

    def _load_config(self, config_path=None):
        # First try user-specified config path
        if config_path:
            config_path = config_path
        else:
            config_path = os.environ.get("DISCOPILOT_CONFIG")

        # If not specified, look in standard locations
        if not config_path or not os.path.exists(config_path):
            # Check current directory
            if os.path.exists("config.yaml"):
                config_path = "config.yaml"
            # Check user's config directory
            else:
                user_config_dir = os.path.expanduser("~/.config/discopilot")
                user_config_path = os.path.join(user_config_dir, "config.yaml")
                if os.path.exists(user_config_path):
                    config_path = user_config_path
                else:
                    # No config found, raise an error with helpful message
                    raise FileNotFoundError(
                        "No configuration file found. Please create a config.yaml file based on the example "
                        "in the examples directory, or set the DISCOPILOT_CONFIG environment variable."
                    )

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Override with environment variables
        self.discord_token = os.environ.get(
            "DISCORD_TOKEN", self.config.get("discord", {}).get("token")
        )
        self.twitter_api_key = os.environ.get(
            "TWITTER_API_KEY", self.config.get("twitter", {}).get("api_key")
        )
        self.twitter_api_secret = os.environ.get(
            "TWITTER_API_SECRET", self.config.get("twitter", {}).get("api_secret")
        )
        self.twitter_access_token = os.environ.get(
            "TWITTER_ACCESS_TOKEN", self.config.get("twitter", {}).get("access_token")
        )
        self.twitter_access_secret = os.environ.get(
            "TWITTER_ACCESS_SECRET", self.config.get("twitter", {}).get("access_secret")
        )
        self.twitter_bearer_token = os.environ.get(
            "TWITTER_BEARER_TOKEN", self.config.get("twitter", {}).get("bearer_token")
        )

        # Add other platform configs as needed

        # Reaction configuration
        self._trigger_emoji = os.environ.get(
            "TRIGGER_EMOJI", self.config.get("triggers", {}).get("emoji", "📢")
        )
        self.admin_ids = [
            int(id) for id in os.environ.get("ADMIN_IDS", "").split(",") if id
        ] or self.config.get("admin_ids", [])

        # Discord configuration from environment variables
        self.discord_token = os.environ.get("DISCORD_TOKEN", self.discord_token)

        # Server IDs from environment variables
        server_ids_env = os.environ.get("SERVER_IDS", "")
        if server_ids_env:
            self.server_ids = [int(id) for id in server_ids_env.split(",") if id]

        # Admin IDs from environment variables
        admin_ids_env = os.environ.get("ADMIN_IDS", "")
        if admin_ids_env:
            self.admin_ids = [int(id) for id in admin_ids_env.split(",") if id]

        # Trigger emoji from environment variables
        self._trigger_emoji = os.environ.get("TRIGGER_EMOJI", self._trigger_emoji)

        # Twitter configuration from environment variables
        self.twitter_api_key = os.environ.get("TWITTER_API_KEY", self.twitter_api_key)
        self.twitter_api_secret = os.environ.get(
            "TWITTER_API_SECRET", self.twitter_api_secret
        )
        self.twitter_access_token = os.environ.get(
            "TWITTER_ACCESS_TOKEN", self.twitter_access_token
        )
        self.twitter_access_secret = os.environ.get(
            "TWITTER_ACCESS_SECRET", self.twitter_access_secret
        )
        self.twitter_bearer_token = os.environ.get(
            "TWITTER_BEARER_TOKEN", self.twitter_bearer_token
        )

        # New OAuth 2.0 credentials
        self.twitter_client_id = self.config.get("twitter", {}).get("client_id")
        self.twitter_client_secret = self.config.get("twitter", {}).get("client_secret")
        self.twitter_oauth2_refresh_token = self.config.get("twitter", {}).get(
            "oauth2_refresh_token"
        )
        self.twitter_oauth2_access_token = self.config.get("twitter", {}).get(
            "oauth2_access_token"
        )

        # ... other configurations ...

    def _process_config(self):
        """Process the loaded configuration and set attributes."""
        # Discord configuration
        discord_config = self.config.get("discord", {})
        self.discord_token = discord_config.get("token")

        # Server IDs - support both new and old format for backward compatibility
        self.server_ids = discord_config.get("servers", []) or discord_config.get(
            "server_ids", []
        )

        # Admin IDs - support both new and old format for backward compatibility
        self.admin_ids = discord_config.get("admins", []) or self.config.get(
            "admin_ids", []
        )

        # Trigger configuration - support both new and old format
        self._trigger_emoji = discord_config.get("triggers", {}).get(
            "emoji"
        ) or self.config.get("triggers", {}).get("emoji", "📢")

        # Notification settings
        self._send_notifications = discord_config.get("send_notifications", False)

        # Twitter configuration
        twitter_config = self.config.get("twitter", {})
        self.twitter_api_key = twitter_config.get("api_key")
        self.twitter_api_secret = twitter_config.get("api_secret")
        self.twitter_access_token = twitter_config.get("access_token")
        self.twitter_access_secret = twitter_config.get("access_secret")
        self.twitter_bearer_token = twitter_config.get("bearer_token")

        # New OAuth 2.0 credentials
        self.twitter_client_id = twitter_config.get("client_id")
        self.twitter_client_secret = twitter_config.get("client_secret")
        self.twitter_oauth2_refresh_token = twitter_config.get("oauth2_refresh_token")
        self.twitter_oauth2_access_token = twitter_config.get("oauth2_access_token")

        # ... other configurations ...

    @property
    def is_server_restricted(self):
        """Check if the bot is restricted to specific servers."""
        return len(self.server_ids) > 0

    def get(self, key, default=None):
        """Get a configuration value with a default fallback.

        Args:
            key: The configuration key to look up
            default: The default value to return if the key is not found

        Returns:
            The configuration value or the default
        """
        if hasattr(self, key):
            return getattr(self, key)
        return default

    @property
    def trigger_emoji(self) -> str:
        """Get the trigger emoji."""
        return self._trigger_emoji

    @property
    def allowed_channel_ids(self) -> List[int]:
        """Get the list of allowed channel IDs."""
        channels = self.config.get("discord", {}).get("allowed_channels", [])
        if not channels:
            return []  # Empty list means all channels are allowed

        # Convert string IDs to integers
        return [int(channel_id) for channel_id in channels]

    @property
    def send_notifications(self) -> bool:
        """Get whether to send notifications about publishing."""
        return self._send_notifications
