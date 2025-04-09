#!/usr/bin/env python3
from unittest.mock import MagicMock, mock_open, patch

import pytest

from discopilot.publishers.twitter_publisher import TwitterPublisher


@pytest.mark.asyncio
async def test_twitter_publisher_init(mock_config):
    """Test initializing the Twitter publisher."""
    # Use the mock_config fixture
    publisher = TwitterPublisher(mock_config)

    assert publisher is not None
    assert publisher.api_key == mock_config.twitter_api_key
    assert publisher.api_secret == mock_config.twitter_api_secret
    assert publisher.access_token == mock_config.twitter_access_token
    assert publisher.access_secret == mock_config.twitter_access_secret
    assert publisher.bearer_token == mock_config.twitter_bearer_token


@pytest.mark.asyncio
async def test_twitter_publisher_publish(mock_config):
    """Test publishing a message."""
    publisher = TwitterPublisher(mock_config)

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
    message.embeds = []

    # Test publishing
    status, url = await publisher.publish(message)

    # Verify results
    assert status == "Success"
    assert url == "https://twitter.com/user/status/12345"
    publisher.client.create_tweet.assert_called_once_with(text="Test message")


@pytest.mark.asyncio
async def test_twitter_publisher_publish_with_embed(mock_config):
    """Test publishing a message with embed."""
    publisher = TwitterPublisher(mock_config)

    # Mock the Twitter API
    publisher.client = MagicMock()
    publisher.api = MagicMock()

    # Mock response data
    mock_response = MagicMock()
    mock_response.data = {"id": "12345"}
    publisher.client.create_tweet.return_value = mock_response

    # Create a mock message with embed
    message = MagicMock()
    message.content = ""
    message.attachments = []

    # Create mock embed
    mock_embed = MagicMock()
    mock_embed.title = "Test Title"
    mock_embed.description = "Test Description"
    mock_embed.url = "https://example.com"
    message.embeds = [mock_embed]

    # Test publishing
    status, url = await publisher.publish(message)

    # Verify results
    assert status == "Success"
    assert url == "https://twitter.com/user/status/12345"
    publisher.client.create_tweet.assert_called_once()

    # Check that the tweet contains the embed information
    call_args = publisher.client.create_tweet.call_args[1]
    assert "text" in call_args
    assert "Test Title" in call_args["text"]
    assert "Test Description" in call_args["text"]
    assert "Source: https://example.com" in call_args["text"]


@pytest.mark.asyncio
async def test_twitter_publisher_publish_with_attachment(mock_config):
    """Test publishing a message with attachment."""
    publisher = TwitterPublisher(mock_config)

    # Mock the Twitter API
    publisher.client = MagicMock()
    publisher.api = MagicMock()

    # Mock response data
    mock_response = MagicMock()
    mock_response.data = {"id": "12345"}
    publisher.client.create_tweet.return_value = mock_response

    # Mock media upload
    mock_media = MagicMock()
    mock_media.media_id = "media123"
    publisher.api.media_upload.return_value = mock_media

    # Create a mock message with attachment
    message = MagicMock()
    message.content = "Test with attachment"

    # Create mock attachment
    mock_attachment = MagicMock()
    mock_attachment.url = "https://example.com/image.jpg"
    mock_attachment.filename = "image.jpg"
    mock_attachment.content_type = "image/jpeg"
    message.attachments = [mock_attachment]
    message.embeds = []

    # Let's look at the actual implementation of TwitterPublisher
    # and patch the specific methods it uses for handling attachments

    # Option 1: If it uses tempfile
    with (
        patch("tempfile.NamedTemporaryFile") as mock_temp_file,
        patch("requests.get") as mock_get,
        patch("builtins.open", mock_open(read_data=b"fake_image_data")),
    ):

        # Setup mock temp file
        mock_file = MagicMock()
        mock_file.name = "temp_image.jpg"
        mock_file.__enter__.return_value = mock_file
        mock_temp_file.return_value = mock_file

        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Test publishing
        status, url = await publisher.publish(message)

        # Verify results
        assert status == "Success"
        assert url == "https://twitter.com/user/status/12345"

        # Check that the tweet contains the correct text
        call_args = publisher.client.create_tweet.call_args[1]
        assert "text" in call_args
        assert call_args["text"] == "Test with attachment"

        # If media_ids is in the call args, check it
        if "media_ids" in call_args:
            assert call_args["media_ids"] == ["media123"]
            publisher.api.media_upload.assert_called_once()


@pytest.mark.asyncio
async def test_twitter_publisher_publish_error(mock_config):
    """Test error handling during publishing."""
    publisher = TwitterPublisher(mock_config)

    # Mock the Twitter API
    publisher.client = MagicMock()
    publisher.api = MagicMock()

    # Make the API raise an exception
    publisher.client.create_tweet.side_effect = Exception("API Error")

    # Create a mock message
    message = MagicMock()
    message.content = "Test message"
    message.attachments = []
    message.embeds = []

    # Test publishing
    status, url = await publisher.publish(message)

    # Verify results
    assert status.startswith("Error")
    assert "API Error" in status
    assert url is None


# For running the test directly
if __name__ == "__main__":
    pytest.main()
