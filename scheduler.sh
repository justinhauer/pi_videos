#!/bin/bash

# Path to the Python script
PYTHON_SCRIPT="/path/to/your/slideshow_script.py"

# Function to run the slideshow
run_slideshow() {
    # Kill any existing Chromium processes
    pkill chromium

    # Run the Python script
    python "$PYTHON_SCRIPT"
}

# Run the slideshow immediately when the script is executed
run_slideshow

# Schedule the script to run every Saturday at 5 PM Central Time
(crontab -l 2>/dev/null; echo "0 17 * * 6 /bin/bash \"$(realpath "$0")\"") | crontab -


