import discord
from discord.ext import commands
import logging
import asyncio
from ..utils.config import Config
from ..publishers.twitter_publisher import TwitterPublisher
# Import other publishers as needed

class HedwigBot(commands.Bot):
    """
    Discord bot that monitors channels and publishes content to social media
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.config = Config()
        self.logger = logging.getLogger("discopilot.bot")
        
        # Initialize publishers
        self.publishers = {}
        self.setup_publishers()
        
        # Register event handlers
        self.add_listener(self.on_ready, "on_ready")
        self.add_listener(self.on_raw_reaction_add, "on_raw_reaction_add")
    
    def setup_publishers(self):
        """Initialize all configured publishers"""
        # Twitter
        if hasattr(self.config, "twitter_api_key") and self.config.twitter_api_key:
            self.publishers["twitter"] = TwitterPublisher(self.config)
            self.logger.info("Twitter publisher initialized")
        
        # Add other publishers as needed
    
    async def on_ready(self):
        """Called when the bot is ready"""
        self.logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        self.logger.info(f"Monitoring for emoji: {self.config.trigger_emoji}")
        self.logger.info(f"Admin IDs: {self.config.admin_ids}")
    
    async def on_raw_reaction_add(self, payload):
        """Called when a reaction is added to a message"""
        # Check if the reaction is the trigger emoji and from an admin
        if (str(payload.emoji) == self.config.trigger_emoji and 
                payload.user_id in self.config.admin_ids):
            
            self.logger.info(f"Trigger emoji detected from admin {payload.user_id}")
            
            # Get the channel and message
            channel = self.get_channel(payload.channel_id)
            if not channel:
                self.logger.error(f"Could not find channel {payload.channel_id}")
                return
            
            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                self.logger.error(f"Could not find message {payload.message_id}")
                return
            
            # Process the message for publishing
            await self.publish_message(message)
    
    async def publish_message(self, message):
        """Publish a message to all configured platforms"""
        content = message.content
        
        # Extract media attachments
        media = []
        for attachment in message.attachments:
            media.append(attachment.url)
        
        # Publish to each platform
        results = {}
        for platform, publisher in self.publishers.items():
            if await publisher.check_rate_limit():
                result = await publisher.publish(content, media)
                results[platform] = result
                
                if result["success"]:
                    self.logger.info(f"Published to {platform}: {result.get('url', 'N/A')}")
                else:
                    self.logger.error(f"Failed to publish to {platform}: {result.get('error', 'Unknown error')}")
            else:
                self.logger.warning(f"Rate limit exceeded for {platform}")
                results[platform] = {"success": False, "error": "Rate limit exceeded"}
        
        # Add a confirmation reaction to the message
        await message.add_reaction("✅")
        
        # Send a summary as a reply
        summary = "**Publication Results:**\n"
        for platform, result in results.items():
            if result["success"]:
                summary += f"✅ {platform.capitalize()}: [View]({result.get('url', 'N/A')})\n"
            else:
                summary += f"❌ {platform.capitalize()}: {result.get('error', 'Unknown error')}\n"
        
        await message.reply(summary)
