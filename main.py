import os
import time
import logging
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import subprocess

# Set up logging with date in filename
current_date: str = time.strftime("%Y-%m-%d")
file_handler: logging.FileHandler = logging.FileHandler(f"app_{current_date}.log")
formatter: logging.Formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Set up Google Drive API credentials
SCOPES: List[str] = ["https://www.googleapis.com/auth/drive.readonly"]
creds: Credentials = Credentials.from_authorized_user_file("credentials.json", SCOPES)
drive_service: Any = build("drive", "v3", credentials=creds)

# Configuration
GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "your_folder_id_here")
DOWNLOAD_PATH: str = os.getenv("DOWNLOAD_PATH", "/path/to/download/folder/")
LIBREOFFICE_PATH: str = os.getenv(
    "LIBREOFFICE_PATH", "/usr/bin/libreoffice"
)  # Adjust if necessary


def get_latest_file() -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recently modified presentation file from the specified Google Drive folder.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the file's 'id' and 'name' if found,
        or None if no files are found.
    """
    results: Dict[str, Any] = (
        drive_service.files()
        .list(
            q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.presentation'",
            orderBy="modifiedTime desc",
            pageSize=1,
            fields="files(id, name)",
        )
        .execute()
    )
    items: List[Dict[str, Any]] = results.get("files", [])
    if not items:
        logger.info("No files found.")
        return None
    return items[0]


def download_file(file_id: str, file_name: str) -> str:
    """
    Download a file from Google Drive and save it to the specified download path.

    Args:
        file_id (str): The Google Drive file ID of the presentation to download.
        file_name (str): The name to give the downloaded file.

    Returns:
        str: The full path of the downloaded file.
    """
    request: Any = drive_service.files().export_media(
        fileId=file_id,
        mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    file_path: str = os.path.join(DOWNLOAD_PATH, file_name)
    with io.FileIO(file_path, "wb") as fh:
        downloader: MediaIoBaseDownload = MediaIoBaseDownload(fh, request)
        done: bool = False
        while done is False:
            status: Any
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}%")
    return file_path


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
    logger.info(f"Removed file: {file_path}")


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
        logger.warning(
            "No presentation file found in the specified Google Drive folder."
        )


if __name__ == "__main__":
    main()
