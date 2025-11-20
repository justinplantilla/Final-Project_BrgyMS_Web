// Add any additional login/register related JavaScript here

// Modal functions for Terms and Conditions
function openTermsModal() {
    document.getElementById('termsModal').style.display = 'flex';
}

function closeTermsModal() {
    document.getElementById('termsModal').style.display = 'none';
    // Uncheck the checkbox when modal is closed without agreeing
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (termsCheckbox) {
        termsCheckbox.checked = false;
    }
}

// Agree to terms function
function agreeToTerms() {
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (termsCheckbox) {
        termsCheckbox.checked = true;
    }
    closeTermsModal();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('termsModal');
    if (event.target === modal) {
        closeTermsModal();
    }
}

// Forgot Password Modal functions
function openForgotPasswordModal() {
    document.getElementById('forgotPasswordModal').style.display = 'flex';
    document.getElementById('emailStep').style.display = 'block';
    document.getElementById('codeStep').style.display = 'none';
    document.getElementById('modalMessage').style.display = 'none';
}

function closeForgotPasswordModal() {
    document.getElementById('forgotPasswordModal').style.display = 'none';
    // Reset forms
    document.getElementById('emailForm').reset();
    document.getElementById('resetForm').reset();
}

// Handle email form submission
document.getElementById('emailForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('resetEmail').value;

    fetch('/send-reset-code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('modalMessage');
        if (data.success) {
            messageDiv.className = 'alert alert-success';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
            // Switch to code step
            document.getElementById('emailStep').style.display = 'none';
            document.getElementById('codeStep').style.display = 'block';
        } else {
            messageDiv.className = 'alert alert-error';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('modalMessage');
        messageDiv.className = 'alert alert-error';
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
    });
});

// Handle reset form submission
document.getElementById('resetForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const code = document.getElementById('resetCode').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        const messageDiv = document.getElementById('modalMessage');
        messageDiv.className = 'alert alert-error';
        messageDiv.textContent = 'Passwords do not match.';
        messageDiv.style.display = 'block';
        return;
    }

    fetch('/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: code,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('modalMessage');
        if (data.success) {
            messageDiv.className = 'alert alert-success';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
            // Close modal after success
            setTimeout(() => {
                closeForgotPasswordModal();
            }, 2000);
        } else {
            messageDiv.className = 'alert alert-error';
            messageDiv.textContent = data.message;
            messageDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('modalMessage');
        messageDiv.className = 'alert alert-error';
        messageDiv.textContent = 'An error occurred. Please try again.';
        messageDiv.style.display = 'block';
    });
});

// Close modal when clicking outside
window.onclick = function(event) {
    const termsModal = document.getElementById('termsModal');
    const forgotModal = document.getElementById('forgotPasswordModal');
    if (event.target === termsModal) {
        closeTermsModal();
    }
    if (event.target === forgotModal) {
        closeForgotPasswordModal();
    }
}
