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


def convert_video(input_path: str, timeout: int = 300) -> Optional[str]:
    """
    Convert the input video to H.264 format using FFmpeg with a timeout and progress reporting.

    Args:
        input_path (str): The path to the input video file.
        timeout (int): Maximum time in seconds to wait for conversion.

    Returns:
        Optional[str]: The path to the converted video file, or None if conversion failed.
    """
    output_path = os.path.splitext(input_path)[0] + "_converted.mp4"
    try:
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",  # Changed from ultrafast to medium for better balance
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            "-progress", "pipe:1",  # Output progress information to stdout
            output_path
        ]

        logging.info(f"Starting FFmpeg conversion: {' '.join(ffmpeg_cmd)}")

        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        start_time = time.time()
        last_progress_time = start_time

        while True:
            if process.poll() is not None:
                break
            if time.time() - start_time > timeout:
                process.terminate()
                logging.error(f"FFmpeg conversion timed out after {timeout} seconds")
                return None

            output = process.stdout.readline()
            if output:
                if "out_time_ms" in output:
                    current_time = time.time()
                    if current_time - last_progress_time >= 10:  # Log progress every 10 seconds
                        logging.info(f"Conversion in progress: {output.strip()}")
                        last_progress_time = current_time

        returncode = process.poll()
        _, stderr = process.communicate()

        if returncode != 0:
            logging.error(f"FFmpeg conversion failed with return code {returncode}")
            logging.error(f"FFmpeg stderr: {stderr}")
            return None

        logging.info(f"Video converted successfully: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"An error occurred during video conversion: {e}")
        return None


def play_video(file_path: str) -> None:
    """
    Convert the video, then launch VLC to play it with optimized settings.
    Includes enhanced error checking, logging, and alternative methods.

    Args:
        file_path (str): The full path to the video file to be played.
    """
    try:
        # Convert the video
        converted_file_path = convert_video(file_path)

        # Ensure DISPLAY is set for GUI applications
        os.environ['DISPLAY'] = ':0'
        logging.info(f"DISPLAY environment variable set to: {os.environ['DISPLAY']}")

        # Check if VLC is installed
        try:
            subprocess.run(["vlc", "--version"], check=True, capture_output=True, text=True)
            logging.info("VLC is installed and accessible")
        except subprocess.CalledProcessError:
            logging.error("VLC is not installed or not accessible")
            raise Exception("VLC is not installed or not accessible")

        # VLC command with optimized settings
        vlc_cmd = [
            "vlc",  # Changed from cvlc to vlc
            "--codec=h264_v4l2m2m",
            "--no-audio",
            "--no-video-deco",
            "--no-snapshot-preview",
            "--no-overlay",
            "--fullscreen",
            "--loop",
            "--no-osd",
            "--no-video-title-show",
            "--video-on-top",
            "--file-caching=5000",
            "--network-caching=5000",
            "--fps-trust",
            "--verbose=2",
            converted_file_path
        ]

        logging.info(f"Attempting to start VLC with command: {' '.join(vlc_cmd)}")

        # Start VLC
        process = subprocess.Popen(vlc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        logging.info(f"VLC process started with PID: {process.pid}")

        # Check if the process is still running after a short delay
        time.sleep(5)
        if process.poll() is None:
            logging.info("VLC process is still running after 5 seconds")
        else:
            logging.error(f"VLC process exited prematurely with return code: {process.returncode}")
            stdout, stderr = process.communicate()
            logging.error(f"VLC stdout: {stdout}")
            logging.error(f"VLC stderr: {stderr}")

            # Try alternative method: using os.system
            logging.info("Attempting to start VLC using os.system")
            os.system(f"vlc --codec=h264_v4l2m2m --fullscreen --loop {converted_file_path} &")
            time.sleep(5)

            # Check if VLC is running
            try:
                subprocess.run(["pgrep", "vlc"], check=True, capture_output=True)
                logging.info("VLC process found after using os.system")
            except subprocess.CalledProcessError:
                logging.error("VLC process not found after using os.system")
                raise Exception("Failed to start VLC")

        # Wait for the specified duration
        total_seconds = DAYS_TO_RUN * 24 * 3600
        logging.info(f"Waiting for {DAYS_TO_RUN} days ({total_seconds} seconds)")

        start_time = time.time()
        while time.time() - start_time < total_seconds:
            if process.poll() is not None:
                logging.error("VLC process ended unexpectedly")
                break
            time.sleep(60)  # Check every minute

        # Terminate VLC
        if process.poll() is None:
            logging.info("Attempting to terminate VLC process")
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                logging.warning("VLC process did not terminate, forcing kill")
                process.kill()

        # Capture any output for debugging
        stdout, stderr = process.communicate()
        if stdout:
            logging.info(f"VLC stdout: {stdout}")
        if stderr:
            logging.error(f"VLC stderr: {stderr}")

        actual_runtime = time.time() - start_time
        logging.info(f"Video played for {actual_runtime:.2f} seconds")

        # Clean up the converted file
        if converted_file_path != file_path:
            os.remove(converted_file_path)
            logging.info(f"Removed converted file: {converted_file_path}")

    except Exception as e:
        logging.error(f"An error occurred while playing the video: {e}")
        raise

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