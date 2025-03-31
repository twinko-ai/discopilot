import asyncio
import logging
import sys
from ..bot.discord_client import HedwigBot
from ..utils.config import Config

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('discopilot.log')
        ]
    )

def main():
    """Main entry point for the bot"""
    setup_logging()
    logger = logging.getLogger("discopilot")
    
    try:
        # Load configuration
        config = Config()
        
        # Create and run the bot
        bot = HedwigBot()
        
        logger.info("Starting Hedwig bot...")
        bot.run(config.discord_token)
    except Exception as e:
        logger.exception(f"Error running bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
