import json
from datetime import datetime, timedelta
from flask import request, jsonify, session
from config import Config
from api.auth import require_login, load_users, save_users
from api.notifications import notify_staff, add_notification

# Load books database
def load_books():
    try:
        with open(Config.BOOKS_DB, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"books": []}

# Save books database
def save_books(data):
    with open(Config.BOOKS_DB, 'w') as f:
        json.dump(data, f, indent=2)

# Load transactions database
def load_transactions():
    try:
        with open(Config.TRANSACTIONS_DB, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"transactions": []}

# Save transactions database
def save_transactions(data):
    with open(Config.TRANSACTIONS_DB, 'w') as f:
        json.dump(data, f, indent=2)

# GET /api/books
@require_login
def get_all_books():
    books_data = load_books()
    
    # Transform response to include only necessary fields
    books_list = [
        {
            "bookid": book['bookid'],
            "title": book['title'],
            "author": book['author'],
            "category": book['category'],
            "status": book['status'],
            "availablecopies": book['availablecopies']
        }
        for book in books_data['books']
    ]
    
    return jsonify({
        "success": True,
        "books": books_list,
        "total": len(books_list)
    }), 200

# GET /api/books/<bookid>
@require_login
def get_book(bookid):
    books_data = load_books()
    
    book = None
    for b in books_data['books']:
        if b['bookid'] == bookid:
            book = b
            break
    
    if not book:
        return jsonify({"success": False, "message": "Book not found"}), 404
    
    return jsonify({
        "success": True,
        "book": {
            "bookid": book['bookid'],
            "title": book['title'],
            "author": book['author'],
            "isbn": book['isbn'],
            "category": book['category'],
            "publicationyear": book['publicationyear'],
            "totalcopies": book['totalcopies'],
            "availablecopies": book['availablecopies'],
            "status": book['status'],
            "location": book['location']
        }
    }), 200

# POST /api/books/borrow
@require_login
def borrow_book():
    data = request.get_json()
    userid = session['userid']
    bookid = data.get('bookid')
    
    if not bookid:
        return jsonify({"success": False, "message": "Book ID required"}), 400
    
    # Check if book exists and is available
    books_data = load_books()
    book = None
    book_index = None
    
    for i, b in enumerate(books_data['books']):
        if b['bookid'] == bookid:
            book = b
            book_index = i
            break
    
    if not book:
        return jsonify({"success": False, "message": "Book not found"}), 404
    
    # Determine status based on availability
    status = "requested"
    if book['availablecopies'] == 0:
        status = "queued"
    
    transactions_data = load_transactions()
    transactionid = f"TRN{len(transactions_data['transactions']) + 1:03d}"
    borrowdate = datetime.now().strftime("%Y-%m-%d")
    duedate = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    transaction = {
        "transactionid": transactionid,
        "userid": userid,
        "bookid": bookid,
        "borrowdate": borrowdate,
        "duedate": duedate,
        "returndate": None,
        "status": status
    }
    
    # Update book availability if not queued
    if status == "requested":
        books_data['books'][book_index]['availablecopies'] -= 1
        if books_data['books'][book_index]['availablecopies'] == 0:
            books_data['books'][book_index]['status'] = 'unavailable'
    
    # Save changes
    transactions_data['transactions'].append(transaction)
    save_books(books_data)
    save_transactions(transactions_data)
    
    # Notify staff
    notify_staff(f"New borrow request for '{book['title']}' by user {userid}")
    if status == "queued":
        return jsonify({"success": True, "message": f"'{book['title']}' is currently out of stock. You have been added to the waitlist (FIFO)."}), 201
    
    return jsonify({
        "success": True, 
        "message": f"Request for '{book['title']}' submitted successfully! Awaiting librarian approval.",
        "transaction": transaction
    }), 201

# POST /api/books/return
@require_login
def return_book():
    data = request.get_json()
    userid = session['userid']
    bookid = data.get('bookid')
    
    if not bookid:
        return jsonify({"success": False, "message": "Book ID required"}), 400
    
    # Find active transaction
    transactions_data = load_transactions()
    transaction = None
    transaction_index = None
    
    for i, t in enumerate(transactions_data['transactions']):
        if t['userid'] == userid and t['bookid'] == bookid and t['status'] == 'borrowed':
            transaction = t
            transaction_index = i
            break
    
    if not transaction:
        return jsonify({"success": False, "message": "No active borrow record found"}), 404
    
    # Update transaction
    return_datetime = datetime.now()
    transactions_data['transactions'][transaction_index]['returndate'] = return_datetime.strftime('%Y-%m-%d')
    transactions_data['transactions'][transaction_index]['status'] = 'returned'
    
    # Check for late submission and calculate persistent fine
    due_date = datetime.strptime(transaction['duedate'], '%Y-%m-%d')
    fine_charged = 0
    if return_datetime > due_date:
        days_late = (return_datetime - due_date).days
        if days_late > 0:
            fine_charged = days_late * 1  # ₹1 per day
            # Update user's unpaid_fines
            users_data = load_users()
            for u in users_data['users']:
                if u['userid'] == userid:
                    if 'unpaid_fines' not in u:
                        u['unpaid_fines'] = 0
                    u['unpaid_fines'] += fine_charged
                    break
            save_users(users_data)
    
    # Update book availability
    books_data = load_books()
    book_restored = False
    for i, b in enumerate(books_data['books']):
        if b['bookid'] == bookid:
            # Check for FIFO queue
            queued_request = None
            for t in transactions_data['transactions']:
                if t['bookid'] == bookid and t['status'] == 'queued':
                    queued_request = t
                    break
            
            if queued_request:
                # Automate next in line (bypass manual staff approval)
                queued_request['status'] = 'approved'
                # Grant exactly 24 hours to pick up the book
                queued_request['pickup_deadline'] = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                # Count stays reduced
                add_notification(queued_request['userid'], f"Good news! Your waitlisted book '{b['title']}' is now available and reserved for you. You have exactly 24 hours to collect it from the librarian.")
                notify_staff(f"FIFO Alert: '{b['title']}' has been automatically reserved for waitlisted user {queued_request['userid']} for 24 hours.")
            else:
                books_data['books'][i]['availablecopies'] += 1
                books_data['books'][i]['status'] = 'available'
            book_restored = True
            break
    
    save_transactions(transactions_data)
    save_books(books_data)
    
    msg = "Book returned successfully"
    if fine_charged > 0:
        msg += f". A late fine of ₹{fine_charged} has been added to your dues."
    
    return jsonify({
        "success": True,
        "message": msg
    }), 200

# GET /api/books/user/<userid>/borrowed
@require_login
def get_user_borrowed_books(userid):
    if session['userid'] != userid:
        return jsonify({"success": False, "message": "Unauthorized access"}), 401
    
    transactions_data = load_transactions()
    books_data = load_books()
    
    # Get all borrowed books for user
    borrowed_books = []
    for t in transactions_data['transactions']:
        if t['userid'] == userid and t['status'] in ['borrowed', 'requested', 'queued', 'approved']:
            # Find book details
            for b in books_data['books']:
                if b['bookid'] == t['bookid']:
                    borrowed_books.append({
                        "bookid": b['bookid'],
                        "title": b['title'],
                        "author": b['author'],
                        "borrowdate": t.get('borrowdate', ''),
                        "duedate": t.get('duedate', ''),
                        "status": t['status'],
                        "pickup_deadline": t.get('pickup_deadline', '')
                    })
                    break
    
    return jsonify({
        "success": True,
        "borrowedbooks": borrowed_books,
        "total": len(borrowed_books)
    }), 200


# GET /api/books/user/<userid>/history
@require_login
def get_user_history(userid):
    """Return full transaction history (borrowed + returned) for logged-in user."""
    if session['userid'] != userid:
        return jsonify({"success": False, "message": "Unauthorized access"}), 401
    
    transactions_data = load_transactions()
    books_data = load_books()
    
    history = []
    for t in transactions_data['transactions']:
        if t['userid'] == userid:
            # attach basic book info
            book_info = next((b for b in books_data['books'] if b['bookid'] == t['bookid']), {})
            history.append({
                "transactionid": t.get('transactionid'),
                "bookid": t.get('bookid'),
                "title": book_info.get('title', ''),
                "author": book_info.get('author', ''),
                "borrowdate": t.get('borrowdate'),
                "duedate": t.get('duedate'),
                "returndate": t.get('returndate'),
                "status": t.get('status')
            })
    
    return jsonify({"success": True, "history": history, "total": len(history)}), 200

# GET /api/books/user/<userid>/overdue
@require_login
def get_user_overdue_books(userid):
    """Return overdue books for logged-in user."""
    if session['userid'] != userid:
        return jsonify({"success": False, "message": "Unauthorized access"}), 401
    
    transactions_data = load_transactions()
    books_data = load_books()
    
    # Get overdue books for user
    overdue_books = []
    today = datetime.now().date()
    
    users_data = load_users()
    unpaid_fines = 0
    for u in users_data['users']:
        if u['userid'] == userid:
            unpaid_fines = u.get('unpaid_fines', 0)
            break
    
    for t in transactions_data['transactions']:
        if t['userid'] == userid and t['status'] == 'borrowed':
            due_date = datetime.strptime(t['duedate'], '%Y-%m-%d').date()
            if due_date < today:
                # Find book details
                for b in books_data['books']:
                    if b['bookid'] == t['bookid']:
                        days_overdue = (today - due_date).days
                        fine_amount = days_overdue * 1  # ₹1 per day (can be adjusted)
                        overdue_books.append({
                            "bookid": b['bookid'],
                            "title": b['title'],
                            "author": b['author'],
                            "borrowdate": t['borrowdate'],
                            "duedate": t['duedate'],
                            "days_overdue": days_overdue,
                            "fine_amount": fine_amount
                        })
                        break
    
    return jsonify({
        "success": True,
        "overduebooks": overdue_books,
        "unpaid_fines": unpaid_fines,
        "total": len(overdue_books)
    }), 200


# Export functions
from api import api_bp

api_bp.add_url_rule('/books', 'get_all_books', get_all_books, methods=['GET'])
api_bp.add_url_rule('/books/<bookid>', 'get_book', get_book, methods=['GET'])
api_bp.add_url_rule('/books/borrow', 'borrow_book', borrow_book, methods=['POST'])
api_bp.add_url_rule('/books/return', 'return_book', return_book, methods=['POST'])
api_bp.add_url_rule('/books/user/<userid>/borrowed', 'get_user_borrowed_books', get_user_borrowed_books, methods=['GET'])
api_bp.add_url_rule('/books/user/<userid>/history', 'get_user_history', get_user_history, methods=['GET'])
api_bp.add_url_rule('/books/user/<userid>/overdue', 'get_user_overdue_books', get_user_overdue_books, methods=['GET'])
