const API_BASE = '/api/staff';
let allBooks = [];


window.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    pollRequestBadge();

    document.getElementById('logoutBtn').addEventListener('click', async (e) => {
        e.preventDefault();
        await fetch(`${API_BASE}/logout`, { method: 'POST' });
        window.location.href = '/staff';
    });

    // Modal closes
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });

    // Edit Form submit
    document.getElementById('editUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);
        const payload = {
            userid: document.getElementById('editUid').value,
            fullname: document.getElementById('editName').value,
            email: document.getElementById('editEmail').value,
            unpaid_fines: document.getElementById('editFines').value
        };
        try {
            const res = await fetch(`${API_BASE}/user/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('editModal').style.display = 'none';
                loadUsers();
            } else {
                alert('Failed to update user');
            }
        } catch (e) { console.error(e); }
        finally { showLoading(false); }
    });

    // Assign Book submit
    document.getElementById('assignBookForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);
        const payload = {
            userid: document.getElementById('assignUid').value,
            bookid: document.getElementById('assignBookId').value
        };
        try {
            const res = await fetch(`${API_BASE}/assign_book`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            alert(data.message);
            if (data.success) {
                document.getElementById('assignModal').style.display = 'none';
                loadUsers();
            }
        } catch (e) { console.error(e); }
        finally { showLoading(false); }
    });
    // Book search listener
    document.getElementById('bookSearchInput')?.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const filtered = allBooks.filter(b => 
            String(b.title || '').toLowerCase().includes(query) ||
            String(b.author || '').toLowerCase().includes(query) ||
            String(b.category || '').toLowerCase().includes(query) ||
            String(b.bookid || '').toLowerCase().includes(query)
        );
        renderBooks(filtered);
    });

    // Add Book Modal logic
    const addBookModal = document.getElementById('addBookModal');
    const openAddBookBtn = document.getElementById('openAddBookModalBtn');
    const closeAddBookBtn = document.getElementById('addBookModalClose');
    const addBookForm = document.getElementById('addBookForm');

    if (openAddBookBtn) {
        openAddBookBtn.onclick = () => {
            addBookForm.reset();
            addBookModal.style.display = 'flex';
        };
    }

    if (closeAddBookBtn) {
        closeAddBookBtn.onclick = () => {
            addBookModal.style.display = 'none';
        };
    }

    if (addBookForm) {
        addBookForm.onsubmit = async (e) => {
            e.preventDefault();
            showLoading(true);
            const payload = {
                title: document.getElementById('addBookTitle').value,
                author: document.getElementById('addBookAuthor').value,
                isbn: document.getElementById('addBookIsbn').value,
                category: document.getElementById('addBookCategory').value,
                publicationyear: document.getElementById('addBookYear').value,
                totalcopies: document.getElementById('addBookCopies').value,
                location: document.getElementById('addBookLocation').value
            };
            try {
                const res = await fetch('/api/staff/book/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    addBookModal.style.display = 'none';
                    alert(data.message);
                    loadBooks(); // Refresh the list
                } else {
                    alert(data.message || 'Failed to add book');
                }
            } catch (err) {
                console.error(err);
                alert('Connection error. Could not add book.');
            } finally {
                showLoading(false);
            }
        };
    }
});

// ──────────────── Tab switching ────────────────
function switchTab(tab, el) {
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
    if (el) el.classList.add('active');

    document.getElementById('rosterSection').style.display   = (tab === 'roster')   ? 'block' : 'none';
    document.getElementById('requestsSection').style.display = (tab === 'requests') ? 'block' : 'none';
    document.getElementById('returnsSection').style.display  = (tab === 'returns')  ? 'block' : 'none';
    document.getElementById('booksSection').style.display    = (tab === 'books')    ? 'block' : 'none';

    const titles = { 
        roster: 'Student Master List', 
        requests: 'Borrow Requests', 
        returns: 'Return Approvals',
        books: 'Books Catalogue' 
    };
    document.getElementById('pageTitle').textContent = titles[tab] || '';

    if (tab === 'roster')   loadUsers();
    if (tab === 'requests') loadBorrowRequests();
    if (tab === 'returns')  loadReturnRequests();
    if (tab === 'books')    loadBooks();
}

// ──────────────── Students ────────────────
async function loadUsers() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/users`);
        if (res.status === 401) { window.location.href = '/staff'; return; }
        const data = await res.json();
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = '';

        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No students found.</td></tr>';
            return;
        }

        data.users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.userid}</td>
                <td><strong>${esc(u.fullname)}</strong></td>
                <td>${esc(u.username)}</td>
                <td>${esc(u.email)}</td>
                <td><span style="font-weight:bold; color:#aaa;">${u.active_borrows}</span> book(s)</td>
                <td style="color:${u.unpaid_fines > 0 ? '#ef4444' : '#aaa'}; font-weight:bold;">₹${u.unpaid_fines}</td>
                <td class="action-links">
                    <button class="btn-edit" onclick="openEditModal('${u.userid}','${esc(u.fullname)}','${esc(u.email)}',${u.unpaid_fines})">Edit</button>
                    <button class="btn-assign" onclick="openAssignModal('${u.userid}','${esc(u.fullname)}')">Assign Book</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

// ──────────────── Borrow Requests ────────────────
async function loadBorrowRequests() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/requests`);
        const data = await res.json();
        const tbody = document.getElementById('requestsTableBody');
        const badge = document.getElementById('requestBadge');

        tbody.innerHTML = '';

        if (!data.requests || data.requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No pending requests</td></tr>';
            badge.style.display = 'none';
            return;
        }

        badge.textContent = data.requests.length;
        badge.style.display = 'inline-block';

        data.requests.forEach(r => {
            const tr = document.createElement('tr');
            const isApproved = r.status === 'approved';
            const isQueued   = r.status === 'queued';

            let statusBadge = '';
            if (r.status === 'requested') statusBadge = `<span class="status-badge status-requested">REQUESTED</span>`;
            if (isQueued)   statusBadge = `<span class="status-badge status-queued">QUEUED</span>`;
            if (isApproved) statusBadge = `<span class="status-badge status-approved">APPROVED</span>`;

            const deadlineRow = isApproved && r.pickup_deadline
                ? `<br><span class="pickup-deadline">Collect by: ${r.pickup_deadline}</span>`
                : '';

            const actions = isApproved
                ? `<button class="btn-collected" onclick="markCollected('${r.transactionid}')">Mark Collected</button>
                   <button class="btn-reject" onclick="rejectRequest('${r.transactionid}')">Reject</button>`
                : `<button class="btn-approve" onclick="approveRequest('${r.transactionid}')">Approve</button>
                   <button class="btn-reject" onclick="rejectRequest('${r.transactionid}')">Reject</button>`;

            tr.innerHTML = `
                <td>${r.transactionid}</td>
                <td><strong>${esc(r.fullname)}</strong><br><small>${esc(r.userid)}</small></td>
                <td><a href="/staff/book/${r.bookid}" style="color:#aaa;text-decoration:none;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#aaa'">${esc(r.title)}</a><br><small>${r.bookid}</small></td>
                <td>${r.date}</td>
                <td>${statusBadge}${deadlineRow}</td>
                <td class="action-links">${actions}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

async function approveRequest(txid) {
    if (!confirm('Approve this borrow request? The student will have 1 working day to collect the book.')) return;
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/request/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transactionid: txid })
        });
        const data = await res.json();
        alert(data.message);
        if (data.success) loadBorrowRequests();
        else alert(data.message);
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

async function markCollected(txid) {
    if (!confirm('Confirm that the student has physically collected this book?')) return;
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/request/collected`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transactionid: txid })
        });
        const data = await res.json();
        if (data.success) {
            loadBorrowRequests();
        } else {
            alert(data.message);
        }
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

async function rejectRequest(txid) {
    if (!confirm('Are you sure you want to REJECT this request?')) return;
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/request/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transactionid: txid })
        });
        if (res.ok) loadBorrowRequests();
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

// ──────────────── Return Approvals ────────────────
async function loadReturnRequests() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/returns`);
        const data = await res.json();
        const tbody = document.getElementById('returnsTableBody');
        const badge = document.getElementById('returnBadge');

        tbody.innerHTML = '';

        if (!data.returns || data.returns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No pending returns</td></tr>';
            badge.style.display = 'none';
            return;
        }

        badge.textContent = data.returns.length;
        badge.style.display = 'inline-block';

        data.returns.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.transactionid}</td>
                <td><strong>${esc(r.fullname)}</strong><br><small>${esc(r.userid)}</small></td>
                <td><strong>${esc(r.title)}</strong><br><small>${r.bookid}</small></td>
                <td>${r.borrowdate}</td>
                <td>${r.returndate}</td>
                <td class="action-links">
                    <button class="btn-approve" onclick="approveReturn('${r.transactionid}')">Approve Return</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

async function approveReturn(txid) {
    if (!confirm('Approve this return? The book will be marked as available in the catalog.')) return;
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/return/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transactionid: txid })
        });
        const data = await res.json();
        alert(data.message);
        if (data.success) loadReturnRequests();
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

async function expireApprovals() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/expire_approvals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        alert(data.message);
        loadBorrowRequests();
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

// ──────────────── Books Catalogue ────────────────
async function loadBooks() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/books`);
        const data = await res.json();
        allBooks = data.books || [];
        renderBooks(allBooks);
    } catch (e) { console.error(e); }
    finally { showLoading(false); }
}

function renderBooks(booksList) {
    const tbody = document.getElementById('booksTableBody');
    tbody.innerHTML = '';

    if (!booksList || booksList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No books found matching the criteria.</td></tr>';
        return;
    }

    booksList.forEach(b => {
        const avail = b.availablecopies;
        const total = b.totalcopies || '?';
        const isAvail = avail > 0;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><small>${b.bookid}</small></td>
            <td><strong>${esc(b.title)}</strong></td>
            <td>${esc(b.author)}</td>
            <td>${esc(b.category || 'General')}</td>
            <td style="font-weight:bold;color:${isAvail?'#4ade80':'#ef4444'};">${avail} / ${total}</td>
            <td><span class="status-badge ${isAvail ? 'status-requested' : 'status-queued'}" style="${isAvail?'background:#0f1225;color:#93c5fd;border:1px solid #1e40af;':'background:#200;color:#f87171;border:1px solid #7f1d1d;'}">${isAvail ? 'AVAILABLE' : 'UNAVAILABLE'}</span></td>
            <td class="action-links">
                <a href="/staff/book/${b.bookid}" class="btn-edit" style="text-decoration:none;display:inline-block;">View Details</a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ──────────────── Modals ────────────────
function openEditModal(uid, name, email, fines) {
    document.getElementById('editUid').value   = uid;
    document.getElementById('editName').value  = name;
    document.getElementById('editEmail').value = email;
    document.getElementById('editFines').value = fines;
    document.getElementById('editModal').style.display = 'flex';
}

async function openAssignModal(uid, name) {
    document.getElementById('assignUid').value = uid;
    document.getElementById('assignUidDisplay').textContent = `${name} (${uid})`;

    const select = document.getElementById('assignBookId');
    select.innerHTML = '<option value="">Loading books...</option>';
    document.getElementById('assignModal').style.display = 'flex';

    try {
        const res = await fetch(`${API_BASE}/books`);
        if (res.ok) {
            const data = await res.json();
            select.innerHTML = '<option value="">-- Choose an Available Book --</option>';
            data.books.filter(b => b.availablecopies > 0).forEach(b => {
                select.innerHTML += `<option value="${b.bookid}">${esc(b.title)} by ${esc(b.author)} (Copies: ${b.availablecopies})</option>`;
            });
        } else {
            select.innerHTML = '<option value="">No books loaded.</option>';
        }
    } catch (e) { console.error(e); }
}

// ──────────────── Helpers ────────────────
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

function esc(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}

// Badge polling
async function pollRequestBadge() {
    try {
        // Poll Borrow Requests
        const resReq = await fetch(`${API_BASE}/requests`);
        const dataReq = await resReq.json();
        const badgeReq = document.getElementById('requestBadge');
        if (dataReq.requests && dataReq.requests.length > 0) {
            badgeReq.textContent = dataReq.requests.length;
            badgeReq.style.display = 'inline-block';
        } else {
            badgeReq.style.display = 'none';
        }

        // Poll Return Requests
        const resRet = await fetch(`${API_BASE}/returns`);
        const dataRet = await resRet.json();
        const badgeRet = document.getElementById('returnBadge');
        if (dataRet.returns && dataRet.returns.length > 0) {
            badgeRet.textContent = dataRet.returns.length;
            badgeRet.style.display = 'inline-block';
        } else {
            badgeRet.style.display = 'none';
        }
    } catch (e) {}
    setTimeout(pollRequestBadge, 30000);
}
