import unittest
from unittest.mock import patch, MagicMock


class TestSlideshowScript(unittest.TestCase):
    @patch('google.oauth2.credentials.Credentials.from_authorized_user_file')
    @patch('googleapiclient.discovery.build')
    def setUp(self, mock_build, mock_creds):
        self.mock_drive_service = MagicMock()
        mock_build.return_value = self.mock_drive_service

    def test_get_latest_file(self):
        mock_file = {'id': 'test_id', 'name': 'test_file.pptx'}
        self.mock_drive_service.files().list().execute.return_value = {'files': [mock_file]}
        result = get_latest_file()
        self.assertEqual(result, mock_file)

    def test_get_latest_file_no_files(self):
        self.mock_drive_service.files().list().execute.return_value = {'files': []}
        result = get_latest_file()
        self.assertIsNone(result)

    @patch('io.FileIO')
    @patch('googleapiclient.http.MediaIoBaseDownload')
    def test_download_file(self, mock_media_download, mock_file_io):
        mock_media_download.return_value.next_chunk.side_effect = [(MagicMock(progress=lambda: 0.5), False),
                                                                   (MagicMock(progress=lambda: 1.0), True)]
        file_path = download_file('test_id', 'test_file.pptx')
        self.assertEqual(file_path, os.path.join(DOWNLOAD_PATH, 'test_file.pptx'))

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_play_slideshow(self, mock_sleep, mock_popen):
        play_slideshow('test_file.pptx')
        mock_popen.assert_called_once_with([LIBREOFFICE_PATH, '--show', 'test_file.pptx'])
        mock_sleep.assert_called_once_with(48 * 3600)

    @patch('os.remove')
    def test_cleanup(self, mock_remove):
        cleanup('test_file.pptx')
        mock_remove.assert_called_once_with('test_file.pptx')


if __name__ == '__main__':
    unittest.main()