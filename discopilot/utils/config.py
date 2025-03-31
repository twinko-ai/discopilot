import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        # First try user-specified config path
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
        self.discord_token = os.environ.get("DISCORD_TOKEN", self.config.get("discord", {}).get("token"))
        self.twitter_api_key = os.environ.get("TWITTER_API_KEY", self.config.get("twitter", {}).get("api_key"))
        self.twitter_api_secret = os.environ.get("TWITTER_API_SECRET", self.config.get("twitter", {}).get("api_secret"))
        self.twitter_access_token = os.environ.get("TWITTER_ACCESS_TOKEN", self.config.get("twitter", {}).get("access_token"))
        self.twitter_access_secret = os.environ.get("TWITTER_ACCESS_SECRET", self.config.get("twitter", {}).get("access_secret"))
        
        # Add other platform configs as needed
        
        # Reaction configuration
        self.trigger_emoji = os.environ.get("TRIGGER_EMOJI", self.config.get("triggers", {}).get("emoji", "📢"))
        self.admin_ids = [int(id) for id in os.environ.get("ADMIN_IDS", "").split(",") if id] or self.config.get("admin_ids", []) 