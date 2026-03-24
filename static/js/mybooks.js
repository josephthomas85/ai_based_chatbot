// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const booksGrid = document.getElementById('booksGrid');
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
    loadMyBooks();
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

// Load user's borrowed books
async function loadMyBooks() {
    showLoading(true);
    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/books/user/${userid}/borrowed`);
        const data = await response.json();

        if (data.success) {
            displayBooks(data.borrowedbooks || []);
        } else {
            booksGrid.innerHTML = '<div class="no-books">Error loading your books.</div>';
        }
    } catch (error) {
        console.error('Error loading books:', error);
        booksGrid.innerHTML = '<div class="no-books">Network error. Please try again.</div>';
    } finally {
        showLoading(false);
    }
}

// Display books
function displayBooks(books) {
    if (books.length === 0) {
        booksGrid.innerHTML = '<div class="no-books">You don\'t have any borrowed books right now.</div>';
        return;
    }

    booksGrid.innerHTML = '';

    books.forEach(book => {
        const card = document.createElement('div');
        card.className = 'book-card';

        // Calculate status
        const today = new Date();
        const dueDate = new Date(book.duedate);
        const daysUntilDue = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

        let statusClass = 'status-normal';
        let statusText = 'On Time';
        let subText = '';

        if (book.status === 'approved') {
            statusClass = 'status-due-soon'; // Using a distinct color from existing ones or same as due-soon
            statusText = 'Awaiting Collection';
            subText = `Please collect by: <strong>${formatDate(book.pickup_deadline)}</strong>`;
        } else if (book.status === 'requested' || book.status === 'queued') {
            statusClass = 'status-normal';
            statusText = book.status.toUpperCase();
            subText = 'Processing...';
        } else {
            if (daysUntilDue < 0) {
                statusClass = 'status-overdue';
                statusText = `${Math.abs(daysUntilDue)} days overdue`;
            } else if (daysUntilDue <= 3) {
                statusClass = 'status-due-soon';
                statusText = `Due in ${daysUntilDue} day${daysUntilDue !== 1 ? 's' : ''}`;
            }
        }

        const actionBtn = (book.status === 'borrowed') 
            ? `<button class="return-btn" onclick="returnBook('${book.bookid}')">Return Book</button>`
            : '';

        card.innerHTML = `
            <div class="book-title">${escapeHtml(book.title)}</div>
            <div class="book-author">by ${escapeHtml(book.author)}</div>
            <div class="book-details">
                ${book.status === 'borrowed' ? `Borrowed: ${formatDate(book.borrowdate)}<br>Due: ${formatDate(book.duedate)}<br>` : ''}
                ${subText ? subText + '<br>' : ''}
                <span class="status ${statusClass}">${statusText}</span>
            </div>
            ${actionBtn}
        `;

        booksGrid.appendChild(card);
    });
}

// Return book
async function returnBook(bookid) {
    if (!confirm('Are you sure you want to return this book?')) {
        return;
    }

    showLoading(true);
    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/books/return`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userid, bookid })
        });

        const data = await response.json();

        if (data.success) {
            alert('Book returned successfully!');
            loadMyBooks(); // Refresh books list
            loadNotifications(); // Refresh notifications
        } else {
            alert(data.message || 'Failed to return book');
        }
    } catch (error) {
        console.error('Return error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
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