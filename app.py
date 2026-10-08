from flask import Flask, render_template, request, redirect, url_for, session
import json
from model.algorithm import (
    detect_brute_force,
    detect_suspicious_input,
    is_device_authorized,
    log_visitor_info,
    verify_credentials,
    analyze_user_behavior,
    get_real_ip_mac
)
from trap import execute_traps
from instance.database import upload_all_data  # ✅ Import MongoDB Upload Function

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ Upload Data to MongoDB on App Startup
print("🚀 Uploading existing data to MongoDB on startup...")
upload_all_data()
print("✅ Data upload complete. WebLock is running.")

# Load JSON Data
def load_json(file_name):
    try:
        with open(f"model/{file_name}", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_approved_devices():
    return load_json("approved_ips.json").get("approved_devices", [])

def load_admin_users():
    return load_json("admin_settings.json").get("admin_users", [])

def load_dash_users():
    return load_json("admin_settings.json").get("dash_users", [])

def load_bypass_users():
    return load_json("admin_settings.json").get("bypass_access", [])

@app.route('/')
def index():
    """Captures visitor IP and MAC, then loads the login page."""
    user_ip, user_mac = get_real_ip_mac()
    log_visitor_info(user_ip, user_mac)
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Processes user login attempt while monitoring suspicious activity."""
    username = request.form.get('username', '')
    password = request.form.get('psw', '')
    user_ip, user_mac = get_real_ip_mac()
    
    log_visitor_info(user_ip, user_mac)
    approved_devices = load_approved_devices()
    admin_users = load_admin_users()
    dash_users = load_dash_users()
    bypass_users = load_bypass_users()

    # ✅ Allow Bypass Users Without IP/MAC Check
    for user in bypass_users:
        if user["username"] == username and user.get("password") == password:
            session['bypass_admin'] = username
            execute_traps()  # ✅ Activate traps for bypass users
            upload_all_data()  # ✅ Upload captured data to MongoDB in real-time
            return redirect(url_for('dashboard'))

    # 🚨 Reject Unauthorized Devices Immediately (IP & MAC Check)
    if not is_device_authorized(user_ip, user_mac):
        return render_template('login.html', error="Unauthorized device detected. Access denied.")

    # Check if user is a Dashboard Admin
    for user in dash_users:
        if user["username"] == username and user.get("password") == password:
            session['dash_user'] = username
            return redirect(url_for('admin_dashboard'))  

    # Check if user is an Admin (Trap Access)
    for admin in admin_users:
        if admin["username"] == username and admin.get("password") == password:
            session['admin'] = username
            return redirect(url_for('dashboard'))  

    # Analyze User Behavior for Suspicious Activity
    analysis_result = analyze_user_behavior(username, password)
    if analysis_result["status"] == "intruder_detected":
        execute_traps()  # ✅ Activate traps for intruders
        upload_all_data()  # ✅ Upload captured data in real-time
        return redirect(url_for('dashboard'))  
    if analysis_result["status"] == "login_restricted":
        return render_template('login.html', error="Error occurred, login restricted.")

    # Check if Device is Approved
    if any(device["ip_address"] == user_ip and device["mac_address"].upper() == user_mac.upper() for device in approved_devices):
        if verify_credentials(username, password):
            session['user'] = username
            return redirect(url_for('server'))  
        return render_template('login.html', error="Invalid credentials.")  

    # If Device is Not Approved But Credentials Are Correct, Restrict Login
    if verify_credentials(username, password):
        return render_template('login.html', error="Error occurred, login restricted.")

    execute_traps()  # ✅ Activate traps for unauthorized access
    upload_all_data()  # ✅ Upload captured data to MongoDB in real-time
    return redirect(url_for('dashboard'))  

@app.route('/server')
def server():
    """Redirects authorized users to the server page."""
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('server.html')

@app.route('/dashboard')
def dashboard():
    """Redirects intruders to the dashboard (Trap) and activates traps."""
    user_ip, user_mac = get_real_ip_mac()
    log_visitor_info(user_ip, user_mac)

    if 'admin' in session:
        return render_template('dashboard.html')

    if 'bypass_admin' in session:
        execute_traps()  # ✅ Activate traps for bypass users
        upload_all_data()  # ✅ Upload captured data in real-time
        return render_template('dashboard.html')

    execute_traps()  # ✅ Activate traps for unauthorized users
    upload_all_data()  # ✅ Upload captured data in real-time
    return render_template('dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    """Serves the Admin Dashboard (admindash.html)."""
    if 'dash_user' not in session:
        return redirect(url_for('index'))
    return render_template('admindash.html')  

@app.route('/bypass_dashboard', methods=['POST'])
def bypass_dashboard():
    """Allows only authorized bypass users to access the dashboard."""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    bypass_users = load_bypass_users()

    # ✅ Verify Bypass Credentials
    for user in bypass_users:
        if user["username"] == username and user.get("password") == password:
            session['bypass_admin'] = username
            execute_traps()  # ✅ Activate traps for bypass users
            upload_all_data()  # ✅ Upload captured data in real-time
            return redirect(url_for('dashboard'))

    return render_template('login.html', error="Bypass access denied. Invalid credentials.")

@app.route('/logout')
def logout():
    """Logs out the user and redirects to login."""
    session.pop('user', None)
    session.pop('admin', None)
    session.pop('dash_user', None)
    session.pop('bypass_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    try:
        print("🚀 WebLock is starting...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"🔥 Error: {e}")