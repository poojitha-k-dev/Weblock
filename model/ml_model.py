import os
import pandas as pd
import numpy as np
import joblib
import json
import datetime
import geoip2.database
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sklearn.ensemble import IsolationForest
from PIL import Image
from reportlab.lib.utils import ImageReader
import gridfs

# Load necessary files
LOGIN_LOG_FILE = "logs/login_logs.csv"
INTRUDER_LOG_FILE = "logs/intruder_log.csv"
EMPLOYEE_LOG_FILE = "logs/employee_log.csv"
BLOCKED_IP_FILE = "data/blocked_ips.json"
VPN_PROVIDERS = "data/vpn_providers.json"
MONGO_URI = "mongodb://localhost:27017/"

client = MongoClient(MONGO_URI)
db = client["security_dashboard"]
fs = gridfs.GridFS(db)

# Ensure required directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("captures", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("visuals", exist_ok=True)

# Train ML Model
def train_anomaly_model():
    try:
        df = pd.read_csv("data/login_activity.csv")
        if df.empty:
            print("Training data is empty. Skipping model training.")
            return

        model = IsolationForest(contamination=0.02, random_state=42)
        model.fit(df.drop(columns=['user_id', 'timestamp'], errors='ignore'))
        joblib.dump(model, "models/anomaly_detector.pkl")
        print("Anomaly detection model trained and saved.")
    except FileNotFoundError:
        print("Training data file not found. Ensure 'data/login_activity.csv' exists.")
    except Exception as e:
        print(f"Error training model: {e}")

# Detect anomalies
def detect_anomaly(data):
    try:
        model_path = "models/anomaly_detector.pkl"
        if not os.path.exists(model_path):
            print("Anomaly detection model not found. Train the model first.")
            return False

        model = joblib.load(model_path)
        df = pd.DataFrame([data])

        if df.empty:
            print("Empty data for anomaly detection.")
            return False

        return model.predict(df)[0] == -1
    except Exception as e:
        print(f"Error detecting anomaly: {e}")
        return False

# VPN Detection
def is_vpn(ip_address):
    try:
        reader = geoip2.database.Reader("GeoLite2-City.mmdb")
        response = reader.city(ip_address)
        isp = getattr(response.traits, 'isp', '')

        if not os.path.exists(VPN_PROVIDERS):
            print("VPN provider file missing. Skipping VPN check.")
            return False

        with open(VPN_PROVIDERS, "r") as file:
            vpn_list = json.load(file)

        return isp in vpn_list
    except Exception as e:
        print(f"VPN check error: {e}")
        return False

# Update Employee Logs
def update_employee_log(user_id, ip_address):
    try:
        if not os.path.exists(EMPLOYEE_LOG_FILE):
            df = pd.DataFrame(columns=['user_id', 'last_login', 'last_ip'])
            df.to_csv(EMPLOYEE_LOG_FILE, index=False)

        df = pd.read_csv(EMPLOYEE_LOG_FILE)

        if user_id not in df["user_id"].values:
            new_entry = pd.DataFrame([[user_id, datetime.datetime.now(), ip_address]], 
                                     columns=['user_id', 'last_login', 'last_ip'])
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df.loc[df['user_id'] == user_id, ['last_login', 'last_ip']] = [datetime.datetime.now(), ip_address]

        df.to_csv(EMPLOYEE_LOG_FILE, index=False)
    except Exception as e:
        print(f"Error updating employee logs: {e}")

# Generate Attack Report
def generate_attack_report(intruder_data):
    try:
        report_file = f"reports/report_{intruder_data['ip']}.pdf"
        c = canvas.Canvas(report_file, pagesize=letter)
        c.drawString(100, 750, "Security Incident Report")
        c.drawString(100, 730, f"Date: {intruder_data['date']}")
        c.drawString(100, 710, f"IP Address: {intruder_data['ip']}")
        c.drawString(100, 690, f"Location: {intruder_data['location']}")
        c.drawString(100, 670, f"Type of Attack: {intruder_data['attack_type']}")

        image_path = f"captures/{intruder_data['ip']}.jpg"
        if os.path.exists(image_path):
            img = ImageReader(image_path)
            c.drawImage(img, 400, 650, width=100, height=100)
        else:
            print("No attacker image found.")

        c.save()
        return report_file
    except Exception as e:
        print(f"Error generating attack report: {e}")
        return None

# Block Suspicious IPs
def block_ip(ip):
    try:
        if not os.path.exists(BLOCKED_IP_FILE):
            with open(BLOCKED_IP_FILE, "w") as file:
                json.dump([], file)

        with open(BLOCKED_IP_FILE, "r+") as file:
            blocked_ips = json.load(file)
            if ip not in blocked_ips:
                blocked_ips.append(ip)
                file.seek(0)
                json.dump(blocked_ips, file)
                print(f"IP {ip} blocked.")
    except Exception as e:
        print(f"Error blocking IP: {e}")

# Real-time Visualization
def update_visuals():
    try:
        df = pd.read_csv(LOGIN_LOG_FILE)
        if df.empty:
            print("No login data to visualize.")
            return

        plt.figure(figsize=(10,5))
        sns.countplot(data=df, x="result")
        plt.title("Login Success vs Failure")

        image_path = "visuals/login_attempts.png"
        plt.savefig(image_path)

        with open(image_path, "rb") as img:
            file_id = fs.put(img, filename="login_attempts.png")
        
        db.visuals.insert_one({"type": "login_attempts", "file_id": file_id})
        print("Visualization updated.")
    except Exception as e:
        print(f"Error updating visuals: {e}")

# Monitor Login Activity
def monitor_logins():
    try:
        df = pd.read_csv(LOGIN_LOG_FILE)
        if df.empty:
            print("No login data available.")
            return

        for _, row in df.iterrows():
            if is_vpn(row["ip"]):
                print(f"VPN detected for IP: {row['ip']}")

            data = row.drop(columns=["user_id", "timestamp"], errors="ignore").to_dict()
            if detect_anomaly(data):
                print(f"Anomaly detected for IP: {row['ip']}")
                block_ip(row["ip"])
                db.alerts.insert_one({"ip": row["ip"], "message": "Suspicious activity detected"})
    except Exception as e:
        print(f"Error monitoring logins: {e}")

if __name__ == "__main__":
    train_anomaly_model()
    monitor_logins()
    update_visuals()
