// ✅ Sidebar toggle functionality
document.querySelector('.toggle-btn').addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('collapsed');
});

// ✅ Dynamic content loader
function loadContent(section) {
    const contentContainer = document.querySelector("#content-area");
    const imagePreviewSection = document.querySelector("#image-preview-section");

    // Show loading state
    contentContainer.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>Loading ${section.replace('-', ' ')}...</p>
        </div>`;
    imagePreviewSection.style.display = "none";

    switch (section) {
        case "home":
            contentContainer.innerHTML = `
                <div class="dashboard-welcome">
                    <h2>Welcome to WebLock Dashboard</h2>
                    <p>Select a section from the sidebar to view logs and captured data.</p>
                    <div class="quick-stats">
                        <div class="stat-card">
                            <i class="fas fa-users"></i>
                            <h3>Employees</h3>
                            <p>24 Active</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-user-secret"></i>
                            <h3>Intruders</h3>
                            <p>5 Detected</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-key"></i>
                            <h3>Keylogs</h3>
                            <p>142 Today</p>
                        </div>
                    </div>
                </div>`;
            break;
        case "employee-logs":
            loadCSVData('/logs/employee_log.csv', renderEmployeeLogs);
            break;
        case "intruder-logs":
            loadCSVData('/logs/intruder_log.csv', renderIntruderLogs);
            break;
        case "keystroke-logs":
            fetchData("/logs/key_logs.json", renderKeystrokes);
            break;
        case "screenshot-logs":
            fetchData("/Capture/screenshots", renderScreenshots);
            break;
        case "captured-images":
            fetchData("/Capture/intruder", renderCapturedImages);
            break;
        default:
            contentContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h2>Error</h2>
                    <p>Invalid selection.</p>
                </div>`;
            break;
    }
}

// ✅ Robust Fetch Data with error handling
function fetchData(endpoint, callback) {
    fetch(endpoint)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to load: ${response.status} - ${response.statusText}`);
            
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                return response.json();
            }
            return response.text();
        })
        .then(data => {
            if (!data || (Array.isArray(data) && data.length === 0)) {
                showNoDataMessage();
            } else {
                callback(data);
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            showErrorMessage(error);
        });
}

// ✅ CSV Data Loader with Error Handling
function loadCSVData(csvFile, callback) {
    fetch(csvFile)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to load: ${response.status} - ${response.statusText}`);
            return response.text();
        })
        .then(data => callback(data))
        .catch(error => {
            console.error("Error loading CSV data:", error);
            showErrorMessage(error);
        });
}

// ✅ Render Employee Logs
function renderEmployeeLogs(csvData) {
    const rows = csvData.trim().split("\n");
    const contentContainer = document.querySelector("#content-area");

    if (rows.length < 2) {
        showNoDataMessage("No Employee Logs Found");
        return;
    }

    let html = `
        <div class="table-header">
            <h2>Employee Logs</h2>
            <div class="table-actions">
                <button class="export-btn" onclick="exportToCSV('employee_logs.csv')">
                    <i class="fas fa-download"></i> Export
                </button>
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" placeholder="Search employees..." oninput="filterTable(this)">
                </div>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>MAC Address</th>
                        <th>Device</th>
                        <th>Location</th>
                        <th>Last Login</th>
                    </tr>
                </thead>
                <tbody>`;

    rows.slice(1).forEach(row => {
        const cols = row.split(",").map(col => col.trim());
        html += `<tr>${cols.map(col => `<td>${col}</td>`).join('')}</tr>`;
    });

    html += `</tbody></table></div>`;
    contentContainer.innerHTML = html;
}

// ✅ Render Intruder Logs
function renderIntruderLogs(csvData) {
    const rows = csvData.trim().split("\n");
    const contentContainer = document.querySelector("#content-area");

    if (rows.length < 2) {
        showNoDataMessage("No Intruder Logs Found");
        return;
    }

    let html = `
        <div class="table-header">
            <h2>Intruder Logs</h2>
            <div class="table-actions">
                <button class="export-btn" onclick="exportToCSV('intruder_logs.csv')">
                    <i class="fas fa-download"></i> Export
                </button>
                <button class="map-view-btn" onclick="showIntruderMap()">
                    <i class="fas fa-map-marked-alt"></i> Map View
                </button>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>IP</th>
                        <th>City</th>
                        <th>State</th>
                        <th>Country</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>ISP</th>
                    </tr>
                </thead>
                <tbody>`;

    rows.slice(1).forEach(row => {
        const cols = row.split(",").map(col => col.trim());
        html += `<tr>${cols.map(col => `<td>${col}</td>`).join('')}</tr>`;
    });

    html += `</tbody></table></div>`;
    contentContainer.innerHTML = html;
}

// ✅ Render Keystroke Logs
function renderKeystrokes(data) {
    const contentContainer = document.querySelector("#content-area");

    if (!data || data.length === 0) {
        showNoDataMessage("No Keystroke Logs Available");
        return;
    }

    let html = `
        <div class="table-header">
            <h2>Keystroke Logs</h2>
            <div class="table-actions">
                <button class="export-btn" onclick="exportToJSON('keystroke_logs.json')">
                    <i class="fas fa-download"></i> Export
                </button>
                <div class="filter-options">
                    <select onchange="filterKeystrokes(this)">
                        <option value="all">All Users</option>
                        ${[...new Set(data.map(item => item.user))].map(user => 
                            `<option value="${user}">${user}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Keystroke</th>
                        <th>User</th>
                        <th>Application</th>
                    </tr>
                </thead>
                <tbody>`;

    data.forEach(log => {
        html += `
            <tr>
                <td>${log.timestamp}</td>
                <td class="keystroke-data">${log.keystroke}</td>
                <td>${log.user}</td>
                <td>${log.application || 'N/A'}</td>
            </tr>`;
    });

    html += `</tbody></table></div>`;
    contentContainer.innerHTML = html;
}

// ✅ Render Screenshots with Gallery
function renderScreenshots(data) {
    const contentContainer = document.querySelector("#content-area");

    if (!data || data.length === 0) {
        showNoDataMessage("No Screenshot Logs Available");
        return;
    }

    let html = `
        <div class="gallery-header">
            <h2>Screenshot Logs</h2>
            <div class="gallery-actions">
                <button class="export-btn" onclick="exportAllScreenshots()">
                    <i class="fas fa-download"></i> Export All
                </button>
                <div class="view-toggle">
                    <button class="view-btn active" data-view="grid">
                        <i class="fas fa-th"></i> Grid
                    </button>
                    <button class="view-btn" data-view="list">
                        <i class="fas fa-list"></i> List
                    </button>
                </div>
            </div>
        </div>
        <div class="screenshot-gallery grid-view">`;

    data.forEach(log => {
        const imagePath = `Capture/screenshots/${log.filename}`;
        html += `
            <div class="screenshot-item" onclick="previewImage('${imagePath}')">
                <div class="screenshot-thumbnail">
                    <img src="${imagePath}" alt="Screenshot" 
                         onerror="this.src='/images/placeholder.png'"
                         loading="lazy">
                    <div class="screenshot-overlay">
                        <i class="fas fa-search-plus"></i>
                    </div>
                </div>
                <div class="screenshot-info">
                    <p class="filename">${log.filename}</p>
                    <p class="timestamp">${log.timestamp}</p>
                    <button class="download-btn" onclick="event.stopPropagation(); downloadImage('${imagePath}', '${log.filename}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>`;
    });

    html += `</div>`;
    contentContainer.innerHTML = html;

    // Add view toggle functionality
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const gallery = document.querySelector('.screenshot-gallery');
            gallery.classList.remove('grid-view', 'list-view');
            gallery.classList.add(`${this.dataset.view}-view`);
        });
    });
}

// ✅ Enhanced Render Captured Images with proper file path handling
function renderCapturedImages(data) {
    const imagePreviewSection = document.querySelector("#image-preview-section");
    imagePreviewSection.style.display = "flex";
    imagePreviewSection.innerHTML = `
        <div class="image-container">
            <div class="file-list">
                <div class="file-list-header">
                    <h3>Captured Files</h3>
                    <div class="file-actions">
                        <button class="refresh-btn" onclick="refreshFiles()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        <div class="search-box">
                            <i class="fas fa-search"></i>
                            <input type="text" placeholder="Search files..." oninput="filterFiles(this)">
                        </div>
                    </div>
                </div>
                <div class="file-list-items"></div>
            </div>
            <div class="preview-area">
                <div class="preview-placeholder">
                    <i class="fas fa-image"></i>
                    <p>Select an image to preview</p>
                </div>
                <img id="selected-image" src="" alt="Preview">
                <div class="preview-actions">
                    <button class="download-btn" onclick="downloadCurrentImage()">
                        <i class="fas fa-download"></i> Download
                    </button>
                    <button class="delete-btn" onclick="deleteCurrentImage()">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>`;

    const fileList = imagePreviewSection.querySelector('.file-list-items');
    
    try {
        // Handle different response formats
        let files = [];
        if (Array.isArray(data)) {
            files = data;
        } else if (typeof data === 'string') {
            // Parse directory listing or newline-separated filenames
            files = data.split('\n')
                .filter(line => line.trim() && 
                      !line.startsWith('<!') && 
                      /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(line.trim()))
                .map(filename => ({ filename: filename.trim() }));
        }

        if (files.length === 0) {
            throw new Error('No image files found in /Capture/intruder');
        }

        // Display the files
        files.forEach(file => {
            const fileName = file.filename || file;
            if (!fileName) return;

            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileExt = fileName.split('.').pop().toLowerCase();
            const fileIcon = 'fa-image'; // All files should be images after filtering
            
            fileItem.innerHTML = `
                <i class="fas ${fileIcon}"></i>
                <div class="file-info">
                    <span class="file-name">${fileName}</span>
                    <span class="file-meta">
                        <span class="file-size">${file.size || getRandomFileSize()}</span>
                        <span class="file-time">${file.timestamp || getRandomTimeAgo()}</span>
                    </span>
                </div>`;
            
            fileItem.addEventListener('click', () => {
                // Use the correct path to the image
                previewImage(`/Capture/intruder/${encodeURIComponent(fileName)}`);
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('selected'));
                fileItem.classList.add('selected');
            });
            
            fileList.appendChild(fileItem);
        });

    } catch (error) {
        fileList.innerHTML = `
            <div class="no-files">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${error.message}</p>
            </div>`;
        console.error('Error loading captured images:', error);
    }
}

// ✅ Enhanced Image Preview Function with proper path handling
function previewImage(imageSrc) {
    const previewPlaceholder = document.querySelector('.preview-placeholder');
    const imgElement = document.getElementById('selected-image');
    
    // Show loading state
    previewPlaceholder.innerHTML = `<div class="loading-spinner"></div>`;
    previewPlaceholder.style.display = 'flex';
    imgElement.style.display = 'none';
    
    // Load image with cache busting to ensure fresh load
    imgElement.src = imageSrc + '?t=' + new Date().getTime();
    
    imgElement.onload = () => {
        previewPlaceholder.style.display = 'none';
        imgElement.style.display = 'block';
    };
    
    imgElement.onerror = () => {
        previewPlaceholder.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <p>Failed to load image</p>
            <small>${imageSrc}</small>`;
        imgElement.style.display = 'none';
    };
}

// Update the fetch call to ensure proper directory listing
function fetchData(endpoint, callback) {
    fetch(endpoint)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to load: ${response.status} - ${response.statusText}`);
            
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                return response.json();
            } else {
                return response.text().then(text => {
                    // Handle plain text directory listing
                    if (text.includes('<html') && text.includes('Directory Listing')) {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(text, 'text/html');
                        return Array.from(doc.querySelectorAll('a'))
                            .map(a => a.getAttribute('href'))
                            .filter(href => !href.startsWith('?') && 
                                          href !== '/' && 
                                          /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(href));
                    }
                    return text;
                });
            }
        })
        .then(data => callback(data))
        .catch(error => {
            console.error("Error fetching data:", error);
            showErrorMessage(error);
        });
}

// Update refresh function to use correct endpoint
function refreshFiles() {
    fetchData("/Capture/intruder", renderCapturedImages);
}

    // Process and filter the file data
    const fileList = imagePreviewSection.querySelector('.file-list-items');
    let files = [];

    try {
        // Convert data to array if it isn't one
        if (Array.isArray(data)) {
            files = data;
        } else if (typeof data === 'string') {
            // Handle directory listing text response - filter out CSS and non-image files
            files = data.split('\n')
                      .filter(line => {
                          // Skip lines that look like CSS code
                          if (line.includes(':') || line.includes('{') || line.includes('}') || line.includes(';')) {
                              return false;
                          }
                          // Only include likely image files
                          return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(line.trim());
                      })
                      .map(name => ({ filename: name.trim() }));
        }

        if (files.length === 0) {
            throw new Error('No valid image files found');
        }

        // Display the filtered files
        files.forEach(file => {
            const fileName = file.filename || file;
            if (!fileName) return;

            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileExt = fileName.split('.').pop().toLowerCase();
            const fileIcon = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExt) ? 'fa-image' : 'fa-file';
            
            fileItem.innerHTML = `
                <i class="fas ${fileIcon}"></i>
                <div class="file-info">
                    <span class="file-name">${fileName}</span>
                    <span class="file-meta">
                        <span class="file-size">${getRandomFileSize()}</span>
                        <span class="file-time">${getRandomTimeAgo()}</span>
                    </span>
                </div>`;
            
            fileItem.addEventListener('click', () => {
                previewImage(`/Capture/intruder/${fileName}`);
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('selected'));
                fileItem.classList.add('selected');
            });
            
            fileList.appendChild(fileItem);
        });

    } catch (error) {
        fileList.innerHTML = `
            <div class="no-files">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${error.message}</p>
            </div>`;
    }


// ✅ Enhanced Image Preview Function
function previewImage(imageSrc) {
    const previewPlaceholder = document.querySelector('.preview-placeholder');
    const imgElement = document.getElementById('selected-image');
    
    // Show loading state
    previewPlaceholder.innerHTML = `<div class="loading-spinner"></div>`;
    previewPlaceholder.style.display = 'flex';
    imgElement.style.display = 'none';
    
    // Load image
    imgElement.src = imageSrc;
    
    imgElement.onload = () => {
        previewPlaceholder.style.display = 'none';
        imgElement.style.display = 'block';
        
        // Add zoom functionality
        imgElement.addEventListener('click', function() {
            this.classList.toggle('zoomed');
        });
    };
    
    imgElement.onerror = () => {
        previewPlaceholder.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <p>Failed to load image</p>`;
        imgElement.style.display = 'none';
    };
}

// Helper Functions
function showNoDataMessage(message = "No data available") {
    document.querySelector("#content-area").innerHTML = `
        <div class="no-data-message">
            <i class="fas fa-database"></i>
            <h3>${message}</h3>
            <p>There is currently no data to display for this section.</p>
        </div>`;
}

function showErrorMessage(error) {
    document.querySelector("#content-area").innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle"></i>
            <h2>Error Loading Data</h2>
            <p>${error.message}</p>
            <button class="retry-btn" onclick="window.location.reload()">
                <i class="fas fa-sync-alt"></i> Retry
            </button>
        </div>`;
}

function getRandomFileSize() {
    const sizes = ['128 KB', '256 KB', '512 KB', '1 MB', '2 MB'];
    return sizes[Math.floor(Math.random() * sizes.length)];
}

function getRandomTimeAgo() {
    const times = ['a few seconds ago', 'less than a minute ago', '2 minutes ago', 
                  '5 minutes ago', '10 minutes ago', 'an hour ago'];
    return times[Math.floor(Math.random() * times.length)];
}

// File Operations
function downloadImage(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || url.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function downloadCurrentImage() {
    const img = document.getElementById('selected-image');
    if (img.src) {
        downloadImage(img.src, img.src.split('/').pop());
    }
}

function deleteCurrentImage() {
    const img = document.getElementById('selected-image');
    if (img.src) {
        const fileName = img.src.split('/').pop();
        if (confirm(`Are you sure you want to delete ${fileName}?`)) {
            // Here you would typically make a DELETE request to your server
            console.log(`Deleting image: ${fileName}`);
            refreshFiles();
        }
    }
}

function refreshFiles() {
    fetchData("/Capture/intruder", renderCapturedImages);
}

function filterFiles(input) {
    const searchTerm = input.value.toLowerCase();
    document.querySelectorAll('.file-item').forEach(item => {
        const fileName = item.querySelector('.file-name').textContent.toLowerCase();
        item.style.display = fileName.includes(searchTerm) ? 'flex' : 'none';
    });
}

// Export Functions
function exportToCSV(filename) {
    // Implementation would convert table data to CSV and download
    console.log(`Exporting to ${filename}`);
    // Example implementation:
    const table = document.querySelector('table');
    if (table) {
        const rows = table.querySelectorAll('tr');
        let csvContent = '';
        
        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = Array.from(cols).map(col => `"${col.textContent.replace(/"/g, '""')}"`).join(',');
            csvContent += rowData + '\r\n';
        });
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        downloadImage(url, filename);
    }
}

function exportToJSON(filename) {
    // Implementation would convert data to JSON and download
    console.log(`Exporting to ${filename}`);
    // Example implementation:
    const table = document.querySelector('table');
    if (table) {
        const rows = table.querySelectorAll('tr');
        const headers = Array.from(rows[0].querySelectorAll('th')).map(th => th.textContent);
        const jsonData = [];
        
        for (let i = 1; i < rows.length; i++) {
            const cols = rows[i].querySelectorAll('td');
            const obj = {};
            headers.forEach((header, index) => {
                obj[header] = cols[index]?.textContent || '';
            });
            jsonData.push(obj);
        }
        
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        downloadImage(url, filename);
    }
}

function exportAllScreenshots() {
    // Implementation would zip and download all screenshots
    console.log('Exporting all screenshots');
    alert('This would normally export all screenshots as a ZIP file');
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadContent('home');
});