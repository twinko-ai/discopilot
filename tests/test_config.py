import tempfile

import yaml

from discopilot.utils.config import load_config


def test_load_config_from_file():
    """Test loading config from a file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as temp:
        config_data = {
            "discord": {"token": "test_token", "server_ids": [123456789]},
            "admin_ids": [987654321],
            "triggers": {"emoji": "📢"},
        }
        yaml.dump(config_data, temp)
        temp.flush()

        config = load_config(config_path=temp.name)

        assert config["discord"]["token"] == "test_token"
        assert config["discord"]["server_ids"] == [123456789]
        assert config["admin_ids"] == [987654321]
        assert config["triggers"]["emoji"] == "📢"


def test_load_config_from_env_var(monkeypatch):
    """Test loading config from environment variable."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as temp:
        config_data = {
            "discord": {"token": "env_token", "server_ids": [123456789]},
            "admin_ids": [987654321],
        }
        yaml.dump(config_data, temp)
        temp.flush()

        monkeypatch.setenv("DISCOPILOT_CONFIG", temp.name)

        config = load_config()

        assert config["discord"]["token"] == "env_token"
        assert config["discord"]["server_ids"] == [123456789]
        assert config["admin_ids"] == [987654321]
