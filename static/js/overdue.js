// overdue.js - fetch and display user's overdue books

const API_BASE_URL = '/api';
let currentUserid = ''; // Global variable to store userid

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔍 Overdue page DOMContentLoaded started');

    // Get userid and fullname from data attributes (embedded by Flask) or localStorage fallback
    const overduePage = document.querySelector('.overdue-page');
    console.log('📍 Found overdue-page element:', overduePage);

    let userid = overduePage?.getAttribute('data-userid');
    let fullname = overduePage?.getAttribute('data-fullname');

    console.log('📊 From data attributes - userid:', userid, 'fullname:', fullname);

    // Fallback to localStorage if not in data attributes
    if (!userid) {
        userid = localStorage.getItem('userid');
        console.log('📦 Fallback from localStorage - userid:', userid);
    }
    if (!fullname) {
        fullname = localStorage.getItem('fullname');
        console.log('📦 Fallback from localStorage - fullname:', fullname);
    }

    const userNameEl = document.getElementById('userName');
    if (!userid) {
        console.error('❌ No userid found! Redirecting to login');
        window.location.href = '/login';
        return;
    }

    currentUserid = userid; // Store in global variable
    console.log('✅ currentUserid set to:', currentUserid);

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
        window.location.href = '/notifications';
    });

    console.log('🚀 Calling loadOverdue with userid:', currentUserid);
    await loadOverdue();
});

async function loadOverdue() {
    const container = document.getElementById('overdueContainer');
    console.log('📋 loadOverdue called');
    console.log('🔑 currentUserid:', currentUserid);
    console.log('🎯 API URL:', `${API_BASE_URL}/books/user/${currentUserid}/overdue`);
    console.log('📌 Container element:', container);

    try {
        const url = `${API_BASE_URL}/books/user/${currentUserid}/overdue`;
        console.log('🌐 Fetching from:', url);
        const resp = await fetch(url, { method: 'GET' });

        console.log('📨 Response status:', resp.status);
        console.log('✔️ Response ok:', resp.ok);

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }

        const data = await resp.json();
        console.log('📦 API Response data:', data);

        if (data.success) {
            const overdue = data.overduebooks || [];
            console.log('✅ Overdue entries count:', overdue.length);

            if (overdue.length === 0) {
                console.log('ℹ️ No overdue entries');
                container.innerHTML = `
                    <div class="no-data">
                        <div class="no-data-icon">✅</div>
                        <h3>No Overdue Books</h3>
                        <p>All your books are on time! Great job!</p>
                    </div>
                `;
            } else {
                console.log('🏗️ Building table with', overdue.length, 'entries');
                const wrapper = document.createElement('div');
                wrapper.className = 'overdue-table-wrapper';

                const table = document.createElement('table');
                table.className = 'overdue-table';

                // Create header
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th style="width: 25%">Title</th>
                        <th style="width: 15%">Author</th>
                        <th style="width: 12%">Borrowed</th>
                        <th style="width: 12%">Due Date</th>
                        <th style="width: 10%">Days Overdue</th>
                        <th style="width: 12%">Fine Amount</th>
                    </tr>
                `;
                table.appendChild(thead);

                // Create body
                const tbody = document.createElement('tbody');
                overdue.forEach((entry, idx) => {
                    console.log(`📄 Processing entry ${idx}:`, entry);
                    const row = document.createElement('tr');

                    row.innerHTML = `
                        <td class="title">${escapeHtml(entry.title)}</td>
                        <td class="author">${escapeHtml(entry.author || 'N/A')}</td>
                        <td>${entry.borrowdate}</td>
                        <td>${entry.duedate}</td>
                        <td><span class="overdue-badge">${entry.days_overdue} days</span></td>
                        <td class="fine-amount">₹${entry.fine_amount}</td>
                    `;
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                wrapper.appendChild(table);
                container.innerHTML = '';
                container.appendChild(wrapper);
                console.log('✅ Table rendered successfully');
            }
        } else {
            console.error('❌ API returned success: false', data.message);
            container.innerHTML = `
                <div class="no-data">
                    <div class="no-data-icon">⚠️</div>
                    <h3>Error Loading Overdue Books</h3>
                    <p>${escapeHtml(data.message || 'Failed to load your overdue books')}</p>
                </div>
            `;
        }
    } catch (err) {
        console.error('❌ loadOverdue failed:', err);
        container.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">🚫</div>
                <h3>Connection Error</h3>
                <p>Unable to load overdue books. Please try again later.</p>
            </div>
        `;
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}