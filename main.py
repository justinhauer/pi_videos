import os
import time
import logging
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = Credentials.from_authorized_user_file('credentials.json', SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Configuration
GOOGLE_DRIVE_FOLDER_ID = 'your_folder_id_here'
DOWNLOAD_PATH = '/path/to/download/folder/'
LIBREOFFICE_PATH = '/usr/bin/libreoffice'  # Adjust if necessary


def get_latest_file() -> Optional[Dict[str, Any]]:
    results = drive_service.files().list(
        q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.presentation'",
        orderBy='modifiedTime desc',
        pageSize=1,
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    if not items:
        logger.info('No files found.')
        return None
    return items[0]


def download_file(file_id: str, file_name: str) -> str:
    request = drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    file_path = os.path.join(DOWNLOAD_PATH, file_name)
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}%")
    return file_path


def play_slideshow(file_path: str) -> None:
    cmd = [LIBREOFFICE_PATH, '--show', file_path]
    process = subprocess.Popen(cmd)
    time.sleep(48 * 3600)  # Sleep for 48 hours
    process.terminate()


def cleanup(file_path: str) -> None:
    os.remove(file_path)
    logger.info(f"Removed file: {file_path}")


def main() -> None:
    latest_file = get_latest_file()
    if latest_file:
        file_path = download_file(latest_file['id'], latest_file['name'])
        play_slideshow(file_path)
        cleanup(file_path)
    else:
        logger.warning("No presentation file found in the specified Google Drive folder.")


if __name__ == '__main__':
    main()