document.querySelector('.toggle-btn').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
});

// Function to load data dynamically based on sidebar selection
function loadContent(section) {
    let contentContainer = document.querySelector("#content-area");
    let imagePreviewSection = document.querySelector("#image-preview-section");

    contentContainer.innerHTML = `<h2>Loading...</h2>`;
    imagePreviewSection.style.display = "none"; // Hide image preview unless required

    switch (section) {
        case "home":
            contentContainer.innerHTML = `<h2>Welcome to WebLock Dashboard</h2><p>Select a section from the sidebar to view logs and captured data.</p>`;
            break;
        case "intruder-logs":
            fetchData("/api/intruder_logs", renderIntruderLogs);
            break;
        case "employee-logs":
            fetchData("/api/employee_logs", renderEmployeeLogs);
            break;
        case "keystroke-logs":
            fetchData("/api/keystrokes", renderKeystrokes);
            break;
        case "screenshot-logs":
            fetchData("/api/screenshots", renderScreenshots);
            break;
        case "captured-images":
            fetchData("/api/captured_images", renderCapturedImages);
            break;
        default:
            contentContainer.innerHTML = `<h2>Error</h2><p>Invalid selection.</p>`;
            break;
    }
}

// Fetch Data from API
function fetchData(endpoint, callback) {
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.querySelector("#content-area").innerHTML = "<h2>No data available.</h2>";
            } else {
                callback(data);
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            document.querySelector("#content-area").innerHTML = `<h2>Error loading data.</h2>`;
        });
}

// Render Intruder Logs Table
function renderIntruderLogs(data) {
    let html = `<h2>Intruder Logs</h2><table><tr><th>IP</th><th>Timestamp</th><th>Action</th></tr>`;
    data.forEach(log => {
        html += `<tr><td>${log.IP}</td><td>${log.timestamp}</td><td>${log.action}</td></tr>`;
    });
    html += `</table>`;
    document.querySelector("#content-area").innerHTML = html;
}

// Render Employee Logs Table
function renderEmployeeLogs(data) {
    let html = `<h2>Employee Logs</h2><table><tr><th>Name</th><th>Device</th><th>IP Address</th><th>Status</th></tr>`;
    data.forEach(log => {
        html += `<tr><td>${log.Name}</td><td>${log.Device}</td><td>${log["IP Address"]}</td><td>${log.Status}</td></tr>`;
    });
    html += `</table>`;
    document.querySelector("#content-area").innerHTML = html;
}

// Render Image List & Preview
function renderCapturedImages(data) {
    let imageList = document.querySelector("#image-list");
    let imagePreviewSection = document.querySelector("#image-preview-section");
    imageList.innerHTML = "";
    imagePreviewSection.style.display = "block";

    data.forEach(img => {
        let listItem = document.createElement("li");
        listItem.innerHTML = `<a href="#" onclick="previewImage('/intruders/${img.filename}')">${img.filename}</a>`;
        imageList.appendChild(listItem);
    });
}

// Function to Preview Selected Image
function previewImage(imageSrc) {
    document.getElementById("selected-image").src = imageSrc;
}
