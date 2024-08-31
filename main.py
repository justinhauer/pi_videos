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

# Configuration, change folder ID
GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "15f0fYEHqzRttjf99I8L8RI5l0-c15WaN")
DOWNLOAD_PATH: str = os.getcwd()
DAYS_TO_RUN: int = int(os.getenv("DAYS_TO_RUN", 6))


def get_files_from_drive(folder_id: str) -> Generator[Dict[str, Any], None, None]:
    """
    Retrieve the video files from the specified Google Drive folder, one at a time.

    Args:
        folder_id (str): The Google Drive folder ID to search.

    Yields:
        Dict[str, Any]: A dictionary containing the file's 'id', 'name', and 'modifiedTime'.
    """
    try:
        # List of common video file MIME types
        video_mime_types = [
            'video/mp4',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'video/webm',
            'video/x-flv',
            'video/x-ms-wmv',
            'video/mpeg',
        ]

        mime_type_query = " or ".join([f"mimeType='{mime}'" for mime in video_mime_types])
        query = f"'{folder_id}' in parents and ({mime_type_query})"

        page_token: Optional[str] = None
        while True:
            results: Dict[str, Any] = drive_service.files().list(
                q=query,
                orderBy="modifiedTime desc",
                pageSize=10,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, modifiedTime)",
            ).execute()
            items: List[Dict[str, Any]] = results.get("files", [])
            for item in items:
                yield item
            page_token = results.get("nextPageToken", None)
            if not page_token:
                break
    except Exception as e:
        logging.error(f"An error occurred while retrieving files: {e}")


def get_latest_file() -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recently modified video file from the specified Google Drive folder.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the file's 'id', 'name', and 'modifiedTime' if found,
        or None if no files are found.
    """
    try:
        files_generator = get_files_from_drive(GOOGLE_DRIVE_FOLDER_ID)
        latest_file = next(files_generator, None)
        if latest_file:
            logging.info(f"Latest video file found: {latest_file['name']}, modified on {latest_file['modifiedTime']}")
        else:
            logging.info("No video files found.")
        return latest_file
    except Exception as e:
        logging.error(f"An error occurred while retrieving the latest file: {e}")
        return None


def download_file(file_id: str, file_name: str) -> str:
    """
    Download a video file from Google Drive and save it to the specified download path.

    Args:
        file_id (str): The Google Drive file ID of the video to download.
        file_name (str): The name to give the downloaded file.

    Returns:
        str: The full path of the downloaded file.
    """
    file_path: str = os.path.join(DOWNLOAD_PATH, file_name)
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logging.info(f"Download {int(status.progress() * 100)}%")
        fh.close()
        logging.info(f"File downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"An error occurred while downloading the file: {e}")
        return ""


def play_video(file_path: str) -> None:
    """
    Launch VLC to play the video and wait for the specified duration before terminating.

    Args:
        file_path (str): The full path to the video file to be played.
    """
    try:
        # Ensure DISPLAY is set for GUI applications
        os.environ['DISPLAY'] = ':0'

        # VLC command to start video in fullscreen and loop
        vlc_cmd = [
            "cvlc",  # Use cvlc (console VLC) to avoid any GUI dialogs
            "--fullscreen",  # Start in fullscreen mode
            "--loop",  # Loop the video
            "--no-osd",  # No on-screen display
            "--no-video-title-show",  # Don't show the title of the video
            file_path  # Path to the video file
        ]

        # Start VLC
        process = subprocess.Popen(vlc_cmd)

        logging.info(f"Started playing video: {file_path}")

        # Wait for the specified duration
        time.sleep(DAYS_TO_RUN * 24 * 3600)

        # Terminate VLC
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()

        logging.info(f"Video played for {DAYS_TO_RUN} days and terminated.")
    except Exception as e:
        logging.error(f"An error occurred while playing the video: {e}")


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
    Main function to orchestrate the video playback process:
    1. Retrieve the latest video from Google Drive
    2. Download the video
    3. Play the video for the specified duration
    4. Clean up the downloaded file
    """
    latest_file: Optional[Dict[str, Any]] = get_latest_file()
    if latest_file:
        file_path: str = download_file(latest_file["id"], latest_file["name"])
        if file_path:
            play_video(file_path)
            cleanup(file_path)
        else:
            logging.warning("Failed to download the video file.")
    else:
        logging.warning(
            "No video file found in the specified Google Drive folder."
        )


if __name__ == "__main__":
    main()