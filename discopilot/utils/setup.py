import os
import shutil

import pkg_resources


def setup_config():
    """
    Set up a new configuration file for the user.

    This function copies the example configuration to the user's
    config directory and prompts them to edit it.
    """
    # Determine the user's config directory
    user_config_dir = os.path.expanduser("~/.config/discopilot")
    user_config_path = os.path.join(user_config_dir, "config.yaml")

    # Create the directory if it doesn't exist
    os.makedirs(user_config_dir, exist_ok=True)

    # Check if config already exists
    if os.path.exists(user_config_path):
        print(f"Configuration file already exists at {user_config_path}")
        return user_config_path

    # Get the example config from the package
    example_config = pkg_resources.resource_filename(
        "discopilot", "examples/config.example.yaml"
    )

    # Copy the example config to the user's directory
    shutil.copy(example_config, user_config_path)

    print(f"Configuration file created at {user_config_path}")
    print("Please edit this file with your Discord token and other settings.")

    return user_config_path
