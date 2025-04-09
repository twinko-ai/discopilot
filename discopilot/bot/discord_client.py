import logging
from typing import Dict, List, Optional

import discord
from discord import RawReactionActionEvent

from ..publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class HedwigBot(discord.Client):
    """Discord client for the DiscoPilot bot."""

    def __init__(
        self,
        token: str,
        server_ids: Optional[List[int]] = None,
        admin_ids: Optional[List[int]] = None,
        channel_ids: Optional[List[int]] = None,
        trigger_emoji: str = "📢",
        send_notifications: bool = False,
        *args,
        **kwargs,
    ):
        """Initialize the Discord client."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True
        super().__init__(intents=intents, *args, **kwargs)

        self.token = token
        self.server_ids = server_ids or []
        self.admin_ids = admin_ids or []
        self.channel_ids = channel_ids or []
        self.trigger_emoji = trigger_emoji
        self.send_notifications = send_notifications
        self.publishers: Dict[str, BasePublisher] = {}

        logger.info(f"Initialized Discord client with trigger emoji: {trigger_emoji}")
        logger.info(f"Trigger emoji repr: {repr(trigger_emoji)}")
        logger.info(f"Trigger emoji bytes: {trigger_emoji.encode('utf-8').hex()}")
        logger.info(f"Send notifications: {send_notifications}")

        if server_ids:
            logger.info(f"Listening to server IDs: {', '.join(map(str, server_ids))}")
        else:
            logger.info("Listening to all servers")

        if admin_ids:
            logger.info(f"Admin IDs: {', '.join(map(str, admin_ids))}")
        else:
            logger.warning("No admin IDs configured - anyone can trigger publishing")

        if channel_ids:
            logger.info(f"Listening to channel IDs: {', '.join(map(str, channel_ids))}")
        else:
            logger.info("Listening to all channels")

    async def on_ready(self):
        """Handle the bot being ready."""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} servers")
        for guild in self.guilds:
            logger.info(f"- {guild.name} (ID: {guild.id})")

    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """Handle raw reaction add event."""
        logger.info(f"Raw reaction detected: {payload.emoji} by user {payload.user_id}")

        # Check if the emoji matches our trigger
        if str(payload.emoji) != self.trigger_emoji:
            logger.debug(
                f"Emoji {payload.emoji} doesn't match trigger {self.trigger_emoji}"
            )
            return

        # Check if user is an admin (if admin_ids is set)
        if self.admin_ids and payload.user_id not in self.admin_ids:
            logger.warning(
                f"User {payload.user_id} tried to publish but is not an admin"
            )
            return

        # Check if message is in a server we're listening to
        if self.server_ids and payload.guild_id not in self.server_ids:
            logger.warning(
                f"Message is in server {payload.guild_id} which is not in the allowed list"
            )
            return

        # Check if message is in a channel we're listening to
        if self.channel_ids and payload.channel_id not in self.channel_ids:
            logger.warning(
                f"Message is in channel {payload.channel_id} which is not in the allowed list"
            )
            return

        # Get the channel and message
        channel = self.get_channel(payload.channel_id)
        if not channel:
            logger.error(f"Could not find channel {payload.channel_id}")
            return

        try:
            message = await channel.fetch_message(payload.message_id)
            logger.info(
                f"Found message: {message.id} with content: {message.content[:50]}..."
            )

            # Process the message
            await self.publish_message(message)
        except Exception as e:
            logger.error(f"Error fetching or publishing message: {e}", exc_info=True)

    async def publish_message(self, message):
        """Publish a message to all configured platforms."""
        logger.info(f"Publishing message {message.id} from {message.author}")

        results = {}

        for name, publisher in self.publishers.items():
            try:
                logger.info(f"Publishing to {name}...")
                status, url = await publisher.publish(message)
                results[name] = {"status": status, "url": url}
                logger.info(f"Published to {name}: {status}")
            except Exception as e:
                logger.error(f"Error publishing to {name}: {e}", exc_info=True)
                results[name] = {"status": f"Error: {str(e)}", "url": None}

        # Format results message
        result_lines = ["Publishing results:"]
        for platform, result in results.items():
            status = result["status"]
            url = result["url"]
            result_line = f"- {platform}: {status}"
            if url:
                result_line += f" - {url}"
            result_lines.append(result_line)

        result_message = "\n".join(result_lines)
        logger.info(result_message)

        # Only send notification if enabled
        if self.send_notifications:
            await message.channel.send(result_message)

        return results

    def add_publisher(self, name: str, publisher: BasePublisher):
        """Add a publisher to the client."""
        self.publishers[name] = publisher
        logger.info(f"Added publisher: {name}")

    def run_bot(self):
        """Run the bot."""
        logger.info("Starting bot...")
        self.run(self.token)
