import os
import time
import logging
from typing import Optional, Dict, Any, List
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
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

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first time.
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

drive_service: Any = build("drive", "v3", credentials=creds)

# Configuration
GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "15f0fYEHqzRttjf99I8L8RI5l0-c15WaN")
DOWNLOAD_PATH: str = os.getenv("DOWNLOAD_PATH", "/test_folder/")
LIBREOFFICE_PATH: str = os.getenv(
    "LIBREOFFICE_PATH", "/usr/bin/libreoffice"
)


def get_latest_file() -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recently modified presentation file from the specified Google Drive folder.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the file's 'id' and 'name' if found,
        or None if no files are found.
    """
    try:
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
        print(f"item is {items[0]}")
        return items[0]
    except Exception as e:
        logger.error(f"An error occurred while retrieving files: {e}")
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
            downloader: MediaIoBaseDownload = MediaIoBaseDownload(fh, request)
            done: bool = False
            while done is False:
                status: Any
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}%")
        print(file_path)
        return file_path
    except Exception as e:
        logger.error(f"An error occurred while downloading the file: {e}")
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
