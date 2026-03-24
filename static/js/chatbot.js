// Library AI Chatbot — Full Desktop UI
const API_BASE_URL = '/api';

const chatInput    = document.getElementById('chatInput');
const sendBtn      = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const logoutBtn    = document.getElementById('logoutBtn');
const userName     = document.getElementById('userName');
const notifBadge   = document.getElementById('notificationCount');

let conversationContext = '';

// ──────────────── Init ────────────────
document.addEventListener('DOMContentLoaded', () => {
    const userid   = localStorage.getItem('userid');
    const fullname = localStorage.getItem('fullname');

    if (!userid) { window.location.href = '/login'; return; }

    userName.textContent = `${fullname}`;
    setupEventListeners();
    loadNotifications();
});

function setupEventListeners() {
    // Logout
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    // Send on click
    sendBtn.addEventListener('click', sendMessage);

    // Keyboard handling
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-grow textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
}

// ──────────────── Logout ────────────────
async function logout() {
    try { await fetch(`${API_BASE_URL}/logout`, { method: 'POST' }); } catch (_) {}
    localStorage.clear();
    window.location.href = '/login';
}

// ──────────────── Notifications ────────────────
async function loadNotifications() {
    try {
        const res  = await fetch(`${API_BASE_URL}/notifications`);
        const data = await res.json();
        if (data.success && data.notifications) {
            const unread = data.notifications.filter(n => !n.read).length;
            notifBadge.textContent    = unread > 0 ? unread : '';
            notifBadge.style.display  = unread > 0 ? 'inline' : 'none';
        }
    } catch (_) {}
}

// ──────────────── Quick message (sidebar chips) ────────────────
function sendQuickMessage(text) {
    chatInput.value = text;
    sendMessage();
}

// ──────────────── Core send ────────────────
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    appendUserMessage(message);

    // Show typing indicator
    const typingEl = showTypingIndicator();

    try {
        const userid = localStorage.getItem('userid');
        const res = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userid, message, context: conversationContext })
        });

        const data = await res.json();

        // Small delay to feel more natural
        await sleep(600);
        removeTypingIndicator(typingEl);

        if (data.success) {
            conversationContext = data.context || '';
            appendBotMessage(data.response, data.data, data.suggestions);
            loadNotifications();
        } else {
            appendBotMessage('Sorry, something went wrong. Please try again.', [], []);
        }
    } catch (err) {
        removeTypingIndicator(typingEl);
        appendBotMessage('Network error — please check your connection and try again.', [], []);
    } finally {
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// ──────────────── Append user message ────────────────
function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user-row';
    row.innerHTML = `
        <div class="message-avatar user-avatar">${getInitials()}</div>
        <div>
            <div class="message-bubble user-bubble">${escapeHtml(text)}</div>
            <div class="timestamp" style="text-align:right;">${getTime()}</div>
        </div>`;
    chatMessages.appendChild(row);
    scrollToBottom();
}

// ──────────────── Append bot message ────────────────
function appendBotMessage(text, data = [], suggestions = []) {
    const row = document.createElement('div');
    row.className = 'message-row bot-row';

    // Format the text (support line breaks and bullet points)
    const formattedText = escapeHtml(text)
        .replace(/\n•/g, '<br>&bull;')
        .replace(/\n/g, '<br>');

    let inner = `<div class="message-bubble bot-bubble">${formattedText}</div>`;

    // Book data
    if (data && data.length > 0) {
        if (data.length <= 6) {
            // Card grid for small results
            inner += '<div class="book-cards-grid">';
            data.forEach(item => {
                const copies = item.availablecopies !== undefined ? item.availablecopies : null;
                const isAvail = copies === null ? null : copies > 0;
                const statusClass = copies === null ? 'status-borrowed' : (isAvail ? 'status-available' : 'status-unavailable');
                const statusText  = copies === null ? (item.duedate ? `Due: ${item.duedate}` : (item.returndate ? `Returned: ${item.returndate}` : 'On loan')) : (isAvail ? `${copies} available` : 'Unavailable');

                inner += `
                <div class="book-card">
                    <div class="book-card-title">${escapeHtml(item.title || 'Unknown')}</div>
                    <div class="book-card-author">${item.author ? escapeHtml(item.author) : ''}</div>
                    <span class="book-card-status ${statusClass}">${statusText}</span>
                </div>`;
            });
            inner += '</div>';
        } else {
            // Scrollable list for larger results
            inner += '<div class="book-list-scroll">';
            data.forEach(item => {
                const copies = item.availablecopies !== undefined ? item.availablecopies : null;
                const isAvail = copies === null ? null : copies > 0;
                const statusClass = copies === null ? 'status-borrowed' : (isAvail ? 'status-available' : 'status-unavailable');
                const statusText  = copies === null ? 'On loan' : (isAvail ? `${copies} copy(s)` : 'Unavailable');

                inner += `
                <div class="book-list-item">
                    <div class="book-list-info">
                        <div class="book-list-title">${escapeHtml(item.title || 'Unknown')}</div>
                        <div class="book-list-author">${item.author ? escapeHtml(item.author) : ''}</div>
                    </div>
                    <span class="book-card-status ${statusClass}">${statusText}</span>
                </div>`;
            });
            inner += '</div>';
        }
    }

    // Suggestion chips
    if (suggestions && suggestions.length > 0) {
        inner += '<div class="suggestion-chips">';
        suggestions.forEach(s => {
            inner += `<button class="chip" onclick="sendQuickMessage('${escapeAttr(s)}')">${escapeHtml(s)}</button>`;
        });
        inner += '</div>';
    }

    inner += `<div class="timestamp">${getTime()}</div>`;
    row.innerHTML = `<div class="message-avatar bot-avatar">AI</div><div>${inner}</div>`;
    chatMessages.appendChild(row);
    scrollToBottom();
}

// ──────────────── Typing indicator ────────────────
function showTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'typing-row';
    row.id = 'typingRow';
    row.innerHTML = `
        <div class="message-avatar bot-avatar">AI</div>
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>`;
    chatMessages.appendChild(row);
    scrollToBottom();
    return row;
}

function removeTypingIndicator(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

// ──────────────── Helpers ────────────────
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}

function escapeAttr(text) {
    if (!text) return '';
    return String(text).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function getInitials() {
    const name = localStorage.getItem('fullname') || 'U';
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
}

function getTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}