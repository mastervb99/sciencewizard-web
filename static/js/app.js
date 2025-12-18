/**
 * ScienceWizard - Phase I Static Frontend
 * Basic interactions only - no actual functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Upload zone interactions
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => fileInput.click());

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
            // Phase I: No actual file handling
            console.log('Files dropped (Phase I - demo only)');
        });
    }

    // Auth tab switching
    const authTabs = document.querySelectorAll('.auth-tab');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

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

    // Form submissions (demo only)
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('Form submitted (Phase I - demo only)');
            alert('Phase I Demo: Authentication will be implemented in Phase II');
        });
    });

    // Continue button
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.addEventListener('click', () => {
            console.log('Continue clicked (Phase I - demo only)');
            // Scroll to auth section
            const authSection = document.getElementById('authSection');
            if (authSection) {
                authSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // Smooth scroll for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
