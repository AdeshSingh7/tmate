#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root or with sudo."
    exit 1
fi

echo "Updating package lists..."
apt-get update

echo "Installing wget..."
apt-get install -y wget

echo "Installing tmate..."
apt-get install -y tmate

echo "Installing Python3 and pip3..."
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
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/usr/bin
ExecStart=/usr/bin/python3 -u /usr/bin/tmate-service
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=20

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
