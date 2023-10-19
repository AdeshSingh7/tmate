#!/bin/bash

# Configuration
TMATE_SOCKET="/tmp/.public-session.sock"
API_ENDPOINT="http://pms.parkmate.in:9001/api/tmate"
SLEEP_INTERVAL_SECONDS=10  # Set the time interval in seconds

# Function to get the first username in /home/ directory
get_username() {
  local username
  for user in /home/*; do
    if [ -d "$user" ]; then
      username=$(basename "$user")
      echo "$(echo $username | sed 's/./\U&/')"
      return 0
    fi
  done
  echo "unknown"
}

# Function to get the MAC address
get_mac_address() {
  local interface_name
  interface_name=$(ip link show | awk '/^[0-9]+: [eE]/{gsub(/:/, "", $2); print $2; exit}') # Get the interface name
  local mac_address
  mac_address=$(ip link show "$interface_name" | awk '/link\/ether/ {print $2}') # Get MAC address for the interface
  if [ -n "$mac_address" ]; then
    echo "$mac_address"
  else
    echo "MAC address not found for interface: $interface_name"
  fi
}

# Function to check internet connectivity
check_internet() {
  if ping -q -c 2 8.8.8.8 > /dev/null 2>&1; then
    echo "Internet is reachable."
    return 0  # Internet is reachable
  else
    echo "Internet is not reachable."
    return 1  # Internet is not reachable
  fi
}

# Function to install tmate if not installed
install_tmate() {
  if ! command -v tmate &> /dev/null; then
    echo "Installing tmate..."
    sudo apt-get update
    sudo apt-get install -y tmate
    echo "tmate has been installed."
  else
    echo "tmate is already installed."
  fi
}

# Function to check if tmate session is running
check_tmate_session() {
  if [ -S "$TMATE_SOCKET" ]; then
    echo "Tmate session is running."
    return 0
  else
    echo "Tmate session is not running."
    return 1
  fi
}

# Function to create a new tmate session
create_new_tmate_session() {
  echo "Creating a new tmate session..."
  if tmate -S "$TMATE_SOCKET" new-session -d && tmate -S "$TMATE_SOCKET" wait tmate-ready; then
    echo "Tmate session created successfully"
  else
    echo "Failed to create tmate session."
    exit 1
  fi
}

# Function to send session data to API with retry
send_data_to_api() {
  local mac_address="$1"
  local username="$2"
  local session="$3"
  local max_retries=3
  local retries=0
  local json_data='{"mac_address": "'"$mac_address"'", "username": "'"$username"'", "session": "'"$session"'"}'
  echo "Sending data to API..."
  while [ $retries -lt $max_retries ]; do
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$json_data" "$API_ENDPOINT")
    if [ "$response" -eq 200 ]; then
      echo "Data sent successfully!"
      return 0
    else
      echo "Failed to send data to API. HTTP Status Code: $response"
      retries=$((retries+1))
      sleep 5  # Wait for 5 seconds before retrying
    fi
  done
  echo "Failed to send data to API after $max_retries attempts. Exiting."
  exit 1
}

# Main loop
while true; do
  if check_internet; then
    install_tmate
    if ! check_tmate_session; then
      create_new_tmate_session
    fi
  fi

  # Run send_data_to_api every 1 minute (60 seconds)
  sleep $SLEEP_INTERVAL_SECONDS

  # Call send_data_to_api function here
  mac_address=$(get_mac_address)
  username=$(get_username)
  tmate_ssh_address=$(tmate -S "$TMATE_SOCKET" display -p '#{tmate_ssh}')
  send_data_to_api "$mac_address" "$username" "$tmate_ssh_address"
done
