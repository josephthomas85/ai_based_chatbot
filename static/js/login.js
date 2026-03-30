// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginBox = document.querySelector('.login-box');
const registerBox = document.getElementById('registerBox');
const registerToggle = document.getElementById('registerToggle');
const loginToggle = document.getElementById('loginToggle');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');

// Event Listeners
registerToggle.addEventListener('click', (e) => {
    e.preventDefault();
    loginBox.style.display = 'none';
    registerBox.style.display = 'block';
});

loginToggle.addEventListener('click', (e) => {
    e.preventDefault();
    registerBox.style.display = 'none';
    loginBox.style.display = 'block';
});

// Login Form Submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showError('Please fill in all fields', errorMessage);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store user info
            localStorage.setItem('userid', data.userid);
            localStorage.setItem('username', data.username);
            localStorage.setItem('fullname', data.fullname);
            
            showSuccess('Login successful! Redirecting...', successMessage);
            setTimeout(() => {
                window.location.href = '/home';
            }, 1500);
        } else {
            showError(data.message || 'Login failed', errorMessage);
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Network error. Please try again.', errorMessage);
    }
});

// Register Form Submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fullname = document.getElementById('fullname').value.trim();
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    const email = document.getElementById('email').value.trim();
    
    if (!fullname || !username || !password) {
        showError('Please fill in required fields', document.getElementById('registerError'));
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters', document.getElementById('registerError'));
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                fullname, 
                username, 
                password, 
                email,
                registereddate: new Date().toISOString().split('T')[0]
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Registration successful! You can now login.', document.getElementById('registerSuccess'));
            registerForm.reset();
            setTimeout(() => {
                registerBox.style.display = 'none';
                loginBox.style.display = 'block';
            }, 2000);
        } else {
            showError(data.message || 'Registration failed', document.getElementById('registerError'));
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('Network error. Please try again.', document.getElementById('registerError'));
    }
});

// Helper Functions
function showError(message, element) {
    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => {
        element.classList.remove('show');
    }, 5000);
}

function showSuccess(message, element) {
    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => {
        element.classList.remove('show');
    }, 5000);
}

// Check if already logged in
document.addEventListener('DOMContentLoaded', () => {
    // If login.js is executing, it means the backend session doesn't exist.
    // Clear any stale front-end localStorage to prevent infinite redirects!
    localStorage.removeItem('userid');
    localStorage.removeItem('username');
    localStorage.removeItem('fullname');
});
