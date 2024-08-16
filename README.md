# Raspberry Pi Video Auto Play

## Summary
- This repository houses code intended to upload to a Raspberry Pi. 
- Once the code is uploaded to the raspberry pi, the code will:
  - Pull the latest Google slides document (a slide deck like powerpoint) from Google drive
  - Play the slide deck for a designated period of time (set to run for 6 days)
  - Once the number of days has been reached, the slide deck will stop running (Runs in Libre Office)
  - The slide deck downloaded from Google Drive will be deleted from the local storage on the Raspberry Pi to preserve disk space

## File Outline

### main.py

- Run the program 
- 
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
- Click "Create Credentials" and choose "OAuth client ID".

### Configure the OAuth consent screen:

- If prompted, select "External" or "Internal" based on your use case.
- Fill in the required information like app name, user support email, etc.
- Add the necessary scopes for Google Drive API access.


### Choose the application type:

- Select the type that best fits your needs (e.g., Web application, Desktop app, etc.).

### Set up the OAuth client:

- For a web application, add authorized JavaScript origins and redirect URIs.
- For a desktop app, you might not need to add any URIs.


### Download the credentials:

- After creating the client ID, you'll be able to download a JSON file containing your credentials.
- Use the credentials in your application:
- Implement the OAuth 2.0 flow in your application using these credentials to authenticate and authorize access to the Google Drive API.
- Remember to keep your credentials secure and never share them publicly. Also, make sure to comply with Google's API usage policies and terms of service.
