from pymongo import MongoClient
import json
import csv
import os
import base64

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "WebLock-db"  # Updated Database Name
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# MongoDB Collections
collections = {
    "intruder_logs": db["intruder_logs"],
    "employee_logs": db["employee_logs"],
    "keystrokes": db["keystrokes"],
    "screenshots": db["screenshots"],  # Storing binary screenshot data
    "captured_images": db["captured_images"]
}

# Paths to Files & Directories
LOGS_DIR = "logs"
CAPTURE_DIR = "Capture"
FILES = {
    "intruder_log": os.path.join(LOGS_DIR, "intruder_log.csv"),
    "employee_log": os.path.join(LOGS_DIR, "employee_log.csv"),
    "key_logs": os.path.join(LOGS_DIR, "key_logs.json"),
    "screenshots": os.path.join(CAPTURE_DIR, "screenshots"),  # Screenshot directory
    "intruder_images": os.path.join(CAPTURE_DIR, "intruder")  # Intruder images directory
}

# Ensure Directories Exist
for path in [LOGS_DIR, FILES["screenshots"], FILES["intruder_images"]]:
    os.makedirs(path, exist_ok=True)

# Function to Upload CSV Files to MongoDB
def upload_csv_to_mongodb(csv_file, collection):
    """Uploads CSV file data to MongoDB, avoiding duplicate inserts."""
    if not os.path.exists(csv_file):
        print(f"⚠ File not found: {csv_file}")
        return

    try:
        with open(csv_file, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            data = list(reader)
            
            if not data:
                print(f"⚠ No data in {csv_file}")
                return

            # Check for existing records to avoid duplicates
            existing_entries = set([entry["id"] for entry in collection.find({}, {"_id": 0, "id": 1}) if "id" in entry])
            new_entries = [entry for entry in data if entry.get("id") not in existing_entries]

            if new_entries:
                collection.insert_many(new_entries)
                print(f"✅ Uploaded {len(new_entries)} new records from {csv_file} to {collection.name}")
            else:
                print(f"⚠ No new data found in {csv_file}")
    except Exception as e:
        print(f"❌ Error uploading {csv_file}: {e}")

# Function to Upload Keystrokes from key_logs.json
def upload_keystrokes_to_mongodb():
    """Uploads key logs from key_logs.json to MongoDB."""
    if not os.path.exists(FILES["key_logs"]):
        print(f"⚠ File not found: {FILES['key_logs']}")
        return

    try:
        with open(FILES["key_logs"], "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            print("❌ Error: key_logs.json must be a dictionary with timestamps as keys.")
            return

        keystroke_entries = [{"timestamp": ts, "keystrokes": keys} for ts, keys in data.items() if isinstance(keys, list)]
        
        if not keystroke_entries:
            print("⚠ No valid keystroke data found.")
            return

        existing_timestamps = {entry["timestamp"] for entry in collections["keystrokes"].find({}, {"_id": 0, "timestamp": 1})}
        new_keystrokes = [entry for entry in keystroke_entries if entry["timestamp"] not in existing_timestamps]

        if new_keystrokes:
            collections["keystrokes"].insert_many(new_keystrokes)
            print(f"✅ Added {len(new_keystrokes)} new keystroke logs to MongoDB.")
        else:
            print("⚠ No new keystroke logs to add.")

    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in key_logs.json.")
    except Exception as e:
        print(f"❌ Error uploading keystrokes: {e}")

# Function to Upload Image Files as Binary Data to MongoDB
def upload_images_to_mongodb(image_dir, collection):
    """Uploads image files as binary data to MongoDB, avoiding re-inserts."""
    if not os.path.exists(image_dir):
        print(f"⚠ Directory not found: {image_dir}")
        return

    images = [img for img in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, img))]
    
    if not images:
        print(f"⚠ No images in {image_dir}")
        return

    try:
        existing_files = {entry["filename"] for entry in collection.find({}, {"_id": 0, "filename": 1})}
        new_images = []

        for img in images:
            if img in existing_files:
                continue  # Skip existing images
            
            img_path = os.path.join(image_dir, img)
            with open(img_path, "rb") as file:
                binary_data = file.read()

            new_images.append({"filename": img, "binary_data": binary_data})

        if new_images:
            collection.insert_many(new_images)
            print(f"✅ Uploaded {len(new_images)} images to {collection.name}")
        else:
            print(f"⚠ No new images to upload from {image_dir}")

    except Exception as e:
        print(f"❌ Error uploading images from {image_dir}: {e}")

# Data Retrieval Functions
def get_data(collection_name):
    """Retrieves data from a specified MongoDB collection."""
    return list(collections[collection_name].find({}, {"_id": 0}))

def get_images(collection_name):
    """Retrieves images from MongoDB and converts binary data to Base64."""
    images = collections[collection_name].find({}, {"_id": 0, "filename": 1, "binary_data": 1})
    return [{"filename": img["filename"], "binary_data": base64.b64encode(img["binary_data"]).decode('utf-8')} for img in images]

# Function to Upload All Data to MongoDB
def upload_all_data():
    print("\n🚀 Uploading data to MongoDB...\n")
    upload_csv_to_mongodb(FILES["intruder_log"], collections["intruder_logs"])
    upload_csv_to_mongodb(FILES["employee_log"], collections["employee_logs"])
    upload_keystrokes_to_mongodb()
    upload_images_to_mongodb(FILES["screenshots"], collections["screenshots"])  # Screenshot data as binary
    upload_images_to_mongodb(FILES["intruder_images"], collections["captured_images"])  # Intruder images as binary
    print("\n✅ Data upload complete!\n")

# Run When Executed
if __name__ == "__main__":
    upload_all_data()
