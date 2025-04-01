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
    
    def __init__(self, config, publishers):
        """Initialize the Discord client."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.config = config
        self.publishers = publishers
        self.logger = logging.getLogger("discopilot")
    
    async def on_ready(self):
        """Called when the client is done preparing the data received from Discord."""
        self.logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        
        # Set up activity
        activity = discord.Activity(type=discord.ActivityType.watching, name="for 📢 reactions")
        await self.change_presence(activity=activity)
    
    async def on_raw_reaction_add(self, payload):
        """Called when a reaction is added to a message."""
        # Check if the reaction is the trigger emoji
        if str(payload.emoji) != self.config.trigger_emoji:
            return
        
        # Get the channel and message
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # Check if user is an admin
        if payload.user_id in self.config.admin_ids:
            self.logger.info(f"Admin {payload.user_id} triggered publishing for message {payload.message_id}")
            
            # Publish the message to all configured platforms
            for name, publisher in self.publishers.items():
                # Pass the entire Discord message object to the publisher
                result = await publisher.publish(message)
                
                # Log the result
                if result["success"]:
                    self.logger.info(f"Published to {name}: {result.get('id', 'N/A')}")
                else:
                    self.logger.error(f"Failed to publish to {name}: {result.get('error', 'Unknown error')}")
        else:
            self.logger.info(f"Non-admin user {payload.user_id} attempted to trigger publishing")
    
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

    async def on_message(self, message):
        if message.content == '!ping':
            await message.channel.send('Pong!')
