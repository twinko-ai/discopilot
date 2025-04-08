#!/usr/bin/env python3
import tweepy
import yaml
import datetime

# Load config
with open('/home/botuser/.config/discopilot/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get Twitter credentials
twitter = config.get('twitter', {})
api_key = twitter.get('api_key')
api_secret = twitter.get('api_secret')
access_token = twitter.get('access_token')
access_secret = twitter.get('access_secret')

print(f"API Key: {api_key[:4]}...{api_key[-4:] if api_key else None}")
print(f"API Secret: {api_secret[:4]}...{api_secret[-4:] if api_secret else None}")
print(f"Access Token: {access_token[:4]}...{access_token[-4:] if access_token else None}")
print(f"Access Secret: {access_secret[:4]}...{access_secret[-4:] if access_secret else None}")

try:
    # Set up authentication
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)
    
    # Verify credentials
    user = api.verify_credentials()
    print(f"Successfully authenticated as: {user.screen_name}")
    
    # Post a test tweet
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tweet = f"Test tweet from DiscoPilot at {timestamp}"
    print(f"Posting tweet: {tweet}")
    
    result = api.update_status(tweet)
    print(f"Tweet posted successfully! ID: {result.id}")
    print(f"URL: https://twitter.com/{user.screen_name}/status/{result.id}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()