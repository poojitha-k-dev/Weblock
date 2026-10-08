from flask import Flask, render_template, request, redirect, url_for, session
import json
from model.algorithm import (
    detect_brute_force,
    detect_suspicious_input,
    detect_unauthorized_ip,
    log_visitor_ip,
    verify_credentials,
    analyze_user_behavior,
    get_real_ip  
)
from trap import execute_traps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load JSON Data
def load_json(file_name):
    try:
        with open(f"model/{file_name}", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_approved_ips():
    return load_json("admin_settings.json").get("approved_ips", [])

def load_admin_users():
    return load_json("admin_settings.json").get("admin_users", [])

def load_dash_users():
    return load_json("admin_settings.json").get("dash_users", [])

@app.route('/')
def index():
    """Captures visitor IP and loads the login page."""
    user_ip = get_real_ip()  
    log_visitor_ip(user_ip)  
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Processes user login attempt while monitoring suspicious activity."""
    username = request.form.get('username', '')
    password = request.form.get('psw', '')
    user_ip = get_real_ip()  

    log_visitor_ip(user_ip)  
    approved_ips = load_approved_ips()
    admin_users = load_admin_users()
    dash_users = load_dash_users()

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
        return redirect(url_for('dashboard'))  

    if analysis_result["status"] == "login_restricted":
        return render_template('login.html', error="Error occurred, login restricted.")

    # Check if IP is Approved
    if user_ip in approved_ips:
        if verify_credentials(username, password):
            session['user'] = username
            return redirect(url_for('server'))  
        return render_template('login.html', error="Invalid credentials.")  

    # If IP is Not Approved But Credentials Are Correct, Restrict Login
    if verify_credentials(username, password):
        return render_template('login.html', error="Error occurred, login restricted.")

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
    if 'admin' in session:  
        return render_template('dashboard.html')

    execute_traps()  
    return render_template('dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    """Serves the Admin Dashboard (admindash.html)."""
    if 'dash_user' not in session:
        return redirect(url_for('index'))
    return render_template('admindash.html')  

@app.route('/logout')
def logout():
    """Logs out the user and redirects to login."""
    session.pop('user', None)
    session.pop('admin', None)
    session.pop('dash_user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
