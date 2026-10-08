from pymongo import MongoClient
import csv
import os

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "weblock"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# MongoDB Collections
intruder_logs_collection = db["intruder_logs"]
employee_logs_collection = db["employee_logs"]
keystrokes_collection = db["keystrokes"]
screenshots_collection = db["screenshots"]
captured_images_collection = db["captured_images"]

# Paths to Files & Directories
INTRUDER_LOG_CSV = "intruder_log.csv"
EMPLOYEE_LOG_CSV = "employee_log.csv"
KEYSTROKE_FILE = "keylogger_logs/keystrokes.txt"
SCREENSHOT_DIR = "keylogger_logs/screenshots"
CAPTURED_IMAGE_DIR = "capture/intruders"

# Function to Upload CSV Files to MongoDB
def upload_csv_to_mongodb(csv_file, collection):
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return

    try:
        with open(csv_file, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            data = list(reader)

            if data:
                collection.delete_many({})  # Avoid duplicates by clearing old data
                collection.insert_many(data)
                print(f"Uploaded {len(data)} records from {csv_file} to {collection.name}")
            else:
                print(f"No data found in {csv_file}")

    except Exception as e:
        print(f"Error uploading {csv_file}: {e}")

# Function to Upload Keystrokes
def upload_keystrokes_to_mongodb():
    if not os.path.exists(KEYSTROKE_FILE):
        print(f"File not found: {KEYSTROKE_FILE}")
        return

    try:
        with open(KEYSTROKE_FILE, "r", encoding="utf-8") as file:
            keystrokes = file.readlines()

        keystroke_data = []
        for line in keystrokes:
            if " - " in line:
                timestamp, keystroke = line.strip().split(" - ", 1)
                keystroke_data.append({"timestamp": timestamp, "keystroke": keystroke})

        if keystroke_data:
            keystrokes_collection.delete_many({})
            keystrokes_collection.insert_many(keystroke_data)
            print(f"Uploaded {len(keystroke_data)} keystrokes to MongoDB.")
        else:
            print("No keystroke data found.")

    except Exception as e:
        print(f"Error uploading keystrokes: {e}")

# Function to Upload Images (Screenshots & Captured Images)
def upload_images_to_mongodb(image_dir, collection):
    if not os.path.exists(image_dir):
        print(f"Directory not found: {image_dir}")
        return

    images = [img for img in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, img))]
    
    if not images:
        print(f"No images found in {image_dir}")
        return

    try:
        collection.delete_many({})  # Clear old images
        for image in images:
            image_path = os.path.join(image_dir, image)
            with open(image_path, "rb") as file:
                image_data = file.read()

            collection.insert_one({
                "filename": image,
                "image_data": image_data
            })
        
        print(f"Uploaded {len(images)} images to MongoDB from {image_dir}")

    except Exception as e:
        print(f"Error uploading images from {image_dir}: {e}")

# Function to Retrieve Data for app.py
def get_intruder_logs():
    return list(intruder_logs_collection.find({}, {"_id": 0}))

def get_employee_logs():
    return list(employee_logs_collection.find({}, {"_id": 0}))

def get_keystrokes():
    return list(keystrokes_collection.find({}, {"_id": 0}))

def get_screenshots():
    return list(screenshots_collection.find({}, {"_id": 0, "filename": 1}))

def get_captured_images():
    return list(captured_images_collection.find({}, {"_id": 0, "filename": 1}))

# Function to Initialize Data Upload to MongoDB
def upload_all_data():
    print("\nUploading data to MongoDB...\n")
    upload_csv_to_mongodb(INTRUDER_LOG_CSV, intruder_logs_collection)
    upload_csv_to_mongodb(EMPLOYEE_LOG_CSV, employee_logs_collection)
    upload_keystrokes_to_mongodb()
    upload_images_to_mongodb(SCREENSHOT_DIR, screenshots_collection)
    upload_images_to_mongodb(CAPTURED_IMAGE_DIR, captured_images_collection)
    print("\nData upload complete!\n")

# Run when executed
if __name__ == "__main__":
    upload_all_data()
