import asyncio
import logging
import sys
import argparse

from ..bot.discord_client import HedwigBot
from ..publishers import get_publishers
from ..utils.config import Config


def main():
    """Run the Discord bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the DiscoPilot Discord bot")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )
    
    # Set discord.py logger to DEBUG
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.DEBUG if log_level == logging.DEBUG else logging.INFO)
    
    logger = logging.getLogger("discopilot")
    logger.info(f"Logging level set to {args.log_level}")

    # Load configuration
    try:
        config = Config()
        logger.info(f"Config loaded with trigger emoji: '{config.trigger_emoji}'")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Initialize publishers
    publishers = get_publishers(config)
    logger.info(f"Initialized publishers: {list(publishers.keys())}")

    # Initialize the Discord client
    client = HedwigBot(
        token=config.discord_token,
        server_ids=config.server_ids,
        admin_ids=config.admin_ids,
        trigger_emoji=config.trigger_emoji,
    )
    
    # Add publishers after initialization
    for name, publisher in publishers.items():
        client.add_publisher(name, publisher)

    # Run the client
    try:
        logger.info("Starting Discord client...")
        asyncio.run(client.start(config.discord_token))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
