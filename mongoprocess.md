# MongoDB Remote Access Setup

This guide explains how to set up a **Lenovo** machine as a MongoDB server and connect it from an **MSI** machine to retrieve data for an admin dashboard.

---

## **🔹 On Lenovo (MongoDB Server)**

### **1️⃣ Start MongoDB Server**
Ensure MongoDB is running. If not, start it manually:
```sh
mongod --port 27017 --bind_ip 0.0.0.0
```
✅ **MongoDB should now be running and accessible from other devices.**

---

### **2️⃣ Allow Remote Access (If Needed)**
If MSI is unable to connect, modify the MongoDB configuration:

- Open MongoDB config file (`mongod.conf`):  
  **Default path:** `C:\Program Files\MongoDB\Server\8.0\bin\mongod.cfg`

- Update the following lines:
  ```yaml
  net:
    bindIp: 0.0.0.0  # Allows access from any IP
    port: 27017
  ```

- Restart MongoDB to apply changes:
  ```sh
  net stop MongoDB
  net start MongoDB
  ```
✅ **MongoDB should now accept remote connections.**

---

### **3️⃣ Check Data Availability**
Verify MongoDB contains the required data:
```sh
mongosh
show dbs
use <your_database>  # Replace with actual database name
show collections
db.<your_collection>.find().pretty()
```
✅ **Ensure your data is present in the collection.**

---

### **4️⃣ Get Lenovo’s IP Address**
Find Lenovo's local IP address (CMD command):
```sh
ipconfig
```
✅ **Note the IPv4 Address (e.g., `10.15.46.85`) for connecting MSI.**

---

### **5️⃣ Keep MongoDB Running**
Ensure MongoDB stays active to allow MSI to fetch data.

---

## **🔹 On MSI (Client / Admin Dashboard)**

### **1️⃣ Install PyMongo**
Ensure **pymongo** is installed for connecting to MongoDB:
```sh
pip install pymongo
```
✅ **This allows MSI to communicate with MongoDB.**

---

### **2️⃣ Test MongoDB Connection from MSI**
Create a Python script (`test_connection.py`) and run it:
```python
from pymongo import MongoClient

# Connect to MongoDB on Lenovo
client = MongoClient("mongodb://10.15.46.85:27017/")  # Replace with Lenovo's IP

db_names = client.list_database_names()
print("Connected! Databases:", db_names)
```
✅ **If MSI prints the database names, connection is successful!**

---

### **3️⃣ Fetch Data from Lenovo**
Create `fetch_data.py`:
```python
from pymongo import MongoClient

client = MongoClient("mongodb://10.15.46.85:27017/")  # Replace with Lenovo's IP
db = client["your_database"]  # Replace with actual database name
collection = db["your_collection"]  # Replace with actual collection name

data = collection.find({}, {"_id": 0})  # Exclude MongoDB ObjectId
for doc in data:
    print(doc)
```
Run:
```sh
python fetch_data.py
```
✅ **If it prints MongoDB data, MSI is successfully retrieving it!**

---

### **4️⃣ Integrate Data into MSI Admin Dashboard**
#### **For Flask (If MSI Dashboard is Web-based)**
Modify `app.py` on MSI:
```python
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://10.15.46.85:27017/")  # Lenovo's IP
db = client["your_database"]
collection = db["your_collection"]

@app.route('/data', methods=['GET'])
def get_data():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```
Run:
```sh
python app.py
```
✅ **Now, access MSI’s API at:**  
📌 `http://<MSI-IP>:5000/data`

---

### **5️⃣ Fetch Data in MSI Admin Dashboard (Frontend)**
If MSI has a web dashboard, fetch data using **JavaScript**:
```javascript
fetch('http://<MSI-IP>:5000/data')
  .then(response => response.json())
  .then(data => console.log(data));
```
✅ **This ensures MSI’s dashboard displays MongoDB data.**

---

## **🎯 Final Verification**
✔ **MongoDB is running on Lenovo and accessible remotely.**  
✔ **MSI can connect and retrieve MongoDB data.**  
✔ **Admin dashboard displays MongoDB data successfully.**  

🚀 **Now, MSI successfully accesses MongoDB data from Lenovo!**  
Let me know if you need any modifications. 😊

