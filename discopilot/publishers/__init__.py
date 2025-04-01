"""
Publishers module for DiscoPilot.
Contains classes for publishing content to various social media platforms.
"""

from .base_publisher import BasePublisher
from .twitter_publisher import TwitterPublisher

def get_publishers(config):
    """
    Initialize and return all configured publishers.
    
    Args:
        config: The application configuration
        
    Returns:
        dict: A dictionary of publisher instances
    """
    publishers = {}
    
    # Initialize Twitter publisher if configured
    if hasattr(config, 'twitter_api_key') and config.twitter_api_key:
        publishers['twitter'] = TwitterPublisher(config)
    
    # Add other publishers here as needed
    
    return publishers

__all__ = ["BasePublisher", "TwitterPublisher", "get_publishers"]
