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