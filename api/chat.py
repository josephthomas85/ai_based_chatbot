import json
from flask import request, jsonify, session
from datetime import datetime, timedelta
from config import Config
from api.auth import require_login
from api.notifications import add_watcher, notify_watchers
from nlp.processor import NLPProcessor

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

# POST /api/chat
@require_login
def chat():
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
    entities = nlp_result['entities']
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

        # Try to find the book
        book = nlp_processor.find_book_by_name(books_data['books'], book_name)
        
        if book:
            if book['availablecopies'] > 0:
                # Process the borrow
                transactions_data = load_transactions()
                transactionid = f"TRN{str(len(transactions_data['transactions']) + 1).zfill(3)}"
                borrowdate = datetime.now().strftime('%Y-%m-%d')
                duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                # Create transaction
                transaction = {
                    "transactionid": transactionid,
                    "userid": userid,
                    "bookid": book['bookid'],
                    "borrowdate": borrowdate,
                    "duedate": duedate,
                    "returndate": None,
                    "status": "borrowed"
                }
                
                # Update book availability
                for i, b in enumerate(books_data['books']):
                    if b['bookid'] == book['bookid']:
                        books_data['books'][i]['availablecopies'] -= 1
                        if books_data['books'][i]['availablecopies'] == 0:
                            books_data['books'][i]['status'] = 'unavailable'
                        break
                
                # Save changes
                transactions_data['transactions'].append(transaction)
                save_books(books_data)
                save_transactions(transactions_data)
                
                response_data["response"] = f"✓ Book borrowed successfully!\n\n📚 Title: {book['title']}\n✍️ Author: {book['author']}\n👤 Borrowed by: {username}\n📅 Due date: {duedate}"
                response_data["data"] = [{
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "borrowedby": username,
                    "borrowdate": borrowdate,
                    "duedate": duedate,
                    "availablecopies": books_data['books'][[idx for idx, b in enumerate(books_data['books']) if b['bookid'] == book['bookid']][0]]['availablecopies']
                }]
                response_data["suggestions"] = ["Borrow another book", "View my books", "Show all books"]
                response_data["context"] = ""
            else:
                response_data["response"] = f"Sorry, '{book['title']}' is not currently available. All copies are borrowed."
                # user might want to know when it comes back
                add_watcher(userid, book['bookid'])
                response_data["suggestions"] = ["Show available books", "Search another book"]
                response_data["context"] = "waiting_for_book"
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
        # Simple greeting response
        response_data["response"] = (
            f"Hello {username}! 👋\n"
            "How can I assist you with our library today?"
        )
        response_data["suggestions"] = ["Show all books", "Search a book", "Borrow a book"]
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
        search_term = ' '.join(entities).lower() if entities else message.lower()
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
            name = name.strip()
            if not name or len(name) < 2:
                return None
            return nlp_processor.find_book_by_name(books_data['books'], name)

        # remove the keyword "borrow" to see if a title follows
        possible_name = message.lower().replace("borrow", "", 1).strip()
        borrowed = False

        # if we're already waiting for a book, handle exactly as before
        if context == "waiting_for_book":
            book_name = message.strip()
            book = try_borrow(book_name)
            if book:
                borrowed = True
        else:
            # try one-shot borrow
            book = try_borrow(possible_name)
            if book:
                borrowed = True

        if borrowed and book:
            if book['availablecopies'] > 0:
                transactions_data = load_transactions()
                transactionid = f"TRN{str(len(transactions_data['transactions']) + 1).zfill(3)}"
                borrowdate = datetime.now().strftime('%Y-%m-%d')
                duedate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                transaction = {
                    "transactionid": transactionid,
                    "userid": userid,
                    "bookid": book['bookid'],
                    "borrowdate": borrowdate,
                    "duedate": duedate,
                    "returndate": None,
                    "status": "borrowed"
                }
                for i, b in enumerate(books_data['books']):
                    if b['bookid'] == book['bookid']:
                        books_data['books'][i]['availablecopies'] -= 1
                        if books_data['books'][i]['availablecopies'] == 0:
                            books_data['books'][i]['status'] = 'unavailable'
                        break
                transactions_data['transactions'].append(transaction)
                save_books(books_data)
                save_transactions(transactions_data)
                response_data["response"] = f"✓ Book borrowed successfully!\n\n📚 Title: {book['title']}\n✍️ Author: {book['author']}\n👤 Borrowed by: {username}\n📅 Due date: {duedate}"
                response_data["data"] = [{
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "borrowedby": username,
                    "borrowdate": borrowdate,
                    "duedate": duedate
                }]
                response_data["suggestions"] = ["Borrow another book", "View my books", "Show all books"]
                response_data["context"] = ""
            else:
                # book exists but no copies
                add_watcher(userid, book['bookid'])
                response_data["response"] = f"Sorry, '{book['title']}' is not currently available. All copies are borrowed."
                response_data["suggestions"] = ["Show available books", "Search another book"]
                response_data["context"] = ""
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
            name = name.strip().lower()
            for borrowed in user_borrowed:
                if (name in borrowed['title'].lower() or 
                    borrowed['title'].lower() in name or
                    any(word in borrowed['title'].lower() for word in name.split())):
                    return borrowed
            return None

        # try to detect book name from message immediately
        returned_book = None
        transaction_to_update = None
        if context == "waiting_for_return":
            book_name = message.replace("return", "").strip()
            if not book_name or len(book_name) < 2:
                book_name = message.lower()
            returned_book = find_borrowed(book_name)
            if returned_book:
                transaction_to_update = returned_book['transaction']
        else:
            # one-shot return attempt
            book_name_candidate = message.lower().replace("return", "", 1).strip()
            returned_book = find_borrowed(book_name_candidate)
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
        # Simple recommendation: suggest books from popular categories or available books
        # For now, recommend 3 random available books
        available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
        if available_books:
            # Simple recommendation: pick first 3 available books
            recommendations = available_books[:3]
            response_data["response"] = f"Here are some book recommendations for you:"
            response_data["data"] = [
                {
                    "bookid": book['bookid'],
                    "title": book['title'],
                    "author": book['author'],
                    "category": book.get('category', 'General'),
                    "status": book['status'],
                    "availablecopies": book['availablecopies']
                }
                for book in recommendations
            ]
            response_data["suggestions"] = ["Borrow a book", "Show all books", "Search a book"]
        else:
            response_data["response"] = "Sorry, no books are currently available for recommendation."
            response_data["suggestions"] = ["Show all books"]
    
    else:
        response_data["response"] = "I'm sorry, I didn't understand that. I can help you with:\n• 'Show all books'\n• 'Borrow [book name]'\n• 'Search [book name]'\n• 'Return a book'\n• 'Check book status'\n• 'My books'\n• 'Recommend books'"
        response_data["suggestions"] = ["Show all books", "Borrow a book", "Search a book", "My books", "Recommend books"]
    
    return jsonify(response_data), 200

# Export functions
from api import api_bp

api_bp.add_url_rule('/chat', 'chat', chat, methods=['POST'])

