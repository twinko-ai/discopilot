import os
import tempfile
from pathlib import Path

import pytest
import yaml

from discopilot.utils.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        config_data = {
            "discord": {
                "token": "test_token",
                "servers": [123456789],
                "admins": [987654321],
                "allowed_channels": [123456789],
                "triggers": {"emoji": "📢"},
                "send_notifications": False,
            },
            "twitter": {
                "api_key": "test_api_key",
                "api_secret": "test_api_secret",
                "access_token": "test_access_token",
                "access_secret": "test_access_secret",
                "bearer_token": "test_bearer_token",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        }
        yaml.dump(config_data, temp)
        config_path = temp.name

    # Set environment variable to point to this config
    old_env = os.environ.get("DISCOPILOT_CONFIG")
    os.environ["DISCOPILOT_CONFIG"] = config_path

    # Reset the Config singleton
    Config._instance = None

    # Return the config instance
    yield Config()

    # Clean up
    if old_env:
        os.environ["DISCOPILOT_CONFIG"] = old_env
    else:
        del os.environ["DISCOPILOT_CONFIG"]

    # Delete the temporary file
    Path(config_path).unlink(missing_ok=True)

    # Reset the Config singleton again
    Config._instance = None
