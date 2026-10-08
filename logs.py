import os
import csv

# Define the log file path
log_file_path = 'logs/login_logs.csv'

# Check if the file exists
if not os.path.exists(log_file_path):
    # Create the file and write headers
    with open(log_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Add header row
        writer.writerow(['IP', 'MAC', 'Timestamp'])
    print(f'{log_file_path} created successfully.')
else:
    print(f'{log_file_path} already exists.')
