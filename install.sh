#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root or with sudo."
    exit 1
fi

echo "Installing wget..."
apt-get install -y wget

echo "Installing tmate..."
apt-get install -y tmate

echo "Installing Python3 and pip3..."
apt-get update
apt-get install -y python3 python3-pip

echo "Installing dependencies..."
pip3 install requests==2.31.0 --break-system-packages

echo "Downloading tmate-service.py script..."
if wget -q https://raw.githubusercontent.com/AdeshSingh7/tmate/main/tmate-service.py -O /usr/bin/tmate-service; then
    echo "Downloaded tmate-service.py successfully."
else
    echo "Failed to download tmate-service.py."
    exit 1
fi

SERVICE_FILE_LOCATION="/etc/systemd/system/tmate.service"
TMATE_SERVICE_FILE="[Unit]
Description=Tmate Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/usr/bin/
ExecStart=/usr/bin/python3 /usr/bin/tmate-service
StandardOutput=file:/var/log/tmate_service.log
StandardError=file:/var/log/tmate_service.log
TimeoutStartSec=10s
TimeoutStopSec=10s
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
Alias=tmate.service"

if [ -f $SERVICE_FILE_LOCATION ]; then
    echo "Updating existing Tmate service file..."
    echo "$TMATE_SERVICE_FILE" > $SERVICE_FILE_LOCATION
else
    echo "Creating new Tmate service file..."
    echo "$TMATE_SERVICE_FILE" > $SERVICE_FILE_LOCATION
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Restarting Tmate service..."
sudo systemctl restart tmate.service

echo "Enabling Tmate service to start on boot..."
sudo systemctl enable tmate.service

echo "Tmate Service setup complete."
