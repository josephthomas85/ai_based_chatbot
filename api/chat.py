import json
import random
from flask import request, jsonify, session
from datetime import datetime, timedelta
from config import Config
from api.auth import require_login
from api.notifications import add_watcher, notify_watchers
from api.books import count_active_borrows
from nlp.processor import NLPProcessor
from nlp.summarizer import summarize_book, extract_book_name_from_query, extract_line_count

# Initialize NLP processor
nlp_processor = NLPProcessor()

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

# Session-based conversational memory (cleared on logout)
USER_CHAT_MEMORY = {}

# POST /api/chat
@require_login
def chat():
    # Execute the core bot logic
    response_tuple = _chat_internal()
    if len(response_tuple) != 2:
        return response_tuple
        
    response_obj, status_code = response_tuple
    
    # Extract the actual json returned to the client
    response_data = response_obj.get_json()
    if not isinstance(response_data, dict):
        return response_tuple

    # Retrieve user session data 
    userid = session.get('userid')
    if not userid: return response_tuple
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    bot_response = response_data.get('response', '')
    
    # Store in memory sliding window
    if message and bot_response:
        if userid not in USER_CHAT_MEMORY:
            USER_CHAT_MEMORY[userid] = []
            
        USER_CHAT_MEMORY[userid].append({"role": "user", "content": message})
        USER_CHAT_MEMORY[userid].append({"role": "assistant", "content": bot_response})
        
        # Keep only the last 10 messages (5 interactions) per user
        if len(USER_CHAT_MEMORY[userid]) > 10:
            USER_CHAT_MEMORY[userid] = USER_CHAT_MEMORY[userid][-10:]
            
    return response_tuple

def _chat_internal():
    data = request.get_json()
    message = data.get('message', '').strip()
    userid = session['userid']
    username = session.get('fullname', session.get('username', 'User'))  # Get logged-in user's name
    context = data.get('context', '')  # Track conversation context
    
    if not message:
        return jsonify({"success": False, "message": "Message cannot be empty"}), 400
    
    # Process message with NLP
    nlp_result = nlp_processor.process_message(message)
    intent = nlp_result['intent']
    extracted_book = nlp_result.get('book_title')
    extracted_branch = nlp_result.get('branch')  # e.g. 'CSE', 'ECE'
    extracted_semester = nlp_result.get('semester')  # e.g. 'S3', 'S5'
    confidence = nlp_result['confidence']
    
    books_data = load_books()
    response_data = {
        "success": True,
        "intent": intent,
        "confidence": confidence,
        "response": "",
        "data": [],
        "suggestions": [],
        "context": ""
    }
    
    # ESCAPE HATCH: If the user provides a very clear command (like clicking a Quick Action),
    # we should break out of the current context and handle the new command.
    if intent != "unknown" and confidence >= 0.8:
        context = ""

    # PRIORITY 1: Handle context-based workflows first
    # If user is in a conversation context, prioritize that over intent recognition
    
    if context == "waiting_for_book":
        # User is responding with a book name after asking to borrow
        book_name = message.strip()
        # guard against empty input (avoids auto-matching '')
        if not book_name:
            # re-prompt with available list
            available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
            response_data["response"] = (
                "Please enter the name of the book you want to borrow. Here are the available books:" 
            )
            response_data["data"] = [
                {
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "status": book['status'],
                    "availablecopies": book['availablecopies']
                }
                for book in available_books[:20]
            ]
            response_data["suggestions"] = ["Try another book name", "Show all books"]
            response_data["context"] = "waiting_for_book"
            return jsonify(response_data), 200

        if book_name:
            transactions_data = load_transactions()
            
            # Enforce 5-book limit
            if count_active_borrows(userid, transactions_data) >= 5:
                response_data["response"] = (
                    "I'm sorry, you've reached your limit of 5 books. 📚\n\n"
                    "You'll need to return one of your current books before you can borrow another. "
                    "Would you like to see your current books?"
                )
                response_data["suggestions"] = ["View my books", "Return a book", "Show all books"]
                response_data["context"] = ""
                return jsonify(response_data), 200

            # Find the book
            book = nlp_processor.find_book_by_name(books_data['books'], book_name)
            if not book:
                response_data["response"] = f"I couldn't find a book named '{book_name}'. Please try searching again or choose from the catalog."
                response_data["suggestions"] = ["Show all books", "Search for a book"]
                response_data["context"] = ""
                return jsonify(response_data), 200

            # Prevent duplicate borrowing of the same book
            active_statuses = ['borrowed', 'requested', 'queued', 'approved', 'pending_return']
            for t in transactions_data['transactions']:
                if t['userid'] == userid and t['bookid'] == book['bookid'] and t['status'] in active_statuses:
                    response_data["response"] = (
                        f"I'm sorry, you already have an active request or a borrowed copy for **'{book['title']}'**. 📚\n\n"
                        "You can see your borrowed books by typing 'my books'."
                    )
                    response_data["suggestions"] = ["View my books", "Show all books"]
                    response_data["context"] = ""
                    return jsonify(response_data), 200

            # Generate a truly unique transaction ID (Date_Time_Random)
            now = datetime.now()
            transactionid = f"T{now.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            
            borrowdate = now.strftime('%Y-%m-%d')
            duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            if book['availablecopies'] > 0:
                status = "borrowed"
                response_message = f"✓ Book borrowed successfully!\n\n📚 Title: {book['title']}\n✍️ Author: {book['author']}\n👤 Borrowed by: {username}\n📅 Due date: {duedate}"
                
                # Update book availability
                for i, b in enumerate(books_data['books']):
                    if b['bookid'] == book['bookid']:
                        books_data['books'][i]['availablecopies'] -= 1
                        if books_data['books'][i]['availablecopies'] == 0:
                            books_data['books'][i]['status'] = 'unavailable'
                        break
            else:
                status = "queued"
                response_message = f"⏳ You have successfully joined the waitlist for '{book['title']}'!\n\nWe will reserve it for you for 24 hours as soon as it is returned."
                add_watcher(userid, book['bookid'])
            
            # Create transaction
            transaction = {
                "transactionid": transactionid,
                "userid": userid,
                "bookid": book['bookid'],
                "borrowdate": borrowdate,
                "duedate": duedate,
                "returndate": None,
                "status": status
            }
            
            # Save changes
            transactions_data['transactions'].append(transaction)
            save_books(books_data)
            save_transactions(transactions_data)
            
            response_data["response"] = response_message
            response_data["data"] = [{
                "bookid": book['bookid'],
                "title": book['title'],
                "author": book['author'],
                "borrowedby": username,
                "borrowdate": borrowdate,
                "duedate": duedate,
                "status": status,
                "availablecopies": books_data['books'][[idx for idx, b in enumerate(books_data['books']) if b['bookid'] == book['bookid']][0]]['availablecopies']
            }]
            response_data["suggestions"] = ["View my books", "Show all books", "Return a book"]
            response_data["context"] = ""
            return jsonify(response_data), 200
        else:
            available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
            response_data["response"] = f"I couldn't find '{book_name}' in our catalog.\n\nHere are the available books:"
            response_data["data"] = [
                {
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "status": book['status'],
                    "availablecopies": book['availablecopies']
                }
                for book in available_books[:20]  # Limit to first 20
            ]
            response_data["suggestions"] = ["Try another book name", "Show all books"]
            response_data["context"] = "waiting_for_book"
        
        return jsonify(response_data), 200
    
    elif context == "waiting_for_return":
        # User is responding with a book name after asking to return
        book_name = message.strip()
        if not book_name:
            # ask again
            transactions_data = load_transactions()
            user_borrowed = []
            for transaction in transactions_data['transactions']:
                if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                    for book in books_data['books']:
                        if book['bookid'] == transaction['bookid']:
                            user_borrowed.append({
                                'bookid': book['bookid'],
                                'title': book['title'],
                                'author': book['author'],
                                'duedate': transaction['duedate'],
                                'transaction': transaction
                            })
                            break
            response_data["response"] = (
                "Please tell me the name of the book you want to return.\n\nHere are your borrowed books:"
            )
            response_data["data"] = [
                {
                    "bookid": b['bookid'],
                    "title": b['title'],
                    "author": b['author'],
                    "duedate": b['duedate']
                }
                for b in user_borrowed
            ]
            response_data["suggestions"] = ["Try another book name"] + [b['title'] for b in user_borrowed[:2]]
            response_data["context"] = "waiting_for_return"
            return jsonify(response_data), 200
        
        # Load user's borrowed books
        transactions_data = load_transactions()
        user_borrowed = []
        
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                # Find book details
                for book in books_data['books']:
                    if book['bookid'] == transaction['bookid']:
                        user_borrowed.append({
                            'bookid': book['bookid'],
                            'title': book['title'],
                            'author': book['author'],
                            'duedate': transaction['duedate'],
                            'transaction': transaction
                        })
                        break
        
        # Find book in user's borrowed list
        returned_book = None
        transaction_to_update = None
        
        for borrowed in user_borrowed:
            if (book_name.lower() in borrowed['title'].lower() or 
                borrowed['title'].lower() in book_name.lower() or
                any(word in borrowed['title'].lower() for word in book_name.lower().split())):
                returned_book = borrowed
                transaction_to_update = borrowed['transaction']
                break
        
        if returned_book:
            # Process return
            returndate = datetime.now().strftime('%Y-%m-%d')
            
            # Update transaction
            for i, t in enumerate(transactions_data['transactions']):
                if t['transactionid'] == transaction_to_update['transactionid']:
                    transactions_data['transactions'][i]['returndate'] = returndate
                    transactions_data['transactions'][i]['status'] = 'returned'
                    break
            
            # Update book availability
            for i, b in enumerate(books_data['books']):
                if b['bookid'] == returned_book['bookid']:
                    was_zero = books_data['books'][i]['availablecopies'] == 0
                    books_data['books'][i]['availablecopies'] += 1
                    books_data['books'][i]['status'] = 'available'
                    if was_zero:
                        notify_watchers(books_data['books'][i])
                    break
            
            save_transactions(transactions_data)
            save_books(books_data)
            
            response_data["response"] = f"✓ Book returned successfully!\n\n📚 Title: {returned_book['title']}\n✍️ Author: {returned_book['author']}\n👤 Returned by: {username}\n📅 Return date: {returndate}\n\nThank you! The book has been added back to our library."
            response_data["data"] = [{
                "bookid": returned_book['bookid'],
                "title": returned_book['title'],
                "author": returned_book['author'],
                "returnedby": username,
                "returndate": returndate,
                "availablecopies": books_data['books'][[idx for idx, b in enumerate(books_data['books']) if b['bookid'] == returned_book['bookid']][0]]['availablecopies']
            }]
            response_data["suggestions"] = ["Borrow another book", "View my books", "Show all books"]
            response_data["context"] = ""
        else:
            response_data["response"] = f"I couldn't find '{book_name}' in your borrowed books.\n\nHere are your borrowed books:"
            response_data["data"] = [
                {
                    "bookid": b['bookid'],
                    "title": b['title'],
                    "author": b['author'],
                    "duedate": b['duedate']
                }
                for b in user_borrowed
            ]
            response_data["suggestions"] = ["Try another book name"] + [b['title'] for b in user_borrowed[:2]]
            response_data["context"] = "waiting_for_return"
        
        return jsonify(response_data), 200
    
    # PRIORITY 2: Handle intent-based workflows
    # Handle different intents
    if intent == "greeting":
        response_data["response"] = (
            f"Hello {username}! 👋\n"
            "How can I assist you with our library today?"
        )
        response_data["suggestions"] = ["Show all books", "Search a book", "Borrow a book", "Books by semester"]
    
    elif intent == "semesterbooks":
        branch = extracted_branch
        semester = extracted_semester

        VALID_BRANCHES = ["CSE", "ECE", "EEE", "ME", "CIVIL", "AUTOMOBILE", "COMMON", "COMMON (ALL BRANCHES)"]
        SEMESTER_ALIASES = {
            "S1": "S1", "S2": "S2", "S3": "S3", "S4": "S4",
            "S5": "S5", "S6": "S6", "S7": "S7", "S8": "S8"
        }

        # Fallback: try to parse branch/semester from raw message if LLM missed them
        if not branch or not semester:
            msg_upper = message.upper()
            for b in VALID_BRANCHES:
                if b in msg_upper:
                    branch = b
                    break
            for s in ["S1","S2","S3","S4","S5","S6","S7","S8"]:
                if s in msg_upper:
                    semester = s
                    break
            # handle numeric references like '3rd semester'
            sem_map = {"1ST":"S1","2ND":"S2","3RD":"S3","4TH":"S4","5TH":"S5","6TH":"S6","7TH":"S7","8TH":"S8",
                       "FIRST":"S1","SECOND":"S2","THIRD":"S3","FOURTH":"S4",
                       "FIFTH":"S5","SIXTH":"S6","SEVENTH":"S7","EIGHTH":"S8"}
            for k, v in sem_map.items():
                if k in msg_upper and not semester:
                    semester = v
                    break

        if not branch and not semester:
            response_data["response"] = (
                "Sure! Please tell me your **branch** and **semester**.\n"
                "For example: *'CSE S3 books'* or *'ECE 5th semester books'*"
            )
            response_data["suggestions"] = ["CSE S3 books", "ECE S5 books", "ME S4 books", "CIVIL S6 books"]
            response_data["context"] = ""
            return jsonify(response_data), 200

        # Normalise branch to match category format
        if branch == "COMMON":
            branch = "COMMON (ALL BRANCHES)"

        # Semesters S1 and S2 are shared across all branches as COMMON
        COMMON_SEMESTERS = {"S1", "S2"}

        # Build the category string to match against database
        if branch and semester:
            category_key = f"{branch} - {semester}"
        elif semester:
            category_key = semester
        else:
            category_key = branch

        matched_books = [
            b for b in books_data['books']
            if category_key.lower() in b.get('category', '').lower()
        ]

        # For S1 and S2: always use COMMON (ALL BRANCHES) as the primary source
        # since those semesters are shared across all branches.
        fallback_used = False
        if semester in COMMON_SEMESTERS and branch and branch != "COMMON (ALL BRANCHES)":
            common_key = f"COMMON (ALL BRANCHES) - {semester}"
            common_books = [
                b for b in books_data['books']
                if common_key.lower() in b.get('category', '').lower()
            ]
            if common_books:
                # Merge: common books + any branch-specific ones not already included
                existing_ids = {b['bookid'] for b in common_books}
                extras = [b for b in matched_books if b['bookid'] not in existing_ids]
                matched_books = common_books + extras
                fallback_used = True
                category_key = common_key

        if matched_books:
            if fallback_used:
                response_data["response"] = (
                    f"📚 **{semester}** is a common semester shared by all branches.\n\n"
                    f"Here are the **{semester}** books ({len(matched_books)} found):"
                )
            else:
                label = f"{branch or ''} {semester or ''}".replace("COMMON (ALL BRANCHES)", "Common").strip()
                response_data["response"] = f"📚 Here are the **{label}** books in our library ({len(matched_books)} found):"
            response_data["data"] = [
                {
                    "bookid": b['bookid'],
                    "title": b['title'],
                    "author": b['author'],
                    "status": b['status'],
                    "availablecopies": b['availablecopies'],
                    "category": b.get('category', '')
                }
                for b in matched_books
            ]
            response_data["suggestions"] = ["Borrow a book", "Search a book", "Show all books"]
        else:
            response_data["response"] = (
                f"I couldn't find books for **{category_key}** in our catalog.\n"
                "Try a different branch or semester.\n\n"
                "Available branches: **CSE, ECE, EEE, ME, CIVIL, AUTOMOBILE**\n"
                "Semesters: **S1 through S8**"
            )
            response_data["suggestions"] = ["CSE S3 books", "ECE S5 books", "ME S4 books", "Show all books"]
        response_data["context"] = ""
        return jsonify(response_data), 200

    elif intent == "showallbooks":
        # list every book, including those currently out of stock
        all_books = books_data['books']
        response_data["response"] = f"I found {len(all_books)} books in our library (some may be unavailable):"
        response_data["data"] = [
            {
                "bookid": book['bookid'],
                "title": book['title'],
                "author": book['author'],
                "status": book['status'],
                "availablecopies": book['availablecopies']
            }
            for book in all_books
        ]
        response_data["suggestions"] = ["Borrow a book", "Check book status", "Search a book"]
    
    elif intent == "searchbook":
        # Search for books by title or author. If the user provides a specific
        # name we return availability information directly.
        search_term = extracted_book if extracted_book else message.strip()
        # try to match a single book using the same logic used for borrowing
        direct = nlp_processor.find_book_by_name(books_data['books'], search_term)
        if direct:
            # user probably wanted availability
            copies = direct['availablecopies']
            if copies > 0:
                response_data["response"] = (
                    f"'{direct['title']}' has {copies} copy(ies) available."
                )
            else:
                response_data["response"] = (
                    f"'{direct['title']}' currently has no copies available."
                )
                # add this user as a watcher so they get notified when it returns
                add_watcher(userid, direct['bookid'])
            response_data["data"] = [{
                "bookid": direct['bookid'],
                "title": direct['title'],
                "author": direct['author'],
                "status": direct['status'],
                "availablecopies": direct['availablecopies']
            }]
            response_data["suggestions"] = ["Borrow a book", "Show all books"]
        else:
            matching_books = []
            for book in books_data['books']:
                if (search_term in book['title'].lower() or 
                    search_term in book['author'].lower() or
                    any(word in book['title'].lower() for word in search_term.split())):
                    matching_books.append({
                        "bookid": book['bookid'],
                        "title": book['title'],
                        "author": book['author'],
                        "status": book['status'],
                        "availablecopies": book['availablecopies']
                    })
            if matching_books:
                response_data["response"] = f"I found {len(matching_books)} book(s) matching your search:"
                response_data["data"] = matching_books
            else:
                response_data["response"] = f"Sorry, I couldn't find any books matching '{search_term}'"
                response_data["data"] = []
            response_data["suggestions"] = ["Show all books", "Search another book", "Borrow a book"]
    
    elif intent == "borrowbook":
        # Attempt to borrow immediately if the message includes a title
        def try_borrow(name):
            if not name or len(name) < 2:
                return None
            return nlp_processor.find_book_by_name(books_data['books'], name)

        # contexts handling
        if context == "waiting_for_book":
            book_name = message.strip()
            book = try_borrow(book_name)
        else:
            book = try_borrow(extracted_book)

        if book:
            transactions_data = load_transactions()
            
            # Enforce 5-book limit
            if count_active_borrows(userid, transactions_data) >= 5:
                response_data["response"] = (
                    "I'm sorry, you've already reached your limit of 5 books. 📚\n\n"
                    "Please return a book before taking another one. Would you like to see what you have borrowed?"
                )
                response_data["suggestions"] = ["View my books", "Return a book", "Show all books"]
                response_data["context"] = ""
                return jsonify(response_data), 200
                
            # Prevent duplicate borrowing of the same book
            active_statuses = ['borrowed', 'requested', 'queued', 'approved', 'pending_return']
            for t in transactions_data['transactions']:
                if t['userid'] == userid and t['bookid'] == book['bookid'] and t['status'] in active_statuses:
                    response_data["response"] = (
                        f"I'm sorry, you already have an active request or a borrowed copy for **'{book['title']}'**. 📚\n\n"
                        "You can see your borrowed books by typing 'my books'."
                    )
                    response_data["suggestions"] = ["View my books", "Show all books"]
                    response_data["context"] = ""
                    return jsonify(response_data), 200

            borrowdate = datetime.now().strftime('%Y-%m-%d')
            duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            transactionid = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            
            if book['availablecopies'] > 0:
                status = "borrowed"
                response_message = f"✓ Book borrowed successfully!\n\n📚 Title: {book['title']}\n✍️ Author: {book['author']}\n👤 Borrowed by: {username}\n📅 Due date: {duedate}"
                
                for i, b in enumerate(books_data['books']):
                    if b['bookid'] == book['bookid']:
                        books_data['books'][i]['availablecopies'] -= 1
                        if books_data['books'][i]['availablecopies'] == 0:
                            books_data['books'][i]['status'] = 'unavailable'
                        break
            else:
                status = "queued"
                response_message = f"⏳ You have successfully joined the waitlist for '{book['title']}'!\n\nWe will reserve it for you for 24 hours as soon as it is returned."
                add_watcher(userid, book['bookid'])
                
            transaction = {
                "transactionid": transactionid,
                "userid": userid,
                "bookid": book['bookid'],
                "borrowdate": borrowdate,
                "duedate": duedate,
                "returndate": None,
                "status": status
            }
            
            transactions_data['transactions'].append(transaction)
            save_books(books_data)
            save_transactions(transactions_data)
            
            response_data["response"] = response_message
            response_data["data"] = [{
                "bookid": book['bookid'],
                "title": book['title'],
                "author": book['author'],
                "borrowedby": username,
                "borrowdate": borrowdate,
                "duedate": duedate,
                "status": status
            }]
            response_data["suggestions"] = ["View my books", "Show all books", "Return a book"]
            response_data["context"] = ""
            return jsonify(response_data), 200
        else:
            if context == "waiting_for_book":
                response_data["response"] = f"I couldn't find a book named '{message.strip()}'. Please try searching again or choose from the catalog."
                response_data["suggestions"] = ["Show all books", "Search for a book"]
                response_data["context"] = ""
            else:
                # Regular borrow request without a name
                available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
                response_data["response"] = "Which book would you like to borrow? Here are some available titles:"
                response_data["data"] = [
                    {
                        "bookid": b['bookid'],
                        "title": b['title'],
                        "author": b['author'],
                        "status": b['status'],
                        "availablecopies": b['availablecopies']
                    }
                    for b in available_books[:5]
                ]
                response_data["suggestions"] = ["Show all books", "Search for a book"]
                response_data["context"] = "waiting_for_book"
            return jsonify(response_data), 200

        # fallback: show list and set context
        available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
        response_data["response"] = f"Here are the {len(available_books)} available books. Just tell me the book name you want to borrow:"
        response_data["data"] = [
            {
                "bookid": book['bookid'],
                "title": book['title'],
                "author": book['author'],
                "status": book['status'],
                "availablecopies": book['availablecopies']
            }
            for book in available_books
        ]
        response_data["suggestions"] = [book['title'] for book in available_books[:3]]
        response_data["context"] = "waiting_for_book"
    
    elif intent == "returnbook":
        # Gather currently borrowed books for this user
        transactions_data = load_transactions()
        user_borrowed = []
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                for book in books_data['books']:
                    if book['bookid'] == transaction['bookid']:
                        user_borrowed.append({
                            'bookid': book['bookid'],
                            'title': book['title'],
                            'author': book['author'],
                            'duedate': transaction['duedate'],
                            'transaction': transaction
                        })
                        break

        # Check if user has any borrowed books
        if not user_borrowed:
            response_data["response"] = "You don't have any borrowed books to return."
            response_data["suggestions"] = ["Borrow a book", "Show all books"]
            response_data["context"] = ""
            return jsonify(response_data), 200

        # helper to find return candidate in user's list
        def find_borrowed(name):
            if not name: return None
            name = name.strip().lower()
            basic_stopwords = {'a', 'an', 'the', 'is', 'at', 'which', 'on', 'for', 'book', 'please'}
            search_words = set(w for w in name.split() if w not in basic_stopwords and len(w) > 2)
            
            for borrowed in user_borrowed:
                title_lower = borrowed['title'].lower()
                if name in title_lower or title_lower in name:
                    return borrowed
                
                title_words = set(w.strip('.,!?()[]"') for w in title_lower.split() if w not in basic_stopwords)
                if search_words and (search_words & title_words):
                    return borrowed
            return None

        # try to detect book name from message immediately
        returned_book = None
        transaction_to_update = None
        if context == "waiting_for_return":
            book_name = extracted_book if extracted_book else message.strip()
            returned_book = find_borrowed(book_name)
            if returned_book:
                transaction_to_update = returned_book['transaction']
        else:
            # one-shot return attempt
            returned_book = find_borrowed(extracted_book)
            if returned_book:
                transaction_to_update = returned_book['transaction']

        if returned_book and transaction_to_update:
            # process return immediately
            returndate = datetime.now().strftime('%Y-%m-%d')
            for i, t in enumerate(transactions_data['transactions']):
                if t['transactionid'] == transaction_to_update['transactionid']:
                    transactions_data['transactions'][i]['returndate'] = returndate
                    transactions_data['transactions'][i]['status'] = 'returned'
                    break
            for i, b in enumerate(books_data['books']):
                if b['bookid'] == returned_book['bookid']:
                    books_data['books'][i]['availablecopies'] += 1
                    books_data['books'][i]['status'] = 'available'
                    break
            save_transactions(transactions_data)
            save_books(books_data)

            response_data["response"] = f"✓ Book returned successfully!\n\n📚 Title: {returned_book['title']}\n✍️ Author: {returned_book['author']}\n👤 Returned by: {username}\n📅 Return date: {returndate}\n\nThank you! The book has been added back to our library."
            response_data["data"] = [{
                "bookid": returned_book['bookid'],
                "title": returned_book['title'],
                "author": returned_book['author'],
                "returnedby": username,
                "returndate": returndate
            }]
            response_data["suggestions"] = ["Borrow another book", "View my books", "Show all books"]
            response_data["context"] = ""
            return jsonify(response_data), 200

        # fallback to normal listing behavior
        if not user_borrowed:
            response_data["response"] = "You don't have any borrowed books to return."
            response_data["suggestions"] = ["Borrow a book", "Show all books"]
            response_data["context"] = ""
        else:
            response_data["response"] = f"You have {len(user_borrowed)} borrowed book(s). Just tell me the name of the book you want to return:"
            response_data["data"] = [
                {
                    "bookid": b['bookid'],
                    "title": b['title'],
                    "author": b['author'],
                    "duedate": b['duedate']
                }
                for b in user_borrowed
            ]
            response_data["suggestions"] = [b['title'] for b in user_borrowed[:3]]
            response_data["context"] = "waiting_for_return"
    
    elif intent == "checkstatus":
        response_data["response"] = "I can help you check book availability. Please tell me the book title or use 'Show All Books' to see availability status."
        response_data["suggestions"] = ["Show all books", "Search for a book"]
    
    elif intent == "mybooks":
        # Show user's currently borrowed books
        transactions_data = load_transactions()
        user_borrowed = []
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                for book in books_data['books']:
                    if book['bookid'] == transaction['bookid']:
                        user_borrowed.append({
                            'bookid': book['bookid'],
                            'title': book['title'],
                            'author': book['author'],
                            'duedate': transaction['duedate']
                        })
                        break
        
        if user_borrowed:
            response_data["response"] = f"You have {len(user_borrowed)} borrowed book(s):"
            response_data["data"] = [
                {
                    "bookid": b['bookid'],
                    "title": b['title'],
                    "author": b['author'],
                    "duedate": b['duedate']
                }
                for b in user_borrowed
            ]
            response_data["suggestions"] = ["Return a book", "Borrow another book", "Show all books"]
        else:
            response_data["response"] = "You don't have any borrowed books right now."
            response_data["suggestions"] = ["Borrow a book", "Show all books"]
    
    elif intent == "recommend":
        # ── AI Personalized Recommendations ──────────────────────────────────
        from nlp.ai_service import generate_ai_recommendations
        
        available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
        if available_books:
            # 1. Gather user's past reading history
            transactions_data = load_transactions()
            user_history_titles = []
            for tx in transactions_data.get('transactions', []):
                if tx['userid'] == userid:
                    # Find the title for this bookid
                    for b in books_data['books']:
                        if b['bookid'] == tx['bookid']:
                            user_history_titles.append(b['title'])
                            break
            
            # Deduplicate history
            user_history_titles = list(set(user_history_titles))
            
            # 2. Get AI recommendations based on history
            ai_result = generate_ai_recommendations(user_history_titles, available_books)
            
            # 3. Map returned bookids back to real book objects
            recommended_books = []
            for bid in ai_result["recommended_bookids"]:
                for b in available_books:
                    if b["bookid"] == bid:
                        recommended_books.append(b)
                        break
            
            response_data["response"] = f"**AI Recommendations:**\n\n{ai_result['explanation']}"
            response_data["data"] = [
                {
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "status": book['status'],
                    "availablecopies": book['availablecopies']
                }
                for book in recommended_books
            ]
            response_data["suggestions"] = ["Borrow a book", "Show all books", "Search a book"]
        else:
            response_data["response"] = "Sorry, no books are currently available for recommendation."
            response_data["suggestions"] = ["Show all books"]

    elif intent == "help":
        response_data["response"] = (
            f"Here's everything I can help you with, {username}:\n\n"
            "• **Show all books** — Browse the full library catalogue\n"
            "• **Search [title/author]** — Find a specific book\n"
            "• **Borrow [title]** — Borrow a book from the library\n"
            "• **Return [title]** — Return a book you've borrowed\n"
            "• **My books** — See your active loans\n"
            "• **Recommend books** — Get personalised reading suggestions\n"
            "• **History** — View your past borrowing history\n"
            "• **Overdue** — Check if you have any overdue books\n"
            "• **Summarize [title]** — Get an AI-powered 5-line book summary\n"
            "• **Explain [title] in 5 lines** — Same as above with custom line count"
        )
        response_data["suggestions"] = ["Show all books", "Borrow a book", "My books", "Summarize a book"]

    elif intent == "history":
        # Show full borrow history (returned + current)
        transactions_data = load_transactions()
        user_history = []
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] in ['borrowed', 'returned', 'requested']:
                for book in books_data['books']:
                    if book['bookid'] == transaction['bookid']:
                        user_history.append({
                            'bookid': book['bookid'],
                            'title': book['title'],
                            'author': book['author'],
                            'status': transaction['status'],
                            'borrowdate': transaction.get('borrowdate', ''),
                            'returndate': transaction.get('returndate', None),
                            'duedate': transaction.get('duedate', '')
                        })
                        break
        if user_history:
            response_data["response"] = f"Your borrowing history ({len(user_history)} record{'s' if len(user_history) != 1 else ''}):"
            response_data["data"] = [
                {
                    "title": h['title'],
                    "author": h['author'],
                    "status": h['status'],
                    "duedate": h['returndate'] if h['returndate'] else h['duedate']
                }
                for h in user_history
            ]
        else:
            response_data["response"] = "You haven't borrowed any books yet. Ready to start reading?"
        response_data["suggestions"] = ["Borrow a book", "Show all books", "Recommend books"]

    elif intent == "overdue":
        transactions_data = load_transactions()
        today = datetime.now().strftime('%Y-%m-%d')
        overdue_books = []
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                if transaction.get('duedate', '9999') < today:
                    for book in books_data['books']:
                        if book['bookid'] == transaction['bookid']:
                            overdue_books.append({
                                'bookid': book['bookid'],
                                'title': book['title'],
                                'author': book['author'],
                                'duedate': transaction['duedate']
                            })
                            break
        if overdue_books:
            response_data["response"] = f"You have {len(overdue_books)} overdue book(s). Please return them as soon as possible:"
            response_data["data"] = [
                {"title": b['title'], "author": b['author'], "duedate": b['duedate']}
                for b in overdue_books
            ]
            response_data["suggestions"] = ["Return a book", "My books"]
        else:
            response_data["response"] = "Great news! You have no overdue books."
            response_data["suggestions"] = ["My books", "Borrow a book"]

    elif intent == "summarize":
        # ── AI Book Summarization ──────────────────────────────────────────
        # Get book name directly from LLM extraction
        requested_name = extracted_book
        line_count = extract_line_count(message)

        # If no name extracted and we're in summarize context, use full message as name
        if not requested_name and context == "waiting_for_summary":
            requested_name = message.strip()

        if requested_name:
            book = nlp_processor.find_book_by_name(books_data['books'], requested_name)
            if book:
                summary = summarize_book(book, lines=line_count)
                response_data["response"] = (
                    f"**AI Book Summary** — {line_count}-line overview:\n\n{summary}"
                )
                response_data["data"] = [{
                    "bookid": book["bookid"],
                    "title": book["title"],
                    "author": book["author"],
                    "status": book["status"],
                    "availablecopies": book["availablecopies"]
                }]
                response_data["suggestions"] = [
                    f"Borrow {book['title']}",
                    "Show all books",
                    "Recommend books"
                ]
                response_data["context"] = ""
            else:
                response_data["response"] = (
                    f"I couldn't find a book called **'{requested_name}'** in the library.\n"
                    "Please try a different title, or type the exact book name:"
                )
                response_data["suggestions"] = ["Show all books", "Search a book"]
                response_data["context"] = "waiting_for_summary"
        else:
            # No book name found — ask the user
            available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
            sample = [b['title'] for b in available_books[:4]]
            response_data["response"] = (
                "I can generate an AI summary for any book in the library!\n\n"
                "Just type the book title and I'll give you a 5-line overview. Examples:\n"
                "• *Explain Python Crash Course in 5 lines*\n"
                "• *Summarize Clean Code*\n"
                "• *What is Designing Data-Intensive Applications about?*"
            )
            response_data["suggestions"] = sample
            response_data["context"] = "waiting_for_summary"

    elif context == "waiting_for_summary":
        # User typed a book name directly after we asked for one
        requested_name = message.strip()
        line_count = extract_line_count(message)
        book = nlp_processor.find_book_by_name(books_data['books'], requested_name)
        if book:
            summary = summarize_book(book, lines=line_count)
            response_data["response"] = (
                f"🤖 **AI Book Summary** — {line_count}-line overview:\n\n{summary}"
            )
            response_data["data"] = [{
                "bookid": book["bookid"],
                "title": book["title"],
                "author": book["author"],
                "status": book["status"],
                "availablecopies": book["availablecopies"]
            }]
            response_data["suggestions"] = [
                f"Borrow {book['title']}",
                "Show all books",
                "Recommend books"
            ]
            response_data["context"] = ""
        else:
            response_data["response"] = (
                f"I still couldn't find **'{requested_name}'**. Try a shorter or different title:"
            )
            response_data["suggestions"] = ["Show all books", "Search a book"]
            response_data["context"] = "waiting_for_summary"

    else:
        # ── AI Conversational Fallback ───────────────────────────────────
        # When intent is unknown, pass to Groq for a helpful response
        from nlp.ai_service import generate_chat_response
        
        # Get a sample of available books (first 5 to keep context small)
        available_books = [b for b in books_data['books'] if b['availablecopies'] > 0][:5]
        
        # Get user's current borrowed books
        transactions_data = load_transactions()
        user_history = []
        for transaction in transactions_data['transactions']:
            if transaction['userid'] == userid and transaction['status'] == 'borrowed':
                for book in books_data['books']:
                    if book['bookid'] == transaction['bookid']:
                        user_history.append({'title': book['title']})
                        break
        
        ai_reply = generate_chat_response(
            message=message, 
            username=username, 
            user_history=user_history, 
            available_books_sample=available_books,
            chat_history=USER_CHAT_MEMORY.get(userid, [])
        )
        
        response_data["response"] = ai_reply
        response_data["suggestions"] = ["Show all books", "Search a book", "Borrow a book"]
    
    return jsonify(response_data), 200

# Export functions
from api import api_bp

api_bp.add_url_rule('/chat', 'chat', chat, methods=['POST'])
