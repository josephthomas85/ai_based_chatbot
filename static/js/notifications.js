// notifications.js - load and display notifications page

const API_BASE_URL = '/api';
let currentUserid = ''; // Global variable to store userid

document.addEventListener('DOMContentLoaded', async () => {
    // Get userid and fullname from data attributes (embedded by Flask) or localStorage fallback
    let userid = document.querySelector('.notifications-page')?.getAttribute('data-userid');
    let fullname = document.querySelector('.notifications-page')?.getAttribute('data-fullname');
    
    // Fallback to localStorage if not in data attributes
    if (!userid) {
        userid = localStorage.getItem('userid');
    }
    if (!fullname) {
        fullname = localStorage.getItem('fullname');
    }
    
    const userNameEl = document.getElementById('userName');
    if (!userid) {
        window.location.href = '/login';
        return;
    }
    
    currentUserid = userid; // Store in global variable
    userNameEl.textContent = `Welcome, ${fullname}!`;
    
    // Store in localStorage for future use
    localStorage.setItem('userid', userid);
    localStorage.setItem('fullname', fullname);

    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        fetch('/api/logout', { method: 'POST' }).catch(e => console.error(e));
        window.location.href = '/login';
    });
    document.getElementById('backHome').addEventListener('click', () => {
        window.location.href = '/home';
    });
    document.getElementById('notificationBtn').addEventListener('click', () => {
        window.location.reload();
    });

    await loadNotifications();
});

async function loadNotifications() {
    const list = document.getElementById('notificationsList');
    const statsEl = document.getElementById('notificationStats');
    try {
        const resp = await fetch(`${API_BASE_URL}/notifications`, { method: 'GET' });
        
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
        
        const data = await resp.json();
        if (data.success) {
            const notifs = data.notifications || [];
            if (notifs.length === 0) {
                list.innerHTML = `
                    <div class="no-data">
                        <div class="no-data-icon">😌</div>
                        <h3>All Caught Up!</h3>
                        <p>You have no notifications at the moment</p>
                    </div>
                `;
                statsEl.style.display = 'none';
            } else {
                list.innerHTML = '';
                const unreadIds = [];
                let unreadCount = 0;

                notifs.forEach((n, index) => {
                    const isUnread = !n.read;
                    if (isUnread) {
                        unreadCount++;
                        unreadIds.push(n.id);
                    }

                    const div = document.createElement('div');
                    div.className = 'notif-item' + (isUnread ? ' unread' : ' read');
                    
                    const badge = isUnread ? 
                        `<span class="notif-badge unread">NEW</span>` : 
                        `<span class="notif-badge read">READ</span>`;
                    
                    const icon = getNotificationIcon(n.message);
                    const timestamp = n.timestamp ? formatTime(n.timestamp) : 'Just now';
                    
                    div.innerHTML = `
                        ${badge}
                        <div style="display: flex; align-items: start; gap: 10px;">
                            <span class="notif-icon">${icon}</span>
                            <div style="flex: 1;">
                                <div class="notif-message">${escapeHtml(n.message)}</div>
                                <div class="notif-time">${timestamp}</div>
                            </div>
                        </div>
                    `;
                    list.appendChild(div);
                });

                // Show stats
                document.getElementById('unreadCount').textContent = unreadCount;
                document.getElementById('totalCount').textContent = notifs.length;
                statsEl.style.display = 'flex';

                // Mark unread as read
                if (unreadIds.length > 0) {
                    fetch(`${API_BASE_URL}/notifications/mark_read`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ userid: currentUserid, ids: unreadIds })
                    })
                    .then(r => r.json())
                    .then(res => {
                        if (res.success) {
                            // Clear the unread count immediately after reading
                            document.getElementById('unreadCount').textContent = '0';

                            // Also clear the top notification badge in the navbar (if present)
                            const navBadge = document.getElementById('notificationCount');
                            if (navBadge) navBadge.textContent = '';

                            // Update list UI to show all as read
                            document.querySelectorAll('.notif-item.unread').forEach(item => {
                                item.classList.remove('unread');
                                item.classList.add('read');
                                const badge = item.querySelector('.notif-badge');
                                if (badge) {
                                    badge.textContent = 'READ';
                                    badge.classList.remove('unread');
                                    badge.classList.add('read');
                                }
                            });
                        }
                    })
                    .catch(e => console.error('mark read failed', e));
                }
            }
        } else {
            list.innerHTML = `
                <div class="no-data">
                    <div class="no-data-icon">⚠️</div>
                    <h3>Error Loading Notifications</h3>
                    <p>${escapeHtml(data.message || 'Failed to load notifications')}</p>
                </div>
            `;
            statsEl.style.display = 'none';
        }
    } catch (err) {
        console.error('Failed to load notifications', err);
        list.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">🔌</div>
                <h3>Network Error</h3>
                <p>Unable to connect to the server</p>
            </div>
        `;
        statsEl.style.display = 'none';
    }
}

function getNotificationIcon(message) {
    if (message.includes('restock') || message.includes('stock')) return '📦';
    if (message.includes('overdue') || message.includes('due')) return '⏰';
    if (message.includes('return')) return '✅';
    if (message.includes('borrow')) return '📕';
    return '📬';
}

function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    } catch (e) {
        return 'Recently';
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}