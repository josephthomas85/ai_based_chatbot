#!/usr/bin/env python
"""
Fix book availability counts by recalculating from actual transactions.
"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, load_transactions, save_books

def fix_availability():
    """Recalculate availablecopies based on active borrowings."""
    
    print("Fixing book availability counts...\n")
    
    books_data = load_books()
    transactions_data = load_transactions()
    
    # Count active borrows per book
    borrow_counts = {}
    for transaction in transactions_data['transactions']:
        if transaction['status'] == 'borrowed':
            bookid = transaction['bookid']
            borrow_counts[bookid] = borrow_counts.get(bookid, 0) + 1
    
    # Recalculate availability
    fixed_count = 0
    for i, book in enumerate(books_data['books']):
        bookid = book['bookid']
        active_borrows = borrow_counts.get(bookid, 0)
        correct_available = book['totalcopies'] - active_borrows
        
        if book['availablecopies'] != correct_available:
            old_copies = book['availablecopies']
            books_data['books'][i]['availablecopies'] = correct_available
            books_data['books'][i]['status'] = 'available' if correct_available > 0 else 'unavailable'
            
            print(f"Fixed: {book['title']}")
            print(f"  Old available: {old_copies} -> New available: {correct_available}")
            print(f"  Active borrows: {active_borrows}, Total copies: {book['totalcopies']}")
            print(f"  Status: {book['status']} -> {books_data['books'][i]['status']}")
            print()
            fixed_count += 1
    
    # Save corrected data
    save_books(books_data)
    
    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} books")
    print(f"Database has been updated with correct availability counts")
    print(f"{'='*60}")

if __name__ == "__main__":
    fix_availability()
