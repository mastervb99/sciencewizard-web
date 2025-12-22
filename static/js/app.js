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
    setupAuthModal();
    setupContinueButton();
    setupNavigation();
    setupSampleButtons();
    setupReferralButton();
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

        // Show files list
        filesList.style.display = 'block';

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
                hideAuthModal();
                updateAuthUI();

                // Proceed with upload if files are ready
                if (uploadedFiles.length > 0) {
                    await processUploadAndGenerate();
                }

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
                hideAuthModal();
                updateAuthUI();

                // Proceed with upload if files are ready
                if (uploadedFiles.length > 0) {
                    await processUploadAndGenerate();
                }

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
                // Show auth modal
                showAuthModal();
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
                <span>Generate Research Project</span>
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
            const href = this.getAttribute('href');
            if (href === '#') return; // Skip empty hash
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Auth Modal
function setupAuthModal() {
    const authSection = document.getElementById('authSection');
    const authClose = document.getElementById('authClose');
    const loginLink = document.querySelector('.login-link');

    // Open modal on login link click
    if (loginLink && !isAuthenticated) {
        loginLink.addEventListener('click', (e) => {
            e.preventDefault();
            showAuthModal();
        });
    }

    // Close modal on close button
    if (authClose) {
        authClose.addEventListener('click', () => {
            hideAuthModal();
        });
    }

    // Close modal on backdrop click
    if (authSection) {
        authSection.addEventListener('click', (e) => {
            if (e.target === authSection) {
                hideAuthModal();
            }
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideAuthModal();
        }
    });
}

function showAuthModal() {
    const authSection = document.getElementById('authSection');
    if (authSection) {
        authSection.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function hideAuthModal() {
    const authSection = document.getElementById('authSection');
    if (authSection) {
        authSection.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Sample Buttons
function setupSampleButtons() {
    const sampleBtns = document.querySelectorAll('.sample-btn');

    sampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const sampleType = btn.getAttribute('data-sample');
            loadSampleData(sampleType);
        });
    });
}

function loadSampleData(type) {
    const filesList = document.getElementById('filesList');

    // Clear existing files
    uploadedFiles = [];
    if (filesList) {
        filesList.innerHTML = '';
        filesList.style.display = 'block';
    }

    // Create mock sample files based on type
    const samples = {
        clinical: [
            { name: 'clinical_trial_data.csv', size: '2.4 MB' },
            { name: 'study_protocol.docx', size: '156 KB' }
        ],
        survey: [
            { name: 'survey_responses.xlsx', size: '1.8 MB' },
            { name: 'survey_questions.docx', size: '45 KB' }
        ]
    };

    const files = samples[type] || samples.clinical;

    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span class="file-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </span>
            <span class="file-name">${file.name}</span>
            <span class="file-size">${file.size}</span>
        `;
        filesList.appendChild(fileItem);

        // Create a mock File object for demo
        const mockFile = new File([''], file.name, { type: 'text/plain' });
        uploadedFiles.push(mockFile);
    });

    // Scroll to upload area
    const uploadCard = document.querySelector('.upload-card');
    if (uploadCard) {
        uploadCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Enhanced Referral System
function setupReferralButton() {
    const generateReferralBtn = document.getElementById('generateReferralBtn');
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    const emailInviteBtn = document.getElementById('emailInviteBtn');

    if (generateReferralBtn) {
        generateReferralBtn.addEventListener('click', async () => {
            if (!isAuthenticated) {
                showAuthModal();
                const signupTab = document.querySelector('.auth-tab[data-tab="signup"]');
                if (signupTab) signupTab.click();
                return;
            }

            try {
                // Generate referral code via API
                const response = await apiCall('/api/referral/generate', {
                    method: 'POST'
                });

                if (response.ok) {
                    const data = await response.json();
                    displayReferralCode(data.referral_code);
                } else {
                    // Fallback to client-side generation
                    const user = JSON.parse(localStorage.getItem('velvet_user') || '{}');
                    const userId = user.id || Math.random().toString(36).substr(2, 5);
                    const refCode = `VR-${userId.toString().substring(0,3).toUpperCase()}${Math.floor(Math.random() * 1000)}`;
                    displayReferralCode(refCode);
                }
            } catch (error) {
                console.error('Error generating referral code:', error);
                // Fallback generation
                const refCode = `VR-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;
                displayReferralCode(refCode);
            }
        });
    }

    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', () => {
            const referralCode = document.getElementById('referralCode').textContent;
            const refLink = `${window.location.origin}?ref=${referralCode}`;

            navigator.clipboard.writeText(refLink).then(() => {
                copyCodeBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyCodeBtn.textContent = 'Copy';
                }, 2000);
            }).catch(() => {
                prompt('Copy your referral link:', refLink);
            });
        });
    }

    if (emailInviteBtn) {
        emailInviteBtn.addEventListener('click', async () => {
            if (!isAuthenticated) {
                showAuthModal();
                return;
            }

            const inviteEmail = document.getElementById('inviteEmail').value.trim();
            if (!inviteEmail) {
                showInviteStatus('Please enter a valid email address', 'error');
                return;
            }

            // Validate email format
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(inviteEmail)) {
                showInviteStatus('Please enter a valid email address', 'error');
                return;
            }

            try {
                emailInviteBtn.disabled = true;
                emailInviteBtn.innerHTML = `
                    <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                        <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                    </svg>
                    Sending...
                `;

                const response = await apiCall('/api/referral/invite', {
                    method: 'POST',
                    body: { email: inviteEmail }
                });

                if (response.ok) {
                    showInviteStatus('Invitation sent successfully!', 'success');
                    document.getElementById('inviteEmail').value = '';
                } else {
                    const data = await response.json();
                    showInviteStatus(data.detail || 'Failed to send invitation', 'error');
                }
            } catch (error) {
                console.error('Error sending invitation:', error);
                showInviteStatus('Failed to send invitation. Please try again.', 'error');
            } finally {
                emailInviteBtn.disabled = false;
                emailInviteBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    Send Invitation
                `;
            }
        });
    }
}

function displayReferralCode(code) {
    document.getElementById('referralCode').textContent = code;
    document.getElementById('referralCodeDisplay').style.display = 'block';

    // Scroll to the code display
    document.getElementById('referralCodeDisplay').scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

function showInviteStatus(message, type) {
    const statusDiv = document.getElementById('inviteStatus');
    statusDiv.textContent = message;
    statusDiv.className = `invite-status ${type}`;
    statusDiv.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
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
