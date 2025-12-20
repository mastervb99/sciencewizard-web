/**
 * Velvet Research - Frontend Application
 * Full functionality with API integration
 */

// State
let uploadedFiles = [];
let uploadId = null;
let isAuthenticated = false;

// API helpers
const API_BASE = '';

async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('velvet_token');
    const headers = {
        ...options.headers
    };

    if (token && !options.noAuth) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        localStorage.removeItem('velvet_token');
        localStorage.removeItem('velvet_user');
        isAuthenticated = false;
        updateAuthUI();
        throw new Error('Session expired. Please log in again.');
    }

    return response;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupUploadZone();
    setupAuthForms();
    setupContinueButton();
    setupNavigation();
});

// Check authentication status
function checkAuth() {
    const token = localStorage.getItem('velvet_token');
    const user = localStorage.getItem('velvet_user');

    if (token && user) {
        isAuthenticated = true;
        updateAuthUI();
    }
}

function updateAuthUI() {
    const authSection = document.getElementById('authSection');
    const loginLink = document.querySelector('.login-link');

    if (isAuthenticated) {
        const user = JSON.parse(localStorage.getItem('velvet_user') || '{}');

        // Update login link to show user
        if (loginLink) {
            loginLink.textContent = user.email ? user.email.split('@')[0] : 'Account';
            loginLink.onclick = (e) => {
                e.preventDefault();
                if (confirm('Do you want to log out?')) {
                    logout();
                }
            };
        }
    }
}

function logout() {
    localStorage.removeItem('velvet_token');
    localStorage.removeItem('velvet_user');
    isAuthenticated = false;
    location.reload();
}

// File Upload
function setupUploadZone() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const filesList = document.getElementById('filesList');

    if (!uploadZone || !fileInput) return;

    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    const filesList = document.getElementById('filesList');

    for (const file of files) {
        // Check extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const allowedExts = ['.csv', '.xlsx', '.xls', '.docx', '.pdf', '.txt'];

        if (!allowedExts.includes(ext)) {
            alert(`File type ${ext} not supported. Allowed: ${allowedExts.join(', ')}`);
            continue;
        }

        // Check size (50MB)
        if (file.size > 50 * 1024 * 1024) {
            alert(`File ${file.name} exceeds 50MB limit`);
            continue;
        }

        // Add to list
        uploadedFiles.push(file);

        // Update UI
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span class="file-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </span>
            <span class="file-name">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;
        filesList.appendChild(fileItem);
    }

    // Clear the demo files if any
    const demoFiles = filesList.querySelectorAll('.file-item');
    if (uploadedFiles.length > 0 && demoFiles.length > uploadedFiles.length) {
        // Remove first N demo items
        const toRemove = demoFiles.length - uploadedFiles.length;
        for (let i = 0; i < toRemove; i++) {
            demoFiles[i].remove();
        }
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Authentication Forms
function setupAuthForms() {
    const authTabs = document.querySelectorAll('.auth-tab');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    // Tab switching
    authTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            authTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            const tabName = this.getAttribute('data-tab');
            if (tabName === 'login') {
                loginForm.classList.remove('hidden');
                signupForm.classList.add('hidden');
            } else {
                loginForm.classList.add('hidden');
                signupForm.classList.remove('hidden');
            }
        });
    });

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await apiCall('/api/auth/login', {
                    method: 'POST',
                    noAuth: true,
                    body: { email, password }
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Login failed');
                }

                const data = await response.json();
                localStorage.setItem('velvet_token', data.access_token);
                localStorage.setItem('velvet_user', JSON.stringify(data.user));
                isAuthenticated = true;

                // Proceed with upload
                await processUploadAndGenerate();

            } catch (error) {
                alert(error.message);
            }
        });
    }

    // Signup form submission
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (password !== confirmPassword) {
                alert('Passwords do not match');
                return;
            }

            if (password.length < 6) {
                alert('Password must be at least 6 characters');
                return;
            }

            try {
                const response = await apiCall('/api/auth/register', {
                    method: 'POST',
                    noAuth: true,
                    body: { email, password }
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Registration failed');
                }

                const data = await response.json();
                localStorage.setItem('velvet_token', data.access_token);
                localStorage.setItem('velvet_user', JSON.stringify(data.user));
                isAuthenticated = true;

                // Proceed with upload
                await processUploadAndGenerate();

            } catch (error) {
                alert(error.message);
            }
        });
    }
}

// Continue Button
function setupContinueButton() {
    const continueBtn = document.getElementById('continueBtn');

    if (continueBtn) {
        continueBtn.addEventListener('click', async () => {
            if (uploadedFiles.length === 0) {
                alert('Please upload at least one file');
                return;
            }

            if (isAuthenticated) {
                // Already logged in, proceed directly
                await processUploadAndGenerate();
            } else {
                // Show auth section
                const authSection = document.getElementById('authSection');
                if (authSection) {
                    authSection.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }
}

// Process Upload and Generate
async function processUploadAndGenerate() {
    const continueBtn = document.getElementById('continueBtn');

    try {
        // Show loading state
        if (continueBtn) {
            continueBtn.disabled = true;
            continueBtn.innerHTML = `
                <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                </svg>
                Uploading...
            `;
        }

        // Upload files
        const formData = new FormData();
        for (const file of uploadedFiles) {
            formData.append('files', file);
        }

        const uploadResponse = await apiCall('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const data = await uploadResponse.json();
            throw new Error(data.detail || 'Upload failed');
        }

        const uploadData = await uploadResponse.json();
        uploadId = uploadData.upload_id;

        // Update button
        if (continueBtn) {
            continueBtn.innerHTML = `
                <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                </svg>
                Starting generation...
            `;
        }

        // Start generation
        const generateResponse = await apiCall('/api/generate', {
            method: 'POST',
            body: { upload_id: uploadId }
        });

        if (!generateResponse.ok) {
            const data = await generateResponse.json();
            throw new Error(data.detail || 'Generation failed to start');
        }

        const generateData = await generateResponse.json();

        // Redirect to review page
        window.location.href = `/review.html?job=${generateData.job_id}`;

    } catch (error) {
        alert(error.message);

        // Reset button
        if (continueBtn) {
            continueBtn.disabled = false;
            continueBtn.innerHTML = `
                Continue
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                </svg>
            `;
        }
    }
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Add spinner CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spinner {
        animation: spin 1s linear infinite;
    }
    .btn-primary:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);
