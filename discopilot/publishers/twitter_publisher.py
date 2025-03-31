import tweepy
import asyncio
import time
import logging
from .base_publisher import BasePublisher
from ..utils.rate_limiter import RateLimiter

class TwitterPublisher(BasePublisher):
    def __init__(self, config):
        super().__init__(config)
        
        # For user authentication (posting tweets)
        self.auth = tweepy.OAuth1UserHandler(
            config.twitter_api_key,
            config.twitter_api_secret,
            config.twitter_access_token,
            config.twitter_access_secret
        )
        self.api = tweepy.API(self.auth)
        
        # For application-only authentication (higher rate limits for reading)
        self.client = tweepy.Client(
            bearer_token=config.twitter_bearer_token,
            consumer_key=config.twitter_api_key,
            consumer_secret=config.twitter_api_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_secret
        )
        
        # Initialize rate limiter - Twitter allows 300 tweets per 3 hours (180 minutes)
        self.rate_limiter = RateLimiter(300, 180 * 60)
        
    async def publish(self, content, media=None):
        """Publish a tweet with optional media"""
        if not await self.check_rate_limit():
            self.logger.warning("Rate limit exceeded for Twitter")
            return {"success": False, "error": "Rate limit exceeded"}
        
        try:
            # Use asyncio to run the blocking Twitter API calls in a thread pool
            loop = asyncio.get_event_loop()
            
            if media:
                # Handle media uploads
                media_ids = []
                for media_item in media[:4]:  # Twitter allows up to 4 media items
                    if media_item.startswith(('http://', 'https://')):
                        # Download from URL and upload
                        # This is simplified - you'd need to implement the download logic
                        pass
                    else:
                        # Upload local file
                        media_obj = await loop.run_in_executor(
                            None, 
                            lambda: self.api.media_upload(media_item)
                        )
                        media_ids.append(media_obj.media_id)
                
                # Create tweet with media
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.create_tweet(text=content, media_ids=media_ids)
                )
            else:
                # Text-only tweet
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.create_tweet(text=content)
                )
            
            # Record successful API call
            self.rate_limiter.add_call()
            
            return {
                "success": True,
                "platform": "twitter",
                "id": result.data["id"],
                "url": f"https://twitter.com/user/status/{result.data['id']}"
            }
            
        except tweepy.TweepyException as e:
            self.logger.error(f"Twitter API error: {str(e)}")
            
            # Handle rate limiting errors specifically
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                # Get the reset time from headers if available
                reset_time = e.response.headers.get('x-rate-limit-reset', 0)
                if reset_time:
                    wait_time = int(reset_time) - int(time.time())
                    self.rate_limiter.set_cooldown(wait_time)
            
            return {"success": False, "error": str(e), "platform": "twitter"}
    
    async def check_rate_limit(self):
        """Check if we're currently rate limited"""
        return not self.rate_limiter.is_limited() 