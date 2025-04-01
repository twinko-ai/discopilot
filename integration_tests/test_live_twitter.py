#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from discopilot.publishers.twitter_publisher import TwitterPublisher
from discopilot.utils.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration-test")

async def test_twitter_publisher():
    """Test the Twitter publisher with real API credentials"""
    config = Config()
    publisher = TwitterPublisher(config)
    
    # Test rate limit check
    rate_limit_status = await publisher.check_rate_limit()
    logger.info(f"Twitter rate limit status: {'OK' if rate_limit_status else 'Limited'}")
    
    # Test publishing a simple message
    test_message = "This is an integration test message from DiscoPilot 🤖 #testing"
    logger.info(f"Attempting to publish: {test_message}")
    
    result = await publisher.publish(test_message)
    logger.info(f"Publish result: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_twitter_publisher()) 