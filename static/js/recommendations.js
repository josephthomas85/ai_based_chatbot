// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const recommendationsGrid = document.getElementById('recommendationsGrid');
const logoutBtn = document.getElementById('logoutBtn');
const userName = document.getElementById('userName');
const notificationCount = document.getElementById('notificationCount');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const userid = localStorage.getItem('userid');
    const fullname = localStorage.getItem('fullname');

    if (!userid) {
        window.location.href = '/login';
        return;
    }

    userName.textContent = `Welcome, ${fullname}!`;
    setupEventListeners();
    loadNotifications();
    loadRecommendations();
});

function setupEventListeners() {
    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
}

// Logout function
async function logout() {
    try {
        await fetch(`${API_BASE_URL}/logout`, { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    }
    localStorage.clear();
    window.location.href = '/login';
}

// Load notifications count
async function loadNotifications() {
    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/notifications`);
        const data = await response.json();

        if (data.success && data.notifications) {
            const unreadCount = data.notifications.filter(n => !n.read).length;
            if (unreadCount > 0) {
                notificationCount.textContent = unreadCount;
                notificationCount.style.display = 'inline';
            } else {
                notificationCount.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

// Load AI recommendations
async function loadRecommendations() {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/books`);
        const data = await response.json();

        if (data.success && data.books) {
            const books = data.books.filter(book => book.availablecopies > 0);

            // Get random recommendations (up to 6)
            const recommendations = [];
            const shuffled = [...books].sort(() => 0.5 - Math.random());
            for (let i = 0; i < Math.min(6, shuffled.length); i++) {
                recommendations.push(shuffled[i]);
            }

            displayRecommendations(recommendations);
        } else {
            recommendationsGrid.innerHTML = '<div class="loading">No recommendations available at this time.</div>';
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        recommendationsGrid.innerHTML = '<div class="loading">Error loading recommendations. Please try again.</div>';
    } finally {
        showLoading(false);
    }
}

// Display recommendations
function displayRecommendations(books) {
    if (books.length === 0) {
        recommendationsGrid.innerHTML = '<div class="loading">No books available for recommendations.</div>';
        return;
    }

    recommendationsGrid.innerHTML = '';

    books.forEach(book => {
        const card = document.createElement('div');
        card.className = 'recommendation-card';

        const isAvailable = book.availablecopies > 0;

        card.innerHTML = `
            <div class="book-title">${escapeHtml(book.title)}</div>
            <div class="book-author">by ${escapeHtml(book.author)}</div>
            <div class="book-details">
                Category: ${escapeHtml(book.category || 'General')}<br>
                Available: ${book.availablecopies} copies
            </div>
            <button class="borrow-btn" onclick="borrowBook('${book.bookid}')" ${isAvailable ? '' : 'disabled'}>
                ${isAvailable ? 'Borrow Book' : 'Unavailable'}
            </button>
        `;

        recommendationsGrid.appendChild(card);
    });
}

// Borrow book
async function borrowBook(bookid) {
    showLoading(true);
    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/books/borrow`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userid, bookid })
        });

        const data = await response.json();

        if (data.success) {
            alert('Book borrowed successfully!');
            loadRecommendations(); // Refresh recommendations
            loadNotifications(); // Refresh notifications
        } else {
            alert(data.message || 'Failed to borrow book');
        }
    } catch (error) {
        console.error('Borrow error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Show loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'flex' : 'none';
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}