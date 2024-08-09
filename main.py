import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
GOOGLE_SLIDES_URL: str = "https://docs.google.com/presentation"
USERNAME: str = "your_username"
PASSWORD: str = "your_password"
FOLDER_PATH: str = "/path/to/your/folder"
MAX_RUNTIME: timedelta = timedelta(days=2)


def login_to_google(driver):
    driver.get(GOOGLE_SLIDES_URL)

    # Wait for and fill in the username
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "identifierId"))
    )
    username_field.send_keys(USERNAME)
    driver.find_element(By.ID, "identifierNext").click()

    # Wait for and fill in the password
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    password_field.send_keys(PASSWORD)
    driver.find_element(By.ID, "passwordNext").click()


def get_latest_slide_deck(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith('.gdoc')]
    if not files:
        raise FileNotFoundError("No Google Slides files found in the specified folder.")
    return max(files, key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))


def play_slideshow(driver, file_path):
    # Open the file (you may need to adjust this part depending on how your files are organized)
    driver.get(f"file://{file_path}")

    # Wait for the presentation to load and start the slideshow
    start_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='Start slideshow']"))
    )
    start_button.click()


def run_slideshow():
    options = webdriver.ChromeOptions()
    options.add_argument("--kiosk")  # This will open Chrome in fullscreen mode
    driver: webdriver = webdriver.Chrome(options=options)

    try:
        login_to_google(driver)
        latest_deck = get_latest_slide_deck(FOLDER_PATH)
        play_slideshow(driver, os.path.join(FOLDER_PATH, latest_deck))

        start_time = datetime.now()
        while datetime.now() - start_time < MAX_RUNTIME:
            time.sleep(60)  # Check every minute if we've exceeded the max runtime

    finally:
        driver.quit()


if __name__ == "__main__":
    run_slideshow()
