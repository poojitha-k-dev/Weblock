import json
import time
import re
import csv
import requests
import psutil
from datetime import datetime
from collections import defaultdict
from flask import request

# Load JSON Files
def load_json(file_name):
    """Loads JSON data from the model directory."""
    try:
        with open(f"model/{file_name}", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load Security Data
approved_devices = load_json("approved_ips.json").get("approved_devices", [])
authorized_users = load_json("data.json").get("users", [])
admin_users = load_json("admin_settings.json").get("admin_users", [])
bypass_users = load_json("admin_settings.json").get("bypass_access", [])  # ✅ Load Bypass Users
sql_patterns = load_json("sql_injection_patterns.json").get("patterns", [])
xss_patterns = load_json("xss_patterns.json").get("patterns", [])
brute_force_config = load_json("brute_force_patterns.json")

# Track Login Attempts Per IP
login_attempts = defaultdict(lambda: {"count": 0, "timestamps": []})

# CSV Log Files
CSV_FILE = "logs/intruder_log.csv"
LOGIN_LOG = "logs/login_log.csv"

# Ensure CSV Files Have Headers
def initialize_csv():
    """Creates CSV files with headers if they don't exist."""
    for file in [CSV_FILE, LOGIN_LOG]:
        try:
            with open(file, "r"):
                pass
        except FileNotFoundError:
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "IP", "MAC", "Reason"] if file == CSV_FILE else ["Timestamp", "IP", "MAC"])

# Capture MAC Address
def get_mac_address():
    """Retrieves the MAC address of the active network adapter."""
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK and addr.address and addr.address != "00:00:00:00:00:00":
                    return addr.address.upper()
        return "MAC Address Not Found"
    except Exception:
        return "MAC Address Not Found"

# Capture Real User IP and MAC Address
def get_real_ip_mac():
    """Retrieves the user's public IPv4 address and MAC address, avoiding local network IPs."""
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

        # Check for private/local IPs
        if client_ip.startswith(("127.", "192.168.", "10.", "172.")):
            response = requests.get("https://api64.ipify.org?format=json", timeout=5)
            client_ip = response.json().get("ip", "Unknown")

        mac = get_mac_address()
        print(f"[INFO] Captured IP: {client_ip}, MAC: {mac}")  # ✅ Console Log
        log_visitor_info(client_ip, mac)
        return client_ip, mac
    except Exception as e:
        print(f"Error fetching IP or MAC: {e}")
        return "Unknown", "Unknown"

# Log Visitor IPs and MAC
def log_visitor_info(ip, mac):
    """Logs real visitor IPs and MAC addresses, excluding localhost or private IPs."""
    if ip.startswith(("127.", "192.168.", "10.", "172.")) or ip == "Unknown":
        return  

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prevent duplicate logging
    try:
        with open(LOGIN_LOG, "r") as f:
            if any(ip in line and mac in line for line in f.readlines()):
                return  
    except FileNotFoundError:
        pass  

    # Log visitor IP and MAC
    with open(LOGIN_LOG, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, ip, mac])

# Verify Device Authorization
def is_device_authorized(ip, mac):
    """Checks if an IP and MAC address are authorized."""
    return any(device["ip_address"] == ip and device["mac_address"].upper() == mac.upper() for device in approved_devices)

# ✅ Verify Bypass Users (Allow Direct Entry)
def is_bypass_user(username, password):
    """Checks if the user is a bypass admin."""
    return any(user["username"] == username and user["password"] == password for user in bypass_users)

# Verify User Credentials
def verify_credentials(username, password):
    """Confirms if the username and password match stored user credentials."""
    return any(user["username"] == username and user["password"] == password for user in authorized_users)

# Verify Admin Access
def verify_admin_login(username):
    """Checks if the username belongs to an admin."""
    return any(admin["username"] == username for admin in admin_users)

# Analyze User Behavior
def analyze_user_behavior(username, password):
    """Evaluates user behavior and determines the appropriate response."""
    ip, mac = get_real_ip_mac()

    # ✅ Allow Bypass Admins Directly (No Device Authorization Check)
    if is_bypass_user(username, password):
        return {"status": "bypass_access"}  # ✅ Redirect to Dashboard

    if verify_admin_login(username):
        return {"status": "admin_access"}
    
    if is_device_authorized(ip, mac):
        return {"status": "clear"} if verify_credentials(username, password) else {"status": "invalid_credentials"}
    
    return {"status": "login_restricted"} if verify_credentials(username, password) else {"status": "intruder_detected"}

# Detect Brute-Force Attacks
def detect_brute_force(ip):
    """Monitors repeated login failures within a short time."""
    global login_attempts
    attempts = login_attempts[ip]
    attempts["timestamps"].append(time.time())
    attempts["count"] += 1

    # Remove timestamps older than the configured time window
    time_window = brute_force_config.get("time_window", 300)
    attempts["timestamps"] = [t for t in attempts["timestamps"] if time.time() - t < time_window]

    if attempts["count"] >= brute_force_config.get("max_attempts", 5):
        log_suspicious_activity(ip, "Brute-force Attack Detected")
        return True
    return False

# Detect SQL Injection & XSS Attacks
def detect_suspicious_input(ip, user_input):
    """Checks for SQL Injection and XSS attack patterns in user input."""
    if not isinstance(user_input, str):
        return False  

    for pattern in sql_patterns + xss_patterns:
        try:
            if re.search(pattern, user_input, re.IGNORECASE):
                log_suspicious_activity(ip, "Suspicious Input Detected")
                return True
        except re.error:
            print(f"Invalid regex pattern: {pattern}")
    return False

# Log Suspicious Activity
def log_suspicious_activity(ip, reason):
    """Records detected suspicious activities in the log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, ip, reason])
    print(f"[ALERT] {reason} from {ip}")

# Initialize CSV on Script Execution
if __name__ == "__main__":
    initialize_csv()