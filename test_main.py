# Unit tests
import unittest
from unittest.mock import patch, MagicMock


class TestSlideshowScript(unittest.TestCase):
    """
    Unit tests for the Raspberry Pi Slideshow Script.
    """

    @patch('google.oauth2.credentials.Credentials.from_authorized_user_file')
    @patch('googleapiclient.discovery.build')
    def setUp(self, mock_build: MagicMock, mock_creds: MagicMock) -> None:
        """
        Set up the test environment before each test method is run.
        """
        self.mock_drive_service: MagicMock = MagicMock()
        mock_build.return_value = self.mock_drive_service

    def test_get_latest_file(self) -> None:
        """
        Test that get_latest_file returns the correct file when one is available.
        """
        mock_file: Dict[str, str] = {'id': 'test_id', 'name': 'test_file.pptx'}
        self.mock_drive_service.files().list().execute.return_value = {'files': [mock_file]}
        result: Optional[Dict[str, Any]] = get_latest_file()
        self.assertEqual(result, mock_file)

    def test_get_latest_file_no_files(self) -> None:
        """
        Test that get_latest_file returns None when no files are found.
        """
        self.mock_drive_service.files().list().execute.return_value = {'files': []}
        result: Optional[Dict[str, Any]] = get_latest_file()
        self.assertIsNone(result)

    @patch('io.FileIO')
    @patch('googleapiclient.http.MediaIoBaseDownload')
    def test_download_file(self, mock_media_download: MagicMock, mock_file_io: MagicMock) -> None:
        """
        Test that download_file correctly downloads and saves a file.
        """
        mock_media_download.return_value.next_chunk.side_effect = [(MagicMock(progress=lambda: 0.5), False),
                                                                   (MagicMock(progress=lambda: 1.0), True)]
        file_path: str = download_file('test_id', 'test_file.pptx')
        self.assertEqual(file_path, os.path.join(DOWNLOAD_PATH, 'test_file.pptx'))

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_play_slideshow(self, mock_sleep: MagicMock, mock_popen: MagicMock) -> None:
        """
        Test that play_slideshow launches LibreOffice correctly and waits for the specified duration.
        """
        play_slideshow('test_file.pptx')
        mock_popen.assert_called_once_with([LIBREOFFICE_PATH, '--show', 'test_file.pptx'])
        mock_sleep.assert_called_once_with(48 * 3600)

    @patch('os.remove')
    def test_cleanup(self, mock_remove: MagicMock) -> None:
        """
        Test that cleanup correctly removes the specified file.
        """
        cleanup('test_file.pptx')
        mock_remove.assert_called_once_with('test_file.pptx')


if __name__ == '__main__':
    unittest.main()