import tweepy
import asyncio
import time
import logging
from .base_publisher import BasePublisher
from ..utils.rate_limiter import RateLimiter
import discord
import re

class TwitterPublisher(BasePublisher):
    def __init__(self, config):
        """Initialize the Twitter publisher."""
        super().__init__(config)
        self.logger = logging.getLogger("discopilot")
        
        # Initialize the Twitter client using v2 API with OAuth 1.0a credentials
        try:
            self.client = tweepy.Client(
                consumer_key=self.config.twitter_api_key,
                consumer_secret=self.config.twitter_api_secret,
                access_token=self.config.twitter_access_token,
                access_token_secret=self.config.twitter_access_secret
            )
            
            # Test the connection
            me = self.client.get_me()
            self.logger.info(f"Twitter publisher initialized for @{me.data.username}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter publisher: {e}")
            self.client = None
        
        # Initialize rate limiter - Twitter allows 300 tweets per 3 hours (180 minutes)
        self.rate_limiter = RateLimiter(300, 180 * 60)
        
    async def publish(self, content, media=None):
        """
        Publish content to Twitter.
        
        Args:
            content: Either a string or a Discord Message object
            media: Optional media attachments (not used for Twitter Basic tier)
            
        Returns:
            dict: Result of the publishing operation
        """
        if not self.client:
            return {"success": False, "platform": "twitter", "error": "Client not initialized"}
        
        try:
            # Check if content is a Discord Message object
            if isinstance(content, discord.Message):
                self.logger.info(f"Processing Discord message with ID: {content.id}")
                
                # Debug: Log message details
                self.logger.info(f"Message content: '{content.content}'")
                self.logger.info(f"Has embeds: {len(content.embeds) > 0}")
                if content.embeds:
                    for i, embed in enumerate(content.embeds):
                        self.logger.info(f"Embed {i+1} - Title: '{embed.title}', Description: '{embed.description[:50] if embed.description else 'None'}...'")
                
                tweet_text = self._format_discord_message(content)
                self.logger.info(f"Formatted tweet text: '{tweet_text[:50]}...'")
            else:
                # Assume it's a string
                tweet_text = str(content)
                self.logger.info(f"Using provided string content: '{tweet_text[:50]}...'")
            
            # Ensure we have text to tweet
            if not tweet_text or tweet_text.strip() == "":
                self.logger.error("No content extracted from message")
                return {"success": False, "platform": "twitter", "error": "No content to tweet"}
            
            # Smart truncation for long tweets
            if len(tweet_text) > 280:
                tweet_text = self._smart_truncate(tweet_text, 280)
            
            # Post the tweet
            self.logger.info(f"Posting tweet: '{tweet_text}'")
            response = self.client.create_tweet(text=tweet_text)
            
            # Log and return success
            tweet_id = response.data["id"]
            self.logger.info(f"Published tweet: {tweet_id}")
            return {"success": True, "platform": "twitter", "id": tweet_id}
        except Exception as e:
            # Log and return error
            self.logger.error(f"Failed to publish to Twitter: {e}")
            return {"success": False, "platform": "twitter", "error": str(e)}
    
    def _format_discord_message(self, message):
        """
        Format a Discord message for Twitter.
        
        Args:
            message: Discord Message object
            
        Returns:
            str: Formatted text for Twitter
        """
        # First check if the message has embeds
        if message.embeds and len(message.embeds) > 0:
            # Use the first embed
            embed = message.embeds[0]
            formatted_text = self._format_embed_for_twitter(embed)
            
            # If we got content from the embed, return it
            if formatted_text and formatted_text.strip() != "":
                return formatted_text
        
        # If no embeds or embed formatting failed, use the message content
        if message.content and message.content.strip() != "":
            return message.content
        
        # If message has attachments but no content or embeds
        if message.attachments:
            return "Shared content from Discord (attachments not included)"
        
        # If we have a referenced message (reply), try to use that
        if message.reference and hasattr(message, 'referenced_message') and message.referenced_message:
            ref_msg = message.referenced_message
            if ref_msg.content:
                return f"Re: {ref_msg.content[:200]}"
        
        # Default message if nothing else is available
        return "Shared content from Discord"
    
    def _format_embed_for_twitter(self, embed):
        """
        Format a Discord embed for Twitter.
        
        Args:
            embed: Discord Embed object
            
        Returns:
            str: Formatted text for Twitter
        """
        self.logger.info(f"Formatting embed - Type: {embed.type}, Title: '{embed.title}', URL: '{embed.url}'")
        
        # Start with the title if available
        components = []
        if embed.title and embed.title.strip() != "":
            # Add a colon after the title
            title = embed.title.strip()
            if not title.endswith(":"):
                title += ":"
            components.append(title)
        
        # Add description if available
        if embed.description and embed.description.strip() != "":
            components.append(embed.description)
        
        # If we have fields, add them
        if embed.fields:
            for field in embed.fields:
                if field.name and field.value:
                    components.append(f"{field.name}: {field.value}")
        
        # Add URL if available
        if embed.url and embed.url.strip() != "":
            components.append(f"Source: {embed.url}")
        
        # Join components with a single newline for compactness
        tweet_text = "\n".join(components)
        
        # If we have no content, check for author or footer
        if not tweet_text or tweet_text.strip() == "":
            if embed.author and embed.author.name:
                tweet_text = f"Content from {embed.author.name}"
            elif embed.footer and embed.footer.text:
                tweet_text = f"Note: {embed.footer.text}"
            else:
                tweet_text = "Shared content from Discord"
        
        self.logger.info(f"Formatted embed text: '{tweet_text[:50]}...'")
        return tweet_text
    
    def _smart_truncate(self, text, max_length=280):
        """
        Intelligently truncate text to fit within Twitter's character limit.
        
        Args:
            text: The text to truncate
            max_length: Maximum allowed length (default: 280)
            
        Returns:
            str: Truncated text
        """
        # If text is already short enough, return it as is
        if len(text) <= max_length:
            return text
        
        # Split the text into components (assuming they're separated by newlines)
        components = text.split("\n")
        
        # If we have a title and URL, prioritize those
        if len(components) >= 2:
            title = components[0]
            
            # Find the URL component (usually starts with "Source: ")
            url_index = -1
            for i, comp in enumerate(components):
                if comp.startswith("Source: "):
                    url_index = i
                    break
            
            url = components[url_index] if url_index >= 0 else None
            
            # If we have both title and URL
            if url:
                # Calculate how much space we have for the middle content
                middle_components = components[1:url_index] if url_index > 1 else []
                middle_text = "\n".join(middle_components)
                
                # Calculate available space
                available_chars = max_length - len(title) - len("\n") - len("\n") - len(url)
                
                # If we have enough space for at least some of the middle content
                if available_chars > 10:  # Ensure we have at least 10 chars for middle content
                    # If middle text is already short enough
                    if len(middle_text) <= available_chars:
                        return f"{title}\n{middle_text}\n{url}"
                    
                    # Try to preserve complete sentences
                    sentences = re.split(r'(?<=[.!?])\s+', middle_text)
                    truncated_middle = ""
                    for sentence in sentences:
                        if len(truncated_middle) + len(sentence) + 3 <= available_chars:
                            if truncated_middle:
                                truncated_middle += " " + sentence
                            else:
                                truncated_middle = sentence
                        else:
                            break
                    
                    # If we couldn't fit even one sentence, do a simple truncation
                    if not truncated_middle:
                        truncated_middle = middle_text[:available_chars-3] + "..."
                    elif len(truncated_middle) < len(middle_text):
                        truncated_middle += "..."
                    
                    return f"{title}\n{truncated_middle}\n{url}"
                else:
                    # Not enough space for middle content, just use title and URL
                    return f"{title}\n{url}"
        
        # If we don't have clear components, do a simple truncation
        return text[:max_length-3] + "..."
    
    async def check_rate_limit(self):
        """Check if we're currently rate limited"""
        return not self.rate_limiter.is_limited() 