import os
from typing import Any, Dict, List
import pytest
from unittest.mock import patch, Mock, mock_open
from googleapiclient.http import HttpMockSequenceWithErrors

# Import the functions you want to test
from main import (
    get_latest_file,
    download_file,
    play_slideshow,
    cleanup,
)


@pytest.fixture
def mock_drive_service() -> Mock:
    """
    Fixture to mock the Google Drive API service.

    Returns:
        Mock: A mock instance of the Google Drive API service.
    """
    with patch("main.build") as mock_build:
        mock_service: Mock = Mock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_filesystem() -> Mock:
    """
    Fixture to mock the file system operations.

    Returns:
        Mock: A mock instance of the file system operations.
    """
    with patch("main.io.FileIO", mock_open()):
        with patch("main.os.remove") as mock_remove:
            yield mock_remove

# Test case for get_latest_file
def test_get_latest_file(mock_drive_service: Mock) -> None:
    """
    Test case for the get_latest_file function.

    Args:
        mock_drive_service (Mock): A mock instance of the Google Drive API service.
    """
    mock_files_list: Mock = Mock()
    mock_drive_service.files.return_value.list.return_value = mock_files_list
    mock_files_list.execute.return_value = {"files": [{"id": "file_id", "name": "file_name.pptx"}]}

    result = get_latest_file()
    assert result == {"id": "file_id", "name": "file_name.pptx"}

    mock_files_list.execute.return_value = {"files": []}
    result = get_latest_file()
    assert result is None


def test_download_file(mock_drive_service: Mock, mock_filesystem: Mock) -> None:
    """
    Test case for the download_file function.

    Args:
        mock_drive_service (Mock): A mock instance of the Google Drive API service.
        mock_filesystem (Mock): A mock instance of the file system operations.
    """
    mock_media_request: Mock = Mock()
    mock_drive_service.files.return_value.export_media.return_value = mock_media_request

    mock_status: Mock = Mock()
    mock_status.progress.return_value = 0.5
    mock_media_request.next_chunk.side_effect = [(mock_status, False), (mock_status, True)]

    file_path: str = download_file("file_id", "file_name.pptx")
    assert file_path == os.path.join(DOWNLOAD_PATH, "file_name.pptx")


@patch("main.subprocess.Popen")
def test_play_slideshow(mock_popen: Mock) -> None:
    """
    Test case for the play_slideshow function.

    Args:
        mock_popen (Mock): A mock instance of the subprocess.Popen function.
    """
    mock_process: Mock = Mock()
    mock_popen.return_value = mock_process

    play_slideshow("/path/to/file.pptx")
    mock_popen.assert_called_with([LIBREOFFICE_PATH, "--impress", "--show", "/path/to/file.pptx"])
    mock_process.terminate.assert_called_once()


def test_cleanup(mock_filesystem: Mock) -> None:
    """
    Test case for the cleanup function.

    Args:
        mock_filesystem (Mock): A mock instance of the file system operations.
    """
    cleanup("/path/to/file.pptx")
    mock_filesystem.assert_called_with("/path/to/file.pptx")
