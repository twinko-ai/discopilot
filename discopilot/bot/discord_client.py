import logging
from typing import Dict, List, Optional

import discord

from ..publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class HedwigBot(discord.Client):
    """Discord client for the DiscoPilot bot."""

    def __init__(
        self,
        token: str,
        server_ids: Optional[List[int]] = None,
        admin_ids: Optional[List[int]] = None,
        trigger_emoji: str = "📢",
        *args,
        **kwargs,
    ):
        """Initialize the Discord client."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        super().__init__(intents=intents, *args, **kwargs)

        self.token = token
        self.server_ids = server_ids or []
        self.admin_ids = admin_ids or []
        self.trigger_emoji = trigger_emoji
        self.publishers: Dict[str, BasePublisher] = {}

        logger.info(f"Initialized Discord client with trigger emoji: {trigger_emoji}")
        if server_ids:
            logger.info(f"Listening to server IDs: {', '.join(map(str, server_ids))}")
        else:
            logger.info("Listening to all servers")

        if admin_ids:
            logger.info(f"Admin IDs: {', '.join(map(str, admin_ids))}")
        else:
            logger.warning("No admin IDs configured - anyone can trigger publishing")

    async def on_ready(self):
        """Handle the bot being ready."""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def on_reaction_add(self, reaction, user):
        """Handle reaction added to a message."""
        logger.debug(f"Reaction detected: {reaction.emoji} by user {user.name} ({user.id})")
        
        # Ignore bot's own reactions
        if user.id == self.user.id:
            logger.debug(f"Ignoring bot's own reaction")
            return

        # Check if reaction is the trigger emoji
        emoji = str(reaction.emoji)
        logger.debug(f"Comparing reaction emoji '{emoji}' with trigger emoji '{self.trigger_emoji}'")
        if emoji != self.trigger_emoji:
            logger.debug(f"Emoji doesn't match trigger emoji, ignoring")
            return

        # Check if user is an admin (if admin list is configured)
        logger.debug(f"Checking if user {user.id} is in admin list: {self.admin_ids}")
        if self.admin_ids and user.id not in self.admin_ids:
            logger.warning(
                f"User {user.name} ({user.id}) tried to publish but is not an admin"
            )
            return

        message = reaction.message
        logger.debug(f"Message content: {message.content[:50]}...")
        logger.info(
            f"Reaction added by {user.name} ({user.id}) to message {message.id} "
            f"with emoji {emoji}"
        )

        # Check if message is in a server we're listening to
        server_id = message.guild.id if message.guild else None
        logger.debug(f"Message server ID: {server_id}, Allowed server IDs: {self.server_ids}")
        if (
            self.server_ids
            and message.guild
            and message.guild.id not in self.server_ids
        ):
            logger.warning(
                f"Message {message.id} is in server {message.guild.id} "
                f"which is not in the allowed list"
            )
            return

        logger.debug(f"All checks passed, publishing message")
        await self.publish_message(message)

    async def publish_message(self, message):
        """Publish a message to all configured platforms."""
        logger.debug(f"publish_message called for message ID: {message.id}")
        
        if not self.publishers:
            logger.warning("No publishers configured")
            await message.reply(
                "No publishing platforms configured.", mention_author=False
            )
            return

        logger.info(
            f"Publishing message {message.id} from {message.author.name} "
            f"to {len(self.publishers)} platforms"
        )
        
        logger.debug(f"Available publishers: {list(self.publishers.keys())}")

        results = []
        for name, publisher in self.publishers.items():
            logger.debug(f"Attempting to publish to {name}")
            try:
                logger.debug(f"Calling {name}.publish() method")
                status, url = await publisher.publish(message)
                logger.info(
                    f"Message {message.id} published to {name} with status {status} "
                    f"and URL {url}"
                )
                results.append((name, status, url))
            except Exception as e:
                logger.error(f"Error publishing to {name}: {e}", exc_info=True)
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                results.append((name, f"Error: {str(e)}", None))

        # Reply with results
        reply = "Publishing results:\n"
        for publisher_name, status, url in results:
            reply += f"- {publisher_name}: {status}"
            if url:
                reply += f" - {url}"
            reply += "\n"

        logger.debug(f"Sending reply: {reply}")
        await message.reply(reply, mention_author=False)

    def add_publisher(self, name: str, publisher: BasePublisher):
        """Add a publisher to the client."""
        self.publishers[name] = publisher
        logger.info(f"Added publisher: {name}")

    def run_bot(self):
        """Run the bot."""
        logger.info("Starting bot...")
        self.run(self.token)
