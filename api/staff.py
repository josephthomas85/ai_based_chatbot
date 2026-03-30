from flask import Blueprint, request, jsonify, session
import json
import bcrypt
import random
from datetime import datetime, timedelta
from functools import wraps
from config import Config
from api.notifications import add_notification
from api.books import count_active_borrows

staff_bp = Blueprint('staff_api', __name__, url_prefix='/api/staff')

def load_db(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_db(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_users(): return load_db(Config.USERS_DB) or {"users": []}
def load_books(): return load_db(Config.BOOKS_DB) or {"books": []}
def load_transactions(): return load_db(Config.TRANSACTIONS_DB) or {"transactions": []}

def save_users(data): save_db(Config.USERS_DB, data)
def save_books(data): save_db(Config.BOOKS_DB, data)
def save_transactions(data): save_db(Config.TRANSACTIONS_DB, data)

def require_staff_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'staff_id' not in session:
            return jsonify({"success": False, "message": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function

def next_working_day(from_date=None):
    """Returns the date of the next working day (Mon–Sat, skip Sunday)."""
    d = from_date or datetime.now()
    d = d + timedelta(days=1)
    # Skip Sunday (weekday 6)
    if d.weekday() == 6:
        d = d + timedelta(days=1)
    return d.strftime('%Y-%m-%d')

# ──────────────── Auth ────────────────
@staff_bp.route('/login', methods=['POST'])
def staff_login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "message": "Missing credentials"}), 400
        
    users_data = load_users()
    user = next((u for u in users_data['users'] if u['username'] == data['username']), None)
    
    if not user or user.get('role') != 'staff':
        return jsonify({"success": False, "message": "Invalid staff credentials"}), 401
        
    if not bcrypt.checkpw(data['password'].encode(), user['password'].encode()):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
    session['staff_id'] = user['userid']
    session['staff_name'] = user['fullname']
    return jsonify({"success": True, "message": "Staff login successful"}), 200

@staff_bp.route('/logout', methods=['POST'])
def staff_logout():
    session.pop('staff_id', None)
    session.pop('staff_name', None)
    return jsonify({"success": True, "message": "Logged out"}), 200

# ──────────────── Users ────────────────
@staff_bp.route('/users', methods=['GET'])
@require_staff_login
def get_all_users():
    users_data = load_users()
    tx_data = load_transactions()
    
    formatted_users = []
    for u in users_data['users']:
        if u.get('role') == 'staff': continue
        active_borrows = sum(1 for t in tx_data['transactions']
                             if t['userid'] == u['userid'] and t['status'] in ['borrowed', 'approved'])
        formatted_users.append({
            "userid": u['userid'],
            "username": u['username'],
            "fullname": u['fullname'],
            "email": u.get('email', ''),
            "unpaid_fines": u.get('unpaid_fines', 0),
            "registereddate": u.get('registereddate', ''),
            "active_borrows": active_borrows
        })
    return jsonify({"success": True, "users": formatted_users}), 200

@staff_bp.route('/user/update', methods=['POST'])
@require_staff_login
def update_user():
    data = request.get_json()
    userid = data.get('userid')
    if not userid:
        return jsonify({"success": False, "message": "Missing userid"}), 400
        
    users_data = load_users()
    user = next((u for u in users_data['users'] if u['userid'] == userid), None)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    if 'fullname' in data: user['fullname'] = data['fullname']
    if 'email' in data: user['email'] = data['email']
    if 'unpaid_fines' in data: user['unpaid_fines'] = int(data['unpaid_fines'])
    
    save_users(users_data)
    return jsonify({"success": True, "message": "User updated successfully"}), 200

# ──────────────── Books ────────────────
@staff_bp.route('/books', methods=['GET'])
@require_staff_login
def get_all_books_staff():
    books_data = load_books()
    return jsonify({"success": True, "books": books_data['books']}), 200

@staff_bp.route('/book/<bookid>', methods=['GET'])
@require_staff_login
def get_book_details(bookid):
    """Full details page data for a single book: copies, active borrowers, pending requests."""
    books_data = load_books()
    users_data = load_users()
    tx_data = load_transactions()

    book = next((b for b in books_data['books'] if b['bookid'] == bookid), None)
    if not book:
        return jsonify({"success": False, "message": "Book not found"}), 404

    # People currently holding / awaiting collection
    active_holders = []
    # People with pending requests (requested / queued / approved)
    pending_requests = []

    for t in tx_data['transactions']:
        if t['bookid'] != bookid:
            continue
        user = next((u for u in users_data['users'] if u['userid'] == t['userid']), {})
        entry = {
            "transactionid": t['transactionid'],
            "userid": t['userid'],
            "fullname": user.get('fullname', 'Unknown'),
            "username": user.get('username', ''),
            "status": t['status'],
            "borrowdate": t.get('borrowdate', ''),
            "duedate": t.get('duedate', ''),
            "pickup_deadline": t.get('pickup_deadline', ''),
            "returndate": t.get('returndate', '')
        }

        if t['status'] == 'borrowed':
            active_holders.append(entry)
        elif t['status'] == 'approved':
            # Awaiting physical collection
            entry['pickup_deadline'] = t.get('pickup_deadline', '')
            active_holders.append(entry)
        elif t['status'] in ['requested', 'queued']:
            pending_requests.append(entry)

    # Sort pending by FIFO
    pending_requests.sort(key=lambda x: x['transactionid'])

    return jsonify({
        "success": True,
        "book": book,
        "active_holders": active_holders,
        "pending_requests": pending_requests,
        "total_copies": book.get('totalcopies', book.get('availablecopies', 0) + len(active_holders)),
        "available_copies": book.get('availablecopies', 0)
    }), 200

@staff_bp.route('/book/add', methods=['POST'])
@require_staff_login
def add_new_book():
    """Adds a completely new book to the library catalog."""
    data = request.get_json()
    if not data or not data.get('title') or not data.get('author'):
        return jsonify({"success": False, "message": "Missing required fields (Title and Author)"}), 400
        
    books_data = load_books()
    
    # Generate new book ID: BKXXXXX
    # We find the maximum numeric ID currently in use and increment it.
    max_id = 10  # Fallback starting point if none exist
    for b in books_data['books']:
        try:
            bid = str(b['bookid'])
            if bid.startswith('BK'):
                num = int(bid[2:])
                if num > max_id:
                    max_id = num
        except (ValueError, IndexError):
            continue
            
    new_id_num = max_id + 1
    new_bookid = f"BK{str(new_id_num).zfill(5)}"
    
    total_copies = int(data.get('totalcopies', 1))
    
    new_book = {
        "bookid": new_bookid,
        "title": data.get('title'),
        "author": data.get('author'),
        "isbn": data.get('isbn', ''),
        "category": data.get('category', 'General'),
        "publicationyear": int(data.get('publicationyear', datetime.now().year)),
        "totalcopies": total_copies,
        "availablecopies": total_copies,
        "status": "available" if total_copies > 0 else "unavailable",
        "location": data.get('location', 'Unassigned')
    }
    
    books_data['books'].insert(0, new_book)  # Insert at top for visibility
    save_books(books_data)
    
    return jsonify({
        "success": True, 
        "message": f"Successfully added '{new_book['title']}' with ID {new_bookid}",
        "book": new_book
    }), 201

@staff_bp.route('/assign_book', methods=['POST'])
@require_staff_login
def assign_book():
    data = request.get_json()
    userid = data.get('userid')
    bookid = data.get('bookid')
    
    if not userid or not bookid:
        return jsonify({"success": False, "message": "Missing user or book"}), 400
        
    users_data = load_users()
    if not any(u['userid'] == userid for u in users_data['users']):
        return jsonify({"success": False, "message": "User not found"}), 404
        
    books_data = load_books()
    book = next((b for b in books_data['books'] if b['bookid'] == bookid), None)
    if not book: return jsonify({"success": False, "message": "Book not found"}), 404
    if book['availablecopies'] == 0: return jsonify({"success": False, "message": "Book out of stock"}), 400
    
    tx_data = load_transactions()
    
    # Enforce 5-book limit
    if count_active_borrows(userid, tx_data) >= 5:
        return jsonify({"success": False, "message": f"User {userid} has already reached the limit of 5 books."}), 403
    
    transactionid = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
    borrowdate = datetime.now().strftime('%Y-%m-%d')
    duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    transaction = {
        "transactionid": transactionid,
        "userid": userid,
        "bookid": bookid,
        "borrowdate": borrowdate,
        "duedate": duedate,
        "returndate": None,
        "status": "borrowed"
    }
    
    book['availablecopies'] -= 1
    if book['availablecopies'] == 0: book['status'] = 'unavailable'
    
    tx_data['transactions'].append(transaction)
    save_books(books_data)
    save_transactions(tx_data)
    
    add_notification(userid, f"'{book['title']}' has been manually issued to you by the librarian. Due: {duedate}.")
    return jsonify({"success": True, "message": f"Book assigned to {userid} successfully!"}), 200

# ──────────────── Borrow Requests ────────────────
@staff_bp.route('/requests', methods=['GET'])
@require_staff_login
def get_pending_requests():
    tx_data = load_transactions()
    books_data = load_books()
    users_data = load_users()
    
    pending = []
    for t in tx_data['transactions']:
        if t['status'] in ['requested', 'queued', 'approved']:
            book = next((b for b in books_data['books'] if b['bookid'] == t['bookid']), {})
            user = next((u for u in users_data['users'] if u['userid'] == t['userid']), {})
            pending.append({
                "transactionid": t['transactionid'],
                "userid": t['userid'],
                "fullname": user.get('fullname', 'Unknown'),
                "bookid": t['bookid'],
                "title": book.get('title', 'Unknown'),
                "status": t['status'],
                "date": t.get('borrowdate', ''),
                "pickup_deadline": t.get('pickup_deadline', '')
            })
    
    pending.sort(key=lambda x: x['transactionid'])
    return jsonify({"success": True, "requests": pending}), 200

@staff_bp.route('/request/approve', methods=['POST'])
@require_staff_login
def approve_request():
    """Approve a borrow request → sets status to 'approved' with a pickup deadline of 1 working day."""
    data = request.get_json()
    txid = data.get('transactionid')
    
    tx_data = load_transactions()
    tx = next((t for t in tx_data['transactions'] if t['transactionid'] == txid), None)
    if not tx: return jsonify({"success": False, "message": "Request not found"}), 404
    if tx['status'] not in ['requested', 'queued', 'rejected']:
        return jsonify({"success": False, "message": f"Cannot approve a request with status '{tx['status']}'"}), 400
    
    books_data = load_books()
    book = next((b for b in books_data['books'] if b['bookid'] == tx['bookid']), None)
    
    # Always try to allocate a copy when approving (since borrow_book or rejection might have messed it up)
    if book and book['availablecopies'] > 0:
        book['availablecopies'] -= 1
        if book['availablecopies'] == 0:
            book['status'] = 'unavailable'
        save_books(books_data)
    else:
        # If no copies available, we can't approve it for pickup right now
        return jsonify({"success": False, "message": "Book is currently out of stock — cannot approve for pickup."}), 400

    pickup_deadline = next_working_day()
    tx['status'] = 'approved'
    tx['pickup_deadline'] = pickup_deadline

    save_transactions(tx_data)
    save_books(books_data)
    
    book_title = book['title'] if book else tx['bookid']
    add_notification(
        tx['userid'],
        f"Your request for '{book_title}' has been APPROVED! "
        f"Please collect the book from the library by {pickup_deadline}. "
        f"Your request will be automatically cancelled if not collected by this date."
    )
    
    return jsonify({"success": True, "message": f"Request approved. Student must collect by {pickup_deadline}."}), 200

@staff_bp.route('/request/collected', methods=['POST'])
@require_staff_login
def mark_collected():
    """Staff marks that the student has physically collected the book → status becomes 'borrowed'."""
    data = request.get_json()
    txid = data.get('transactionid')
    
    tx_data = load_transactions()
    tx = next((t for t in tx_data['transactions'] if t['transactionid'] == txid), None)
    if not tx: return jsonify({"success": False, "message": "Request not found"}), 404
    if tx['status'] != 'approved':
        return jsonify({"success": False, "message": "Only approved requests can be marked as collected"}), 400
    
    books_data = load_books()
    book = next((b for b in books_data['books'] if b['bookid'] == tx['bookid']), None)

    borrowdate = datetime.now().strftime('%Y-%m-%d')
    duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    tx['status'] = 'borrowed'
    tx['borrowdate'] = borrowdate
    tx['duedate'] = duedate
    tx.pop('pickup_deadline', None)

    save_transactions(tx_data)

    book_title = book['title'] if book else tx['bookid']
    add_notification(
        tx['userid'],
        f"Book collected! '{book_title}' is now checked out to you. Due date: {duedate}."
    )
    return jsonify({"success": True, "message": f"Book marked as collected. Due date: {duedate}"}), 200

@staff_bp.route('/request/reject', methods=['POST'])
@require_staff_login
def reject_request():
    data = request.get_json()
    txid = data.get('transactionid')
    reason = data.get('reason', '')
    
    tx_data = load_transactions()
    tx = next((t for t in tx_data['transactions'] if t['transactionid'] == txid), None)
    if not tx: return jsonify({"success": False, "message": "Request not found"}), 404
    
    books_data = load_books()
    book = next((b for b in books_data['books'] if b['bookid'] == tx['bookid']), None)

    # If requested or approved, restore the allocated copy
    if tx['status'] in ['requested', 'approved']:
        if book:
            book['availablecopies'] += 1
            book['status'] = 'available'
            save_books(books_data)
            
    tx['status'] = 'rejected'
    tx.pop('pickup_deadline', None)
    save_transactions(tx_data)

    book_title = book['title'] if book else tx['bookid']
    msg = f"Your request for '{book_title}' was declined."
    if reason:
        msg += f" Reason: {reason}"
    add_notification(tx['userid'], msg)
    
    return jsonify({"success": True, "message": "Request rejected"}), 200

@staff_bp.route('/expire_approvals', methods=['POST'])
@require_staff_login
def expire_approvals():
    """Auto-reject any 'approved' requests whose pickup deadline has passed."""
    tx_data = load_transactions()
    books_data = load_books()
    today = datetime.now().strftime('%Y-%m-%d')
    expired_count = 0

    for tx in tx_data['transactions']:
        if tx['status'] == 'approved':
            deadline = tx.get('pickup_deadline', '')
            if deadline and deadline < today:
                # Restore copy
                book = next((b for b in books_data['books'] if b['bookid'] == tx['bookid']), None)
                if book:
                    book['availablecopies'] += 1
                    book['status'] = 'available'
                tx['status'] = 'rejected'
                tx.pop('pickup_deadline', None)
                expired_count += 1
                add_notification(
                    tx['userid'],
                    f"Your approved borrow request for book '{book['title'] if book else tx['bookid']}' "
                    f"has been automatically cancelled because the pickup deadline passed."
                )

    if expired_count > 0:
        save_transactions(tx_data)
        save_books(books_data)

    return jsonify({"success": True, "expired": expired_count,
                    "message": f"{expired_count} overdue approval(s) expired."}), 200
@staff_bp.route('/returns', methods=['GET'])
@require_staff_login
def get_pending_returns():
    tx_data = load_transactions()
    books_data = load_books()
    users_data = load_users()
    
    pending = []
    for t in tx_data['transactions']:
        if t['status'] == 'pending_return':
            book = next((b for b in books_data['books'] if b['bookid'] == t['bookid']), {})
            user = next((u for u in users_data['users'] if u['userid'] == t['userid']), {})
            pending.append({
                "transactionid": t['transactionid'],
                "userid": t['userid'],
                "fullname": user.get('fullname', 'Unknown'),
                "bookid": t['bookid'],
                "title": book.get('title', 'Unknown'),
                "borrowdate": t.get('borrowdate', ''),
                "returndate": t.get('returndate', ''),
                "status": t['status']
            })
    
    pending.sort(key=lambda x: x['transactionid'])
    return jsonify({"success": True, "returns": pending}), 200

@staff_bp.route('/return/approve', methods=['POST'])
@require_staff_login
def approve_return():
    data = request.get_json()
    txid = data.get('transactionid')
    
    tx_data = load_transactions()
    tx = next((t for t in tx_data['transactions'] if t['transactionid'] == txid), None)
    
    if not tx:
        return jsonify({"success": False, "message": "Transaction not found"}), 404
    
    if tx['status'] != 'pending_return':
        return jsonify({"success": False, "message": "Transaction is not pending return"}), 400
    
    # Update transaction status
    tx['status'] = 'returned'
    
    # Update book availability
    books_data = load_books()
    book = next((b for b in books_data['books'] if b['bookid'] == tx['bookid']), None)
    
    if book:
        # Check for FIFO queue
        queued_request = None
        for t in tx_data['transactions']:
            if t['bookid'] == tx['bookid'] and t['status'] == 'queued':
                queued_request = t
                break
        
        if queued_request:
            # Automate next in line
            queued_request['status'] = 'approved'
            # Grant exactly 24 hours to pick up the book
            queued_request['pickup_deadline'] = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            add_notification(queued_request['userid'], f"Good news! Your waitlisted book '{book['title']}' is now available and reserved for you. You have exactly 24 hours to collect it.")
        else:
            book['availablecopies'] += 1
            book['status'] = 'available'
        
        save_books(books_data)
    
    save_transactions(tx_data)
    
    add_notification(tx['userid'], f"Your return request for '{book['title'] if book else tx['bookid']}' has been approved.")
    
    return jsonify({"success": True, "message": "Return approved successfully"}), 200
