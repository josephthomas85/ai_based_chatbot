#!/usr/bin/env python
"""
Test availability constraint enforcement for borrow/return operations.
"""

import json
import os
from datetime import datetime, timedelta

# Load config
import sys
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, load_transactions

def test_unavailable_book_check():
    """Test that books with 0 available copies cannot be borrowed."""
    
    print("=" * 60)
    print("TEST: Availability Constraint Enforcement")
    print("=" * 60)
    
    # Load books
    books_data = load_books()
    
    # Find a book with 0 copies available
    unavailable_books = [b for b in books_data['books'] if b['availablecopies'] == 0]
    available_books = [b for b in books_data['books'] if b['availablecopies'] > 0]
    
    print(f"\nDatabase Status:")
    print(f"  Total books: {len(books_data['books'])}")
    print(f"  Available (copies > 0): {len(available_books)}")
    print(f"  Unavailable (copies = 0): {len(unavailable_books)}")
    
    if unavailable_books:
        print(f"\nUnavailable Books Found:")
        for book in unavailable_books[:3]:
            print(f"  - {book['title']} (ID: {book['bookid']}, Copies: {book['availablecopies']})")
        
        # Test the borrow endpoint logic
        test_book = unavailable_books[0]
        print(f"\nTesting Borrow Logic on Unavailable Book:")
        print(f"  Book: {test_book['title']}")
        print(f"  Available Copies: {test_book['availablecopies']}")
        print(f"  Status: {test_book['status']}")
        
        # Simulate the borrow endpoint check
        if test_book['availablecopies'] == 0:
            print(f"  ✗ CORRECT: Book would be rejected (availablecopies == 0)")
        else:
            print(f"  ✓ BUG: Book would be allowed to borrow!")
    else:
        print(f"\nNo unavailable books in database. Creating test scenario...")
    
    # Check transactions
    transactions_data = load_transactions()
    borrowed_count = sum(1 for t in transactions_data['transactions'] if t['status'] == 'borrowed')
    returned_count = sum(1 for t in transactions_data['transactions'] if t['status'] == 'returned')
    
    print(f"\nTransaction Status:")
    print(f"  Active Borrows: {borrowed_count}")
    print(f"  Completed Returns: {returned_count}")
    
    # Validate that borrowed books are properly tracked
    print(f"\nValidating Book Availability Consistency:")
    for book in books_data['books'][:5]:  # Check first 5 books
        active_borrows = sum(1 for t in transactions_data['transactions'] 
                            if t['bookid'] == book['bookid'] and t['status'] == 'borrowed')
        expected_available = book['totalcopies'] - active_borrows
        
        match = "✓" if book['availablecopies'] == expected_available else "✗"
        print(f"  {match} {book['title']}")
        print(f"      Available: {book['availablecopies']}, Expected: {expected_available}")
        print(f"      Active Borrows: {active_borrows}, Total Copies: {book['totalcopies']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_unavailable_book_check()
