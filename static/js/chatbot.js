// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const logoutBtn = document.getElementById('logoutBtn');
const userName = document.getElementById('userName');
const notificationCount = document.getElementById('notificationCount');

// State Management
let conversationContext = '';  // Track conversation context

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

    // Set up chat event listeners
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

function setupEventListeners() {
    // Logout functionality
    document.querySelectorAll('#logoutBtn, #sidebarLogoutBtn').forEach(btn => {
        if (btn) {
            btn.addEventListener('click', async () => {
                try {
                    await fetch(`${API_BASE_URL}/logout`, { method: 'POST' });
                } catch (error) {
                    console.error('Logout error:', error);
                }
                localStorage.clear();
                window.location.href = '/login';
            });
        }
    });
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

// Send Chat Message
async function sendMessage() {
    const message = chatInput.value.trim();

    if (!message) return;

    // Remove focus and clear input
    chatInput.value = '';
    chatInput.focus();

    // Add user message to chat
    addMessageToChat(message, 'user');

    // Show loading
    showLoading(true);

    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userid,
                message,
                context: conversationContext  // Send current context
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update context for next message
            conversationContext = data.context || '';

            // Add bot response
            addMessageToChat(data.response, 'bot', data.data, data.suggestions);

            // Refresh notifications
            loadNotifications();
        } else {
            addMessageToChat('Sorry, something went wrong. Please try again.', 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        addMessageToChat('Network error. Please try again.', 'bot');
    } finally {
        showLoading(false);
    }
}

// Add Message to Chat
function addMessageToChat(message, sender, data = [], suggestions = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    let content = `<div class="message-content">${escapeHtml(message)}</div>`;

    // Add data items if present
    if (data && data.length > 0) {
        content += '<div class="message-data">';
        data.forEach(item => {
            const title = item.title || item.bookid || 'Unknown';
            const author = item.author ? ` by ${item.author}` : '';
            const status = item.status ? ` (${item.status})` : '';
            const copies = item.availablecopies !== undefined ? ` - ${item.availablecopies} copies available` : '';
            const duedate = item.duedate ? ` | Due: ${item.duedate}` : '';
            const returndate = item.returndate ? ` | Returned: ${item.returndate}` : '';
            const borrowedby = item.borrowedby ? ` | Borrowed by: ${item.borrowedby}` : '';
            const returnedby = item.returnedby ? ` | Returned by: ${item.returnedby}` : '';

            content += `<div class="data-item">
                <strong>${escapeHtml(title)}</strong>
                ${author}${status}${copies}${duedate}${returndate}${borrowedby}${returnedby}
            </div>`;
        });
        content += '</div>';
    }

    // Add suggestions if present
    if (suggestions && suggestions.length > 0) {
        content += '<div class="suggestions">';
        suggestions.forEach(suggestion => {
            content += `<button class="suggestion-btn" onclick="useSuggestion('${escapeHtml(suggestion)}')">${escapeHtml(suggestion)}</button>`;
        });
        content += '</div>';
    }

    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Use suggestion
function useSuggestion(suggestion) {
    chatInput.value = suggestion;
    sendMessage();
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