#!/usr/bin/env python3
import asyncio
import unittest
from unittest.mock import patch, MagicMock
from discopilot.publishers.twitter_publisher import TwitterPublisher
from discopilot.utils.config import Config

class TestTwitterPublisher(unittest.TestCase):
    def setUp(self):
        # Mock the config
        self.config = MagicMock()
        self.config.twitter_api_key = "test_key"
        self.config.twitter_api_secret = "test_secret"
        self.config.twitter_access_token = "test_token"
        self.config.twitter_access_secret = "test_secret"
        self.config.twitter_bearer_token = "test_bearer"
        
    @patch('tweepy.Client')
    @patch('tweepy.API')
    @patch('tweepy.OAuth1UserHandler')
    def test_init(self, mock_oauth, mock_api, mock_client):
        # Test initialization
        publisher = TwitterPublisher(self.config)
        mock_oauth.assert_called_once()
        mock_api.assert_called_once()
        mock_client.assert_called_once()
        
    @patch('tweepy.Client')
    @patch('tweepy.API')
    @patch('tweepy.OAuth1UserHandler')
    async def test_publish(self, mock_oauth, mock_api, mock_client):
        # Setup mock return values
        mock_instance = mock_client.return_value
        mock_instance.create_tweet.return_value = MagicMock(data={"id": "12345"})
        
        # Test publishing
        publisher = TwitterPublisher(self.config)
        result = await publisher.publish("Test message")
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["platform"], "twitter")
        self.assertEqual(result["id"], "12345")
        mock_instance.create_tweet.assert_called_once_with(text="Test message")

# For running the test directly
if __name__ == "__main__":
    unittest.main() 