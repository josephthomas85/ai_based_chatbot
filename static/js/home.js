// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const logoutBtn = document.getElementById('logoutBtn');
const userName = document.getElementById('userName');
// quick actions replaced by sidebar, may not exist
const quickActionButtons = document.querySelectorAll('.action-btn');
// modal elements may not exist on dashboard
const bookModal = document.getElementById('bookModal');
const booksList = document.getElementById('booksList');
const modalTitle = document.getElementById('modalTitle');
const modalAction = document.getElementById('modalAction');
const modalClose = document.querySelector('.modal-close');
const loadingSpinner = document.getElementById('loadingSpinner');

// detect whether we are on the chat view or dashboard
const isChatView = !!chatInput;

// State Management
let currentAction = null;
let selectedBookId = null;
let allBooks = [];
let conversationContext = '';  // Track conversation context (e.g., waiting_for_book)
let notifications = [];  // store fetched notifications
let overdueDetails = [];  // store overdue book details for fee breakdown
let overdueFeeTotal = 0;  // cached overall fee total for popup
let persistentFines = 0;  // cached unpaid persistent fines

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const userid = localStorage.getItem('userid');
    const fullname = localStorage.getItem('fullname');
    
    if (!userid) {
        window.location.href = '/login';
        return;
    }
    
    userName.textContent = `Welcome, ${fullname}!`;

    loadNotifications();

    // Set up chat event listeners always (since views can be switched)
    if (sendBtn && chatInput) {
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // load dashboard metrics
    if (!isChatView) {
        loadDashboardData();

        // show fee breakdown when user taps the card
        const feeCard = document.getElementById('feeCard');
        if (feeCard) {
            feeCard.addEventListener('click', () => {
                showFeeModal();
            });
        }

        // close modal controls
        const feeModal = document.getElementById('feeModal');
        const feeModalClose = document.getElementById('feeModalClose');
        const feeModalCloseBtn = document.getElementById('feeModalCloseBtn');
        const feeModalPayBtn = document.getElementById('feeModalPayBtn');

        if (feeModal) {
            feeModal.addEventListener('click', (evt) => {
                if (evt.target === feeModal) {
                    feeModal.style.display = 'none';
                }
            });
        }
        if (feeModalClose) {
            feeModalClose.addEventListener('click', () => {
                feeModal.style.display = 'none';
            });
        }
        if (feeModalCloseBtn) {
            feeModalCloseBtn.addEventListener('click', () => {
                feeModal.style.display = 'none';
            });
        }
        if (feeModalPayBtn) {
            feeModalPayBtn.addEventListener('click', () => {
                payFines();
            });
        }
    }
    if (modalAction) modalAction.addEventListener('click', confirmModalAction);

    // Logout button listeners - handle both navbar and sidebar buttons
    document.querySelectorAll('#logoutBtn, #sidebarLogoutBtn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });

    // sidebar nav links - now redirect to separate pages
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = e.currentTarget.getAttribute('href');
            if (href === '#') {
                e.preventDefault();
                // This should not happen anymore since we updated the links
            }
        });
    });
});

// Send Chat Message
async function sendMessage() {
    if (!isChatView) return; // no-op on dashboard
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
            
            // Store books if returned
            if (data.data && data.data.length > 0) {
                allBooks = data.data;
            }
            // refresh notifications (e.g., restock triggered)
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
    if (!isChatView) return; // ignore when not chat
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
            content += `<button class="suggestion-btn" onclick="chatInput.value='${escapeHtml(suggestion)}'; sendMessage();">
                ${escapeHtml(suggestion)}
            </button>`;
        });
        content += '</div>';
    }
    
    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle Quick Actions
function handleQuickAction(e) {
    if (!isChatView) return;
    const action = e.currentTarget.getAttribute('data-action');
    conversationContext = '';  // Reset context for new action
    
    // Update active button
    quickActionButtons.forEach(btn => btn.classList.remove('active'));
    e.currentTarget.classList.add('active');
    
    switch (action) {
        case 'show-all':
            chatInput.value = 'Show all books';
            sendMessage();
            break;
        case 'search':
            chatInput.focus();
            chatInput.placeholder = 'Search for a book (e.g., "Python")...';
            break;
        case 'borrow':
            chatInput.value = 'Borrow book';
            sendMessage();
            break;
        case 'return':
            chatInput.value = 'Return book';
            sendMessage();
            break;
        case 'my-books':
            showMyBooks();
            break;
        case 'status':
            chatInput.value = 'Check book status';
            sendMessage();
            break;
    }
}

// Notifications
async function loadNotifications() {
    try {
        const response = await fetch(`${API_BASE_URL}/notifications`, { method: 'GET' });
        const data = await response.json();
        if (data.success) {
            notifications = data.notifications || [];
            updateNotificationBadge();
            // always refresh dashboard metrics, even if hidden
            const count = notifications.filter(n => !n.read).length;
            const el = document.getElementById('cardAlerts');
            if (el) el.textContent = count;
            loadDashboardData();
        }
    } catch (err) {
        console.error('Failed to load notifications', err);
    }
}

function updateNotificationBadge() {
    const count = notifications.filter(n => !n.read).length;
    const badge = document.getElementById('notificationCount');
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

async function loadDashboardData() {
    const userid = localStorage.getItem('userid');
    try {
        const resp = await fetch(`${API_BASE_URL}/books/user/${userid}/borrowed`, { method: 'GET' });
        const data = await resp.json();
        if (data.success) {
            const borrowed = data.borrowedbooks || [];
            document.getElementById('cardBooksIssued').textContent = borrowed.length;
            // calculate overdue and fees
            const today = new Date();
            let overdueCount = 0;
            let feeTotal = 0;
            overdueDetails = [];
            const issuedContainer = document.getElementById('issuedList');
            issuedContainer.innerHTML = '';
            borrowed.forEach(b => {
                const due = new Date(b.duedate);
                const item = document.createElement('div');
                item.className = 'issued-book-item';
                item.textContent = `${b.title} by ${b.author} – Due: ${b.duedate}`;
                issuedContainer.appendChild(item);
                if (due < today) {
                    overdueCount++;
                    const days = Math.ceil((today - due)/ (1000*60*60*24));
                    const fine = days * 1; // ₹1 per day
                    feeTotal += fine;
                    overdueDetails.push({
                        title: b.title,
                        author: b.author,
                        duedate: b.duedate,
                        daysOverdue: days,
                        fineAmount: fine
                    });
                }
            });
            persistentFines = data.unpaid_fines || 0;
            overdueFeeTotal = feeTotal + persistentFines;
            document.getElementById('cardOverdue').textContent = overdueCount;
            document.getElementById('cardFees').textContent = `₹${overdueFeeTotal}`;
            document.getElementById('cardAlerts').textContent = notifications.filter(n => !n.read).length;
            // populate alerts list from notifications
            const alertsList = document.getElementById('alertsList');
            alertsList.innerHTML = '';
            notifications.slice(-5).forEach(n => {
                const row = document.createElement('div');
                row.className = 'alert-item';
                row.textContent = n.message;
                alertsList.appendChild(row);
            });
        }
    } catch (err) {
        console.error('Dashboard load failed', err);
    }
}

function showFeeModal() {
    const modal = document.getElementById('feeModal');
    const detailsEl = document.getElementById('feeDetails');
    if (!modal || !detailsEl) return;

    if (!overdueDetails || overdueDetails.length === 0) {
        detailsEl.innerHTML = `
            <div style="text-align:center; padding: 20px;">
                <div style="font-size: 32px; margin-bottom: 12px;">✅</div>
                <div style="font-weight: 600; margin-bottom: 8px;">No overdue books</div>
                <div>You're all caught up — no fines to pay.</div>
            </div>
        `;
    } else {
        const rows = overdueDetails.map(d => `
            <tr>
                <td>${escapeHtml(d.title)}</td>
                <td>${escapeHtml(d.author)}</td>
                <td style="text-align:center;">${d.daysOverdue}</td>
                <td style="text-align:right;">₹${d.fineAmount}</td>
            </tr>
        `).join('');

        detailsEl.innerHTML = `
            <div style="margin-bottom: 16px;">
                <div style="font-weight: 600;">Previous Unpaid Fines</div>
                <div style="font-size: 18px; color: #787878;">₹${persistentFines}</div>
            </div>
            <div style="margin-bottom: 16px;">
                <div style="font-weight: 600;">Total Fine (Including Active)</div>
                <div style="font-size: 22px; color: #787878;">₹${overdueFeeTotal}</div>
            </div>
            
            <div style="max-height: 280px; overflow-y: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="text-align:left; border-bottom: 1px solid #e0e0e0;">
                            <th>Title</th>
                            <th>Author</th>
                            <th style="text-align:center;">Days Late</th>
                            <th style="text-align:right;">Fine</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }

    const payBtn = document.getElementById('feeModalPayBtn');
    if (payBtn) payBtn.style.display = persistentFines > 0 ? 'inline-block' : 'none';

    modal.style.display = 'flex';
}

function showNotifications() {
    if (notifications.length === 0) {
        addMessageToChat('You have no notifications.', 'bot');
        return;
    }
    const unreadIds = [];
    notifications.forEach(n => {
        addMessageToChat(n.message, 'bot');
        if (!n.read) unreadIds.push(n.id);
        n.read = true;
    });
    if (unreadIds.length > 0) {
        fetch(`${API_BASE_URL}/notifications/mark_read`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ userid: localStorage.getItem('userid'), ids: unreadIds })
        }).catch(e => console.error('mark read failed', e));
    }
    updateNotificationBadge();
}

// Display my books view
async function showMyBooksView() {
    // display view
    document.getElementById('myBooksView').style.display = '';
    document.getElementById('dashboardView').style.display = 'none';
    document.getElementById('chatView').style.display = 'none';
    document.getElementById('aiView').style.display = 'none';
    // update metrics when viewing
    loadDashboardData();
    const userid = localStorage.getItem('userid');
    const container = document.getElementById('myBooksList');
    container.innerHTML = '<p>Loading...</p>';
    try {
        const resp = await fetch(`${API_BASE_URL}/books/user/${userid}/borrowed`, {method: 'GET'});
        const data = await resp.json();
        if (data.success) {
            const books = data.borrowedbooks || [];
            if (books.length === 0) {
                container.innerHTML = '<p>You have no borrowed books.</p>';
            } else {
                container.innerHTML = '';
                books.forEach(b => {
                    const div = document.createElement('div');
                    div.className = 'issued-book-item';
                    div.textContent = `${b.title} by ${b.author} (Due: ${b.duedate})`;
                    container.appendChild(div);
                });
            }
        } else {
            container.innerHTML = '<p>Error loading books.</p>';
        }
    } catch (err) {
        console.error('Failed to load my books', err);
        container.innerHTML = '<p>Network error.</p>';
    }
}

// Display AI recommendations view
async function showAIRecommendations() {
    // show view
    document.getElementById('aiView').style.display = '';
    document.getElementById('dashboardView').style.display = 'none';
    document.getElementById('chatView').style.display = 'none';
    document.getElementById('myBooksView').style.display = 'none';
    loadDashboardData();
    const container = document.getElementById('aiList');
    container.innerHTML = '<p>Loading recommendations...</p>';
    try {
        const resp = await fetch(`${API_BASE_URL}/books`, {method:'GET'});
        const data = await resp.json();
        if (data.success) {
            const books = data.books || [];
            // pick up to 3 random books
            const recs = [];
            for (let i=0; i<3 && books.length>0; i++){
                const idx = Math.floor(Math.random()*books.length);
                recs.push(books.splice(idx,1)[0]);
            }
            if (recs.length === 0) {
                container.innerHTML = '<p>No recommendations available.</p>';
            } else {
                container.innerHTML = '';
                recs.forEach(b => {
                    const div = document.createElement('div');
                    div.className = 'issued-book-item';
                    div.textContent = `${b.title} by ${b.author}`;
                    container.appendChild(div);
                });
            }
        } else {
            container.innerHTML = '<p>Failed to load recommendations.</p>';
        }
    } catch (err) {
        console.error('AI load error', err);
        container.innerHTML = '<p>Network error.</p>';
    }
}

// Show Return Modal
async function showReturnModal() {
    currentAction = 'return';
    conversationContext = '';  // Reset context
    modalTitle.textContent = 'Select a Book to Return';
    booksList.innerHTML = '';
    
    showLoading(true);
    
    try {
        const userid = localStorage.getItem('userid');
        const response = await fetch(`${API_BASE_URL}/books/user/${userid}/borrowed`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.borrowedbooks) {
            if (data.borrowedbooks.length === 0) {
                booksList.innerHTML = '<p>You have no borrowed books to return.</p>';
            } else {
                data.borrowedbooks.forEach(book => {
                    const bookDiv = document.createElement('div');
                    bookDiv.className = 'book-item';
                    bookDiv.innerHTML = `
                        <input type="radio" name="book" value="${book.bookid}">
                        <span class="book-title">${escapeHtml(book.title)}</span>
                        <div class="book-author">${escapeHtml(book.author)} - Due: ${book.duedate}</div>
                    `;
                    booksList.appendChild(bookDiv);
                });
            }
        }
        
        openModal();
    } catch (error) {
        console.error('Error loading borrowed books:', error);
        booksList.innerHTML = '<p>Error loading your books. Please try again.</p>';
        openModal();
    } finally {
        showLoading(false);
    }
}

// Show My Books
async function showMyBooks() {
    conversationContext = '';  // Reset context
    const userid = localStorage.getItem('userid');
    
    addMessageToChat('Loading your borrowed books...', 'bot');
    
    try {
        const response = await fetch(`${API_BASE_URL}/books/user/${userid}/borrowed`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.borrowedbooks) {
            if (data.borrowedbooks.length === 0) {
                addMessageToChat('You currently have no borrowed books.', 'bot');
            } else {
                const message = `You have ${data.borrowedbooks.length} borrowed book(s):`;
                addMessageToChat(message, 'bot', data.borrowedbooks, ['Borrow another book', 'Return a book']);
            }
        }
    } catch (error) {
        console.error('Error loading borrowed books:', error);
        addMessageToChat('Error loading your books. Please try again.', 'bot');
    }
}

// Confirm Modal Action
async function confirmModalAction() {
    const selectedRadio = document.querySelector('input[name="book"]:checked');
    
    if (!selectedRadio) {
        alert('Please select a book');
        return;
    }
    
    const bookId = selectedRadio.value;
    const userid = localStorage.getItem('userid');
    
    showLoading(true);
    closeModal();
    
    try {
        const endpoint = currentAction === 'borrow' ? '/books/borrow' : '/books/return';
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userid, bookid: bookId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const action = currentAction === 'borrow' ? 'borrowed' : 'returned';
            const bookTitle = selectedRadio.nextElementSibling.textContent;
            addMessageToChat(`Successfully ${action} "${bookTitle}"!`, 'bot', [], ['Show all books', 'View my books']);
            // refresh dashboard and notifications
            loadNotifications();
        } else {
            addMessageToChat(`Error: ${data.message}`, 'bot');
        }
    } catch (error) {
        console.error('Action error:', error);
        addMessageToChat('Error processing request. Please try again.', 'bot');
    } finally {
        showLoading(false);
    }
}

// Modal Functions
function openModal() {
    bookModal.style.display = 'flex';
}

function closeModal() {
    bookModal.style.display = 'none';
    selectedBookId = null;
}

// Logout
function logout() {
    fetch(`${API_BASE_URL}/logout`, { method: 'POST' })
        .then(() => {
            localStorage.removeItem('userid');
            localStorage.removeItem('username');
            localStorage.removeItem('fullname');
            window.location.href = '/login';
        })
        .catch(error => {
            console.error('Logout error:', error);
            window.location.href = '/login';
        });
}

// Show/Hide Loading
function showLoading(show) {
    loadingSpinner.style.display = show ? 'flex' : 'none';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
bookModal.addEventListener('click', (e) => {
    if (e.target === bookModal) {
        closeModal();
    }
});

// Pay Fines API
async function payFines() {
    try {
        const response = await fetch(`${API_BASE_URL}/pay_fines`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            alert('Fines paid successfully!');
            document.getElementById('feeModal').style.display = 'none';
            loadDashboardData();
        } else {
            alert(data.message || 'Error paying fines.');
        }
    } catch (e) {
        console.error(e);
        alert('Network error while paying fines.');
    }
}
