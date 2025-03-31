from abc import ABC, abstractmethod
import logging

class BasePublisher(ABC):
    """Base class for all social media publishers"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(f"discopilot.publishers.{self.__class__.__name__}")
    
    @abstractmethod
    async def publish(self, content, media=None):
        """
        Publish content to the platform
        
        Args:
            content (str): The text content to publish
            media (list, optional): List of media URLs or file paths
            
        Returns:
            dict: Result of the publishing operation
        """
        pass
    
    @abstractmethod
    async def check_rate_limit(self):
        """
        Check if the publisher is rate limited
        
        Returns:
            bool: True if rate limited, False otherwise
        """
        pass 