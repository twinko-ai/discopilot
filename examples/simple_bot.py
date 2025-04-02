#!/usr/bin/env python3
"""
A simple example of running the DiscoPilot bot.
"""
import logging

from discopilot.bot.discord_client import HedwigBot
from discopilot.utils.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    # Load configuration
    config = Config()

    # Create and run the bot
    bot = HedwigBot()
    bot.run(config.discord_token)


if __name__ == "__main__":
    main()
