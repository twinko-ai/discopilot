import logging
import os
from typing import Dict, Optional, Tuple

import tweepy

from ..utils.media import download_attachments, get_media_type
from .base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class TwitterPublisher(BasePublisher):
    """Publisher for Twitter (X)."""

    def __init__(self, config: Dict):
        """Initialize the Twitter publisher."""
        super().__init__(config)

        # Get Twitter API credentials from config
        self.api_key = config.twitter_api_key
        self.api_secret = config.twitter_api_secret
        self.access_token = config.twitter_access_token
        self.access_secret = config.twitter_access_secret
        self.bearer_token = config.twitter_bearer_token

        # Check if credentials are provided
        if not all(
            [self.api_key, self.api_secret, self.access_token, self.access_secret]
        ):
            logger.warning("Twitter API credentials not fully configured")
            self.client = None
            self.api = None
            return

        # Initialize Twitter API client
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret, self.access_token, self.access_secret
        )
        self.api = tweepy.API(auth)

        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
        )

        logger.info("Twitter publisher initialized")

    async def publish(self, message) -> Tuple[str, Optional[str]]:
        """Publish a message to Twitter."""
        try:
            # Log the entire message object structure
            logger.info(f"Publishing message type: {type(message)}")

            # Check if message is a Discord message object
            if hasattr(message, "id"):
                logger.info(f"Message ID: {message.id}")
            else:
                logger.error("Message object doesn't have an ID attribute")
                return "Error: Invalid message object", None

            if not self.client or not self.api:
                logger.error(
                    "Twitter API not configured properly - client or API is None"
                )
                return "Error: Twitter API not configured", None

            # Get message content with better error handling
            try:
                if hasattr(message, "content"):
                    content = message.content
                    logger.info(
                        f"Message content: {content[:50]}..."
                        if content
                        else "No content"
                    )
                else:
                    # If message is a string (from test scripts)
                    if isinstance(message, str):
                        content = message
                        logger.info(f"Message is a string: {content[:50]}...")
                    else:
                        logger.error(
                            f"Message has no content attribute and is not a string: {type(message)}"
                        )
                        return "Error: Cannot extract content from message", None
            except Exception as e:
                logger.error(f"Error accessing message content: {e}", exc_info=True)
                return f"Error accessing message content: {str(e)}", None

            # Check for embeds if content is empty
            has_embeds = hasattr(message, "embeds") and message.embeds
            logger.info(f"Message has embeds: {has_embeds}")

            if has_embeds and not content:
                # Format embed content in the original style
                embed = message.embeds[0]  # Use the first embed

                title = embed.title or ""
                description = embed.description or ""
                url = embed.url or ""

                logger.info(f"Embed title: {title}")
                logger.info(
                    f"Embed description: {description[:50]}..."
                    if description
                    else "No description"
                )
                logger.info(f"Embed URL: {url}")

                # Calculate available space for description
                # Title line: title + ":"
                # URL line: "Source: " + url
                # 2 newlines
                reserved_chars = len(title) + 1 + len("Source: ") + len(url) + 2
                available_chars = 280 - reserved_chars

                logger.info(
                    f"Reserved chars: {reserved_chars}, Available for description: {available_chars}"
                )

                # Format the tweet with single line breaks
                tweet_parts = []

                # Add title with colon
                if title:
                    tweet_parts.append(f"{title}:")

                # Add description with smart truncation
                if description:
                    if len(description) <= available_chars:
                        # Use full description if it fits
                        tweet_parts.append(description)
                    else:
                        # Try to find a good breakpoint
                        # First try to find a sentence break
                        sentences = description.split(". ")
                        desc_part = ""
                        for sentence in sentences:
                            if len(desc_part + sentence + ". ") <= available_chars:
                                if desc_part:
                                    desc_part += ". " + sentence
                                else:
                                    desc_part = sentence
                            else:
                                break

                        # If we have at least one sentence, use it
                        if (
                            desc_part and len(desc_part) > 20
                        ):  # Ensure it's not too short
                            if not desc_part.endswith("."):
                                desc_part += "."
                            tweet_parts.append(desc_part)
                        else:
                            # Otherwise use as many characters as possible
                            tweet_parts.append(
                                description[: available_chars - 3] + "..."
                            )

                # Add URL with "Source:" prefix
                if url:
                    tweet_parts.append(f"Source: {url}")

                # Combine parts into final content with single line breaks
                content = "\n".join(tweet_parts)
                logger.info(f"Formatted tweet content: {content[:100]}...")
                logger.info(f"Tweet length: {len(content)} characters")

            # Check if we have content, embeds, or attachments
            has_attachments = hasattr(message, "attachments") and message.attachments

            if not content and not has_attachments:
                logger.error("Message has no content, embeds, or attachments")
                return "Error: Empty message", None

            # Download attachments if any
            media_ids = []
            if has_attachments:
                logger.debug(f"Message has {len(message.attachments)} attachments")
                media_files = await download_attachments(message.attachments)

                if media_files:
                    logger.info(
                        f"Uploading media for tweet: "
                        f"{', '.join([f'{m.filename} ({m.size} bytes)' for m in media_files])}"
                    )

                    # Upload media to Twitter
                    for media in media_files:
                        media_type = get_media_type(media.filename)
                        logger.debug(
                            f"Media type: {media_type} for file {media.filename}"
                        )
                        try:
                            logger.debug(f"Uploading media file: {media.filename}")
                            media_id = self.api.media_upload(
                                filename=media.filename, file=media.file
                            ).media_id_string
                            logger.debug(f"Media uploaded successfully, ID: {media_id}")
                            media_ids.append(media_id)
                        except Exception as e:
                            logger.error(f"Error uploading media: {e}", exc_info=True)
                            return f"Error uploading media: {str(e)}", None

                            # Clean up temp files
                            try:
                                os.unlink(media.filename)
                            except Exception as e:
                                logger.warning(f"Error deleting temp file: {e}")

            # Final check to ensure we're under 280 characters
            if len(content) > 280:
                logger.debug(f"Content too long ({len(content)} chars), truncating")
                content = content[:277] + "..."

            try:
                # Post tweet
                logger.debug(
                    f"Attempting to post tweet with content: '{content[:50]}...'"
                )
                logger.debug(f"Using media IDs: {media_ids}")

                if media_ids:
                    logger.debug("Creating tweet with media")
                    response = self.client.create_tweet(
                        text=content, media_ids=media_ids
                    )
                else:
                    logger.debug("Creating tweet without media")
                    response = self.client.create_tweet(text=content)

                logger.debug(f"Twitter API response: {response}")
                tweet_id = response.data["id"]
                tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                logger.info(f"Tweet posted successfully with ID: {tweet_id}")
                return "Success", tweet_url
            except Exception as e:
                logger.error(f"Error posting tweet: {e}", exc_info=True)
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                return f"Error: {str(e)}", None
        except Exception as e:
            logger.error(f"Error publishing message: {e}", exc_info=True)
            return f"Error: {str(e)}", None

    def check_rate_limit(self) -> Dict:
        """Check Twitter API rate limit status."""
        if not self.api:
            return {"error": "Twitter API not configured"}

        try:
            rate_limit_status = self.api.rate_limit_status()
            logger.info(
                f"Rate limit status: "
                f"{rate_limit_status.get('resources', {}).get('statuses', {})}"
            )
            return rate_limit_status
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}", exc_info=True)
            return {"error": str(e)}
