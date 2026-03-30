// history.js - fetch and display user's borrow/return history

const API_BASE_URL = '/api';
let currentUserid = ''; // Global variable to store userid

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔍 History page DOMContentLoaded started');
    
    // Get userid and fullname from data attributes (embedded by Flask) or localStorage fallback
    const historyPage = document.querySelector('.history-page');
    console.log('📍 Found history-page element:', historyPage);
    
    let userid = historyPage?.getAttribute('data-userid');
    let fullname = historyPage?.getAttribute('data-fullname');
    
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

    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    document.getElementById('backHome').addEventListener('click', () => {
        window.location.href = '/home';
    });

    document.getElementById('notificationBtn').addEventListener('click', () => {
        window.location.href = '/notifications';
    });

    console.log('🚀 Calling loadHistory with userid:', currentUserid);
    await loadHistory();
});

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    }
    localStorage.clear();
    window.location.href = '/login';
}

async function loadHistory() {
    const container = document.getElementById('historyContainer');
    console.log('📋 loadHistory called');
    console.log('🔑 currentUserid:', currentUserid);
    console.log('🎯 API URL:', `${API_BASE_URL}/books/user/${currentUserid}/history`);
    console.log('📌 Container element:', container);
    
    try {
        const url = `${API_BASE_URL}/books/user/${currentUserid}/history`;
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
            const hist = data.history || [];
            console.log('✅ History entries count:', hist.length);
            
            if (hist.length === 0) {
                console.log('ℹ️ No history entries');
                container.innerHTML = `
                    <div class="no-data">
                        <div class="no-data-icon">📚</div>
                        <h3>No History Yet</h3>
                        <p>Your borrowed and returned books will appear here</p>
                    </div>
                `;
            } else {
                console.log('🏗️ Building table with', hist.length, 'entries');
                const wrapper = document.createElement('div');
                wrapper.className = 'history-table-wrapper';
                
                const table = document.createElement('table');
                table.className = 'history-table';
                
                // Create header
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th style="width: 25%">Title</th>
                        <th style="width: 15%">Author</th>
                        <th style="width: 12%">Borrowed</th>
                        <th style="width: 12%">Due Date</th>
                        <th style="width: 12%">Returned</th>
                        <th style="width: 12%">Status</th>
                    </tr>
                `;
                table.appendChild(thead);
                
                // Create body
                const tbody = document.createElement('tbody');
                hist.forEach((entry, idx) => {
                    console.log(`📄 Processing entry ${idx}:`, entry);
                    const row = document.createElement('tr');
                    const statusClass = entry.status === 'returned' ? 'returned' : 'borrowed';
                    const statusText = entry.status === 'returned' ? '✓ Returned' : '⏳ Borrowed';
                    
                    row.innerHTML = `
                        <td class="title">${escapeHtml(entry.title)}</td>
                        <td class="author">${escapeHtml(entry.author || 'N/A')}</td>
                        <td>${entry.borrowdate}</td>
                        <td>${entry.duedate}</td>
                        <td>${entry.returndate || '—'}</td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
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
                    <h3>Error Loading History</h3>
                    <p>${escapeHtml(data.message || 'Failed to load your history')}</p>
                </div>
            `;
        }
    } catch (e) {
        console.error('❌ History load error:', e);
        console.error('📍 Error details:', e.message, e.stack);
        container.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">🔌</div>
                <h3>Network Error</h3>
                <p>Unable to connect to the server. Please try again.</p>
            </div>
        `;
    }
}

// simple escape helper
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