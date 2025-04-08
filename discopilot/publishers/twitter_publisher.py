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
        logger.debug(f"Twitter publish method called with message ID: {message.id}")
        
        if not self.client or not self.api:
            logger.error("Twitter API not configured properly - client or API is None")
            return "Error: Twitter API not configured", None

        # Get message content
        content = message.content
        logger.debug(f"Message content length: {len(content) if content else 0}")
        
        if not content and not message.attachments:
            logger.error("Message has no content or attachments")
            return "Error: Empty message", None

        # Download attachments if any
        media_ids = []
        if message.attachments:
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
                    logger.debug(f"Media type: {media_type} for file {media.filename}")
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

        # Truncate content if needed (Twitter limit is 280 chars)
        if len(content) > 280:
            logger.debug(f"Content too long ({len(content)} chars), truncating")
            content = content[:277] + "..."

        try:
            # Post tweet
            logger.debug(f"Attempting to post tweet with content: '{content[:50]}...'")
            logger.debug(f"Using media IDs: {media_ids}")
            
            if media_ids:
                logger.debug("Creating tweet with media")
                response = self.client.create_tweet(text=content, media_ids=media_ids)
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
