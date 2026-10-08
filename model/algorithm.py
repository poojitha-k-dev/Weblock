import json
import time
import re
import csv
import requests
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
approved_ips = load_json("approved_ips.json").get("approved_ips", [])
authorized_users = load_json("data.json").get("users", [])
admin_users = load_json("admin_settings.json").get("admin_users", [])
sql_patterns = load_json("sql_injection_patterns.json").get("patterns", [])
xss_patterns = load_json("xss_patterns.json").get("patterns", [])
brute_force_config = load_json("brute_force_patterns.json")

# Track Login Attempts Per IP
login_attempts = defaultdict(lambda: {"count": 0, "timestamps": []})

# CSV Log Files
CSV_FILE = "intruder_log.csv"
LOGIN_LOG = "login_log.csv"

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
                writer.writerow(["Timestamp", "IP", "Reason"] if file == CSV_FILE else ["Timestamp", "IP"])

# Capture Real User IP
def get_real_ip():
    """Retrieves the user's public IPv4 address, avoiding local network IPs."""
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

        # Check for private/local IPs
        if client_ip.startswith(("127.", "192.168.", "10.", "172.")):
            print(f"Detected local IP ({client_ip}), fetching public IP...")
            response = requests.get("https://api64.ipify.org?format=json", timeout=5)
            client_ip = response.json().get("ip", "Unknown")

        print(f"Captured Public IPv4: {client_ip}")
        log_visitor_ip(client_ip)
        return client_ip
    except Exception as e:
        print(f"Error fetching IP: {e}")
        return "Unknown"

# Log Visitor IPs
def log_visitor_ip(ip):
    """Logs real visitor IPs, excluding localhost or private IPs."""
    if ip.startswith(("127.", "192.168.", "10.", "172.")) or ip == "Unknown":
        return  

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Prevent duplicate logging
    try:
        with open(LOGIN_LOG, "r") as f:
            if any(ip in line for line in f.readlines()):
                return  
    except FileNotFoundError:
        pass  

    # Log visitor IP
    with open(LOGIN_LOG, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, ip])

# Log Suspicious Activity
def log_suspicious_activity(ip, reason):
    """Records detected suspicious activities in the log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, ip, reason])
    print(f"[ALERT] {reason} from {ip}")

# Detect Unauthorized IPs
def detect_unauthorized_ip(ip):
    """Checks if an IP is unauthorized."""
    return ip not in approved_ips

# Detect Brute-Force Attacks
def detect_brute_force(ip):
    """Monitors repeated login failures within a short time."""
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

# Verify User Credentials
def verify_credentials(username, password):
    """Confirms if the username and password match stored user credentials."""
    return any(user["username1"] == username and user["password1"] == password for user in authorized_users)

# Verify Admin Access
def verify_admin_login(username):
    """Checks if the username belongs to an admin."""
    return any(admin["username"] == username for admin in admin_users)

# Analyze User Behavior
def analyze_user_behavior(username, password):
    """Evaluates user behavior and determines the appropriate response."""
    ip = get_real_ip()  

    # If an admin logs in, grant access to the trap
    if verify_admin_login(username):
        return {"status": "admin_access"}

    # If the IP is approved, allow login if credentials are correct
    if ip in approved_ips:
        return {"status": "clear"} if verify_credentials(username, password) else {"status": "invalid_credentials"}

    # If the IP is unauthorized
    if detect_unauthorized_ip(ip):
        return {"status": "login_restricted"} if verify_credentials(username, password) else {"status": "intruder_detected"}

    # Check for suspicious input
    if detect_suspicious_input(ip, username) or detect_suspicious_input(ip, password):
        return {"status": "intruder_detected"}

    return {"status": "clear"}  

# Initialize CSV on Script Execution
if __name__ == "__main__":
    initialize_csv()
