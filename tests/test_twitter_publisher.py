#!/usr/bin/env python3
from unittest.mock import MagicMock

import pytest

from discopilot.publishers.twitter_publisher import TwitterPublisher


def test_twitter_publisher_init():
    """Test initializing the Twitter publisher."""
    config = {
        "twitter": {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_secret": "test_secret",
            "bearer_token": "test_bearer",
        }
    }

    publisher = TwitterPublisher(config)
    assert publisher is not None
    assert publisher.api_key == "test_key"
    assert publisher.api_secret == "test_secret"
    assert publisher.access_token == "test_token"
    assert publisher.access_secret == "test_secret"
    assert publisher.bearer_token == "test_bearer"


@pytest.mark.asyncio
async def test_twitter_publisher_publish():
    """Test publishing a message."""
    config = {
        "twitter": {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_secret": "test_secret",
            "bearer_token": "test_bearer",
        }
    }

    publisher = TwitterPublisher(config)

    # Mock the Twitter API
    publisher.client = MagicMock()
    publisher.api = MagicMock()

    # Mock response data
    mock_response = MagicMock()
    mock_response.data = {"id": "12345"}
    publisher.client.create_tweet.return_value = mock_response

    # Create a mock message
    message = MagicMock()
    message.content = "Test message"
    message.attachments = []

    # Test publishing
    status, url = await publisher.publish(message)

    # Verify results
    assert status == "Success"
    assert url == "https://twitter.com/user/status/12345"
    publisher.client.create_tweet.assert_called_once_with(text="Test message")


# For running the test directly
if __name__ == "__main__":
    pytest.main()
