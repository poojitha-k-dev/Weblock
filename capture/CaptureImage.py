import cv2
import os
import time
from datetime import datetime

# Ensure the 'intruders' directory exists
INTRUDERS_DIR = "intruders"
if not os.path.exists(INTRUDERS_DIR):
    os.makedirs(INTRUDERS_DIR)

# Function to capture an image from the webcam
def capture_image(ip_address, max_retries=3, delay=1):
    for attempt in range(max_retries):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print(f"Error: Could not open the camera on attempt {attempt + 1}. Retrying...")
            time.sleep(delay)
            continue
        
        ret, frame = cap.read()
        if ret:
            # Create a unique filename with the IP address and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intruder_{ip_address.replace('.', '_')}_{timestamp}.jpg"
            
            # Save the image in the 'intruders' directory
            filepath = os.path.join(os.path.abspath(INTRUDERS_DIR), filename)
            cv2.imwrite(filepath, frame)  # Save the image
            print(f"Image saved as {filename} in {INTRUDERS_DIR}")
            cap.release()
            return filename  # Return the filename for logging purposes

        print(f"Failed to capture a frame on attempt {attempt + 1}. Retrying...")
        cap.release()
        time.sleep(delay)

    print("Error: Failed to capture an image after multiple retries.")
    return None  # Return None if capture fails after retries
