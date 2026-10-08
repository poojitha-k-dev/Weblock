import smtplib
import time
import psutil
import json
import os
import pymongo
import glob
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pymongo import MongoClient
from fpdf import FPDF

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["WebLock-db"]
network_collection = db["network_logs"]
report_collection = db["attack_reports"]

# Email Setup
sender_email = "sentinels1825@gmail.com"
receiver_email = "sentinels1825@gmail.com"
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_password = "czoi adum duzn zijm"  # Replace with your App Password

# Ensure 'reports/' directory exists
os.makedirs("reports", exist_ok=True)

# Path for intruder logs and images
intruder_log_path = "logs/intruder_log.csv"
intruder_image_path = "Capture/intruder/"


# Function to get network traffic data
def get_network_traffic():
    traffic_data = psutil.net_io_counters()
    return {
        "bytes_sent": traffic_data.bytes_sent,
        "bytes_recv": traffic_data.bytes_recv,
        "packets_sent": traffic_data.packets_sent,
        "packets_recv": traffic_data.packets_recv,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# Function to fetch latest intruder details from CSV
def get_latest_intruder_data():
    if os.path.exists(intruder_log_path):
        df = pd.read_csv(intruder_log_path)
        if not df.empty:
            latest_intruder = df.iloc[-1].to_dict()
            return latest_intruder
    return None


# Function to fetch latest intruder image
def get_latest_intruder_image():
    image_files = glob.glob(os.path.join(intruder_image_path, "*.jpg"))  # Assuming images are stored as .jpg
    if image_files:
        latest_image = max(image_files, key=os.path.getctime)
        return latest_image
    return None


# Insert network data into MongoDB
def insert_network_data_to_mongo(network_data):
    try:
        network_collection.insert_one(network_data)
        print(f"✅ Network data inserted at {network_data['timestamp']}")
    except Exception as e:
        print(f"❌ Error inserting network data: {e}")


# Generate PDF Report with intruder details and image
def generate_pdf_report(network_data, intruder_data, intruder_image):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"reports/Network_Report_{timestamp}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "WebLock Security Report", ln=True, align="C")

    # Network Data
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Network Traffic Data:", ln=True)
    pdf.set_font("Arial", size=12)
    for key, value in network_data.items():
        pdf.cell(200, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Intruder Data
    if intruder_data:
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Intruder Details:", ln=True)
        pdf.set_font("Arial", size=12)
        for key, value in intruder_data.items():
            pdf.cell(200, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Attach intruder image
    if intruder_image:
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Intruder Image:", ln=True)
        pdf.image(intruder_image, x=50, y=None, w=100)  # Adjust position & size

    # Save PDF
    pdf.output(report_filename)
    print(f"📄 Report saved: {report_filename}")

    # Store report metadata in MongoDB
    report_collection.insert_one({
        "report_filename": report_filename,
        "generated_at": network_data["timestamp"],
        "network_data": network_data,
        "intruder_data": intruder_data,
    })
    print("✅ Report details saved to MongoDB.")

    return report_filename


# Send Email with Report Attachment
def send_attack_email(report_filename):
    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "🚨 Alert: Attack Detected on WebLock"

        body = MIMEText(
            f"An attack is currently happening on WebLock.\n\n"
            f"🕒 Time of Detection: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⚠️ Type: Suspicious Activity Detected\n\n"
            f"Please find the attached report for details.",
            "plain",
        )
        message.attach(body)

        # Attach the report file
        with open(report_filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename={os.path.basename(report_filename)}"
            )
            message.attach(part)

        # Sending email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, email_password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        print("✅ Attack email with report sent successfully.")

    except Exception as e:
        print(f"❌ Error sending attack email: {e}")


# Main Execution Loop (Runs Every 10 Minutes)
def main():
    while True:
        network_data = get_network_traffic()
        insert_network_data_to_mongo(network_data)

        intruder_data = get_latest_intruder_data()
        intruder_image = get_latest_intruder_image()

        report_filename = generate_pdf_report(network_data, intruder_data, intruder_image)

        send_attack_email(report_filename)

        print("⏳ Waiting for 10 minutes before next execution...")
        time.sleep(600)  # Run every 10 minutes


if __name__ == "__main__":
    main()
