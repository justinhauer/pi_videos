#!/bin/bash

# Path to the log file
LOG_FILE="/path/to/your/logfile.log"

# Remove logs older than 7 days
find $LOG_FILE -type f -mtime +7 -delete

# Alternatively, if you want to keep the file but clear its contents:
# truncate -s 0 $LOG_FILE