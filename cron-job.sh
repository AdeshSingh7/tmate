#!/bin/bash

# Check if the script is run as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo" 
   exit 1
fi

# Download the tmate-service.py script
echo "Downloading tmate-service.py script..."
if wget -q https://raw.githubusercontent.com/AdeshSingh7/tmate/main/tmate-service.py -O /etc/tmate-service.py; then
    echo "Downloaded tmate-service.py successfully."
else
    echo "Failed to download tmate-service.py."
    exit 1
fi

# Define the cron job
CRON_JOB="* * * * * /usr/bin/python3 /etc/tmate-service.py"

# Get the current user's crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# Check if the cron job already exists
if echo "$CURRENT_CRONTAB" | grep -Fxq "$CRON_JOB"; then
    echo "Cron job already exists."
else
    # Add the cron job to the current crontab
    (echo "$CURRENT_CRONTAB"; echo "$CRON_JOB") | crontab -
    echo "Cron job added."
fi
