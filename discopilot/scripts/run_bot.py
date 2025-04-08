import asyncio
import logging
import sys

from ..bot.discord_client import HedwigBot
from ..publishers import get_publishers
from ..utils.config import Config


def main():
    """Run the Discord bot."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger("discopilot")

    # Load configuration
    try:
        config = Config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Initialize publishers
    publishers = get_publishers(config)

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
        asyncio.run(client.start(config.discord_token))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
