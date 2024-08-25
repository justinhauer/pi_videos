# Raspberry Pi Video Auto Play

## Summary
- This repository houses code intended to upload to a Raspberry Pi. 
- Once the code is uploaded to the raspberry pi, the code will:
  - Pull the latest Google slides document (a slide deck like powerpoint) from Google drive in a designated folder
  - Play the slide deck for a designated period of time (set to run for 6 days)
  - Once the number of days has been reached, the slide deck will stop running (Runs in Libre Office)
  - The slide deck downloaded from Google Drive will be deleted from the local storage on the Raspberry Pi to preserve disk space

## File Outline

### main.py

- Runs the program (runs on a schedule) 
- Can be manually executed by opening the `terminal` program on the raspberry pi desktop, navigating to the program and running `python main.py`
### Credientials.json
- Stores credentials to authenticate to google apis

### Requirements.txt
- Lists python library dependencies and versions

### Scheduler.sh and clean_up.sh
- Scheduler.sh schedules the program to run
- Cleanup.sh removes and deletes files downloaded

### test_main.py
- Unit tests to test the code

## How to obtain API Credentials to authenticate to Google Drive api

- API stands for Application Programming Interface. It is a way to interact with things without a user interface
- To create API credentials for calling the Google Drive API with your Google account, follow these steps:

Go to the Google Cloud Console (https://console.cloud.google.com/).
Create a new project or select an existing one.
Enable the Google Drive API:

In the dashboard, click on "Enable APIs and Services".
Search for "Google Drive API" and select it.
Click "Enable" if it's not already enabled.


### Create credentials:

- In the left sidebar, click on "Credentials".
- Create a service account and utilize the service account credentials to authenticate to google

## Raspberry pi setup

### Downloading the Operating system
The easiest way to set up a raspberry pi is to go to the website and download the imager [here](https://www.raspberrypi.com/software/)
- If Using a raspberry pi 3b, choose an `arm 32 bit` operating system image, choose raspbian. If choosing a raspberry pi 4 or newer, choose 64 bit
- Install the software to a micro-sd card
- Once installed, insert the card into the raspberry pi and plug it in to a monitor, keyboard, mouse, and power adapter

### Set up necessary software once the Operating system is up and running
- Install all necessary software updates to the computer. There should be a prompt to do this through the UI. If not, go to terminal and type `apt-get update -y && apt-get upgrade -y`
- Open a terminal and type the command `apt-get install libreoffice -y`, hit enter and yes through any prompts that come up. Libre Office is a free office software used to play slide decks
- Go to this github repository and download the files. The easiest way to do so will be it utilize git if you are familiar with git. If not, download the zip file onto the raspberry pi. unzip the file contents and place the files in a folder

## Configuring the program and running on a schedule

### Configuring the main.py file

You will see a file named main.py, within the files you downloaded from this location in github. Open this file (under programming in the desktop, an programming editor is bundled) and modify the value of the variable `GOOGLE_DRIVE_FOLDER_ID:` with the ID of the folder where we will pull down files from google drive. 
- To find the ID of the folder you want to place slide decks in, go to your folder in google drive, and find the ending characters in the URL path within your web browser, this is the folder ID
- Modify the `DAYS_TO_RUN` variable if the desired length to play the slideshow is something different than 6 days

### Scheduling the program to run
- Open the scheduler.sh file
  - Modify the path to the main.py file to where it has been placed on the filesystem. Save and exit
  - Go to the terminal and type `crontab -e`. If using `vi` hit the `i` key, this will open an editor, type the following: `0 20 * * 6 /path/to/scheduler.sh` which will schedule the program to run on a cadence. modify the path to the file to where the file is on the filesystem and to be called main.py
  - hit escape, then type `:wq!` which will save and exit

### Obtaining credentials to authenticate to google drive
- Go to google and search `google cloud console`, navigate to the google cloud console and create a service account. please look up instructions for this as this could change and this document will not be updated.
- Once a service account is created, obtain the `.json` file with credentials, and modify the value of this on the `credientials.json` file on the raspberry pi. once done the program should be set to go.


