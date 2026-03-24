import json
import os
import bcrypt
import random
from datetime import datetime, timedelta
import sys

# Paths (Relative to project root)
USERS_DB = 'database/users.json'
TRANSACTIONS_DB = 'database/transactions.json'
BOOKS_DB = 'database/books.json'

def load_json(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("Initializing Database Seeding...")

    users_data = load_json(USERS_DB) or {"users": []}
    transactions_data = load_json(TRANSACTIONS_DB) or {"transactions": []}
    books_data = load_json(BOOKS_DB) or {"books": []}

    if not books_data.get("books"):
        print("Warning: Expected books in books.json to assign transactions.")
        return

    # 1) Add unpaid_fines to all existing users
    for u in users_data['users']:
        if 'unpaid_fines' not in u:
            u['unpaid_fines'] = 0

    # 2) Generate 15 New Users
    print("Generating 15 new users...")
    start_id = len(users_data['users']) + 1
    new_users = []
    
    # Generic securely hashed password for all new accounts ('password')
    salt = bcrypt.gensalt()
    pwd_hash = bcrypt.hashpw(b"password", salt).decode('utf-8')

    first_names = ["Rahul", "Sophie", "Aarav", "Meghan", "John", "David", "Sanjay", "Li", "Priya", "Carlos", "Aisha", "Wei", "Chloe", "Emma", "Oliver"]
    last_names = ["Sharma", "Turner", "Patel", "Fox", "Smith", "Lee", "Kumar", "Zhang", "Singh", "Garcia", "Tariq", "Chen", "Davis", "White", "Brown"]

    for i in range(15):
        uid = f"USR{str(start_id + i).zfill(3)}"
        fname = first_names[i]
        lname = last_names[i]
        
        user = {
            "userid": uid,
            "username": f"{fname.lower()}{lname.lower()[0]}",
            "password": pwd_hash,
            "fullname": f"{fname} {lname}",
            "email": f"{fname.lower()}@example.com",
            "registereddate": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
            "borrowedbooks": [],
            "unpaid_fines": 0
        }
        new_users.append(user)

    users_data['users'].extend(new_users)

    # 3) Seed Transactions for New Users
    print("Generating transactions for new users...")
    
    valid_books = [b for b in books_data['books']]
    if not valid_books:
        print("No valid books found.")
        sys.exit(1)

    today = datetime.now()

    for user in new_users:
        # Give each user 1-3 transactions
        num_trans = random.randint(1, 3)
        for _ in range(num_trans):
            book = random.choice(valid_books)
            is_overdue = random.choice([True, False, False]) # 33% chance of being overdue
            is_returned = random.choice([True, False]) # 50% chance of being returned
            
            # If overdue, borrow date needs to be far back
            # If returned, return date needs to be set.
            
            txn_id = f"TRN{str(len(transactions_data['transactions']) + 1).zfill(3)}"
            
            if is_overdue and not is_returned:
                borrowdate = today - timedelta(days=random.randint(35, 60))
                duedate = borrowdate + timedelta(days=30)
                status = "borrowed"
                returndate = None
                # Update book availability
                if book['availablecopies'] > 0:
                    book['availablecopies'] -= 1
                    if book['availablecopies'] == 0:
                        book['status'] = 'unavailable'
            elif is_returned:
                borrowdate = today - timedelta(days=random.randint(15, 60))
                duedate = borrowdate + timedelta(days=30)
                status = "returned"
                # If they returned it late, we could simulate adding to unpaid_fines!
                returndate = borrowdate + timedelta(days=random.randint(10, 40))
                
                if returndate > duedate:
                    days_late = (returndate - duedate).days
                    user['unpaid_fines'] += (days_late * 1)
                
                returndate = returndate.strftime('%Y-%m-%d')
            else:
                borrowdate = today - timedelta(days=random.randint(1, 25))
                duedate = borrowdate + timedelta(days=30)
                status = "borrowed"
                returndate = None
                if book['availablecopies'] > 0:
                    book['availablecopies'] -= 1
                    if book['availablecopies'] == 0:
                        book['status'] = 'unavailable'
            
            txn = {
                "transactionid": txn_id,
                "userid": user['userid'],
                "bookid": book['bookid'],
                "borrowdate": borrowdate.strftime('%Y-%m-%d'),
                "duedate": duedate.strftime('%Y-%m-%d'),
                "returndate": returndate,
                "status": status
            }
            transactions_data['transactions'].append(txn)

    # 4) Save changes
    print("Saving databases...")
    save_json(USERS_DB, users_data)
    save_json(TRANSACTIONS_DB, transactions_data)
    save_json(BOOKS_DB, books_data)
    
    print("Seed complete! Added 15 users, generated transactions, updated active overdues and persistent fines.")

if __name__ == '__main__':
    main()
