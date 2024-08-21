import os
import time
import logging
from typing import Optional, Dict, Any, List, Generator
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import subprocess

# Set up logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set up Google Drive API credentials
SCOPES: List[str] = ["https://www.googleapis.com/auth/drive.readonly"]

# Load the service account credentials from the JSON file
SERVICE_ACCOUNT_FILE: str = "credentials.json"
creds: service_account.Credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service: Any = build("drive", "v3", credentials=creds)

# Configuration
GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "15f0fYEHqzRttjf99I8L8RI5l0-c15WaN")
DOWNLOAD_PATH: str = os.getcwd()
LIBREOFFICE_PATH: str = os.getenv(
    "LIBREOFFICE_PATH", "/usr/bin/libreoffice"
)

def get_files_from_drive(folder_id: str) -> Generator[Dict[str, Any], None, None]:
    """
    Retrieve the presentation files from the specified Google Drive folder, one at a time.

    Args:
        folder_id (str): The Google Drive folder ID to search.

    Yields:
        Dict[str, Any]: A dictionary containing the file's 'id' and 'name'.
    """
    try:
        page_token: Optional[str] = None
        while True:
            results: Dict[str, Any] = drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.presentation'",
                orderBy="modifiedTime desc",
                pageSize=10,
                pageToken=page_token,
                fields="nextPageToken, files(id, name)",
            ).execute()
            items: List[Dict[str, Any]] = results.get("files", [])
            if not items:
                break
            for item in items:
                yield item
            page_token = results.get("nextPageToken", None)
            if not page_token:
                break
    except Exception as e:
        logging.error(f"An error occurred while retrieving files: {e}")

def get_latest_file() -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recently modified presentation file from the specified Google Drive folder.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the file's 'id' and 'name' if found,
        or None if no files are found.
    """
    try:
        files_generator = get_files_from_drive(GOOGLE_DRIVE_FOLDER_ID)
        for file_info in files_generator:
            return file_info
        logging.info("No files found.")
        return None
    except Exception as e:
        logging.error(f"An error occurred while retrieving files: {e}")
        return None

def download_file(file_id: str, file_name: str) -> str:
    """
    Download a file from Google Drive and save it to the specified download path.

    Args:
        file_id (str): The Google Drive file ID of the presentation to download.
        file_name (str): The name to give the downloaded file.

    Returns:
        str: The full path of the downloaded file.
    """
    file_path: str = os.path.join(DOWNLOAD_PATH, file_name)
    try:
        request: Any = drive_service.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        with io.FileIO(file_path, "wb") as fh:
            downloader: MediaIoBaseDownload = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
            done: bool = False
            while done is False:
                status: Any
                status, done = downloader.next_chunk()
                logging.info(f"Download {int(status.progress() * 100)}%")
        print(file_path)
        return file_path
    except Exception as e:
        logging.error(f"An error occurred while downloading the file: {e}")
        return ""

def play_slideshow(file_path: str) -> None:
    """
    Launch LibreOffice to play the slideshow and wait for 48 hours before terminating.

    Args:
        file_path (str): The full path to the presentation file to be played.
    """
    cmd: List[str] = [LIBREOFFICE_PATH, "--impress", "--show", file_path]
    process: subprocess.Popen = subprocess.Popen(cmd)
    time.sleep(144 * 3600)  # Sleep for 48 hours
    process.terminate()

def cleanup(file_path: str) -> None:
    """
    Remove the specified file from the filesystem.

    Args:
        file_path (str): The full path of the file to be removed.
    """
    os.remove(file_path)
    logging.info(f"Removed file: {file_path}")

def main() -> None:
    """
    Main function to orchestrate the slideshow process:
    1. Retrieve the latest presentation from Google Drive
    2. Download the presentation
    3. Play the slideshow for 48 hours
    4. Clean up the downloaded file
    """
    latest_file: Optional[Dict[str, Any]] = get_latest_file()
    if latest_file:
        file_path: str = download_file(latest_file["id"], latest_file["name"])
        play_slideshow(file_path)
        cleanup(file_path)
    else:
        logging.warning(
            "No presentation file found in the specified Google Drive folder."
        )

if __name__ == "__main__":
    main()