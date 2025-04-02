"""
Utility functions for handling media files in messages.
"""

import os
import tempfile
from typing import List, Optional

import aiohttp


async def download_attachments(attachments: List) -> List[str]:
    """
    Download attachments from a Discord message.

    Args:
        attachments: List of Discord attachment objects

    Returns:
        List of paths to downloaded files
    """
    file_paths = []

    if not attachments:
        return file_paths

    async with aiohttp.ClientSession() as session:
        for attachment in attachments:
            # Create a temporary file
            fd, file_path = tempfile.mkstemp(
                suffix=f".{attachment.filename.split('.')[-1]}"
            )
            os.close(fd)

            # Download the attachment
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())
                    file_paths.append(file_path)

    return file_paths


def get_media_type(file_path: str) -> Optional[str]:
    """
    Determine the media type of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Media type string or None if not recognized
    """
    extension = file_path.lower().split(".")[-1]

    # Image types
    if extension in ["jpg", "jpeg", "png", "gif", "webp"]:
        return "photo"

    # Video types
    if extension in ["mp4", "mov", "avi", "webm"]:
        return "video"

    # Audio types
    if extension in ["mp3", "wav", "ogg", "flac"]:
        return "audio"

    # Unknown type
    return None


def cleanup_files(file_paths: List[str]) -> None:
    """
    Delete temporary files after they've been used.

    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore errors when cleaning up
