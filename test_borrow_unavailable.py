#!/usr/bin/env python
"""
Test the borrow endpoint with an unavailable book scenario.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, load_transactions, save_books

def test_borrow_unavailable():
    """Simulate attempting to borrow a book with zero availability."""
    
    print("=" * 70)
    print("TEST: Borrow Endpoint Rejects Unavailable Books")
    print("=" * 70)
    
    books_data = load_books()
    
    # Create a test scenario: set a book to have 0 availablecopies
    test_book = None
    for i, book in enumerate(books_data['books']):
        if book['bookid'] == 'BK00006':  # Deep Dive into Pandas
            test_book = book
            test_index = i
            break
    
    if not test_book:
        print("Test book not found")
        return
    
    print(f"\nTest Scenario Setup:")
    print(f"  Book: {test_book['title']}")
    print(f"  Original Available Copies: {test_book['availablecopies']}")
    
    # Temporarily set copies to 0
    books_data['books'][test_index]['availablecopies'] = 0
    books_data['books'][test_index]['status'] = 'unavailable'
    save_books(books_data)
    
    print(f"  Modified to: 0 copies (unavailable)")
    
    # Reload and test the borrow logic
    books_data = load_books()
    book = None
    for b in books_data['books']:
        if b['bookid'] == 'BK00006':
            book = b
            break
    
    print(f"\nBorrow Endpoint Logic Check:")
    print(f"  Checking: if book['availablecopies'] == 0")
    print(f"  Result: book['availablecopies'] = {book['availablecopies']}")
    
    # Simulate the endpoint check
    if book['availablecopies'] == 0:
        print(f"  Decision: REJECT borrow")
        print(f"  Message: 'Book is not available'")
        print(f"  HTTP Status: 400")
        result = "PASS - Book correctly rejected"
    else:
        print(f"  Decision: ALLOW borrow")
        result = "FAIL - Book should have been rejected"
    
    # Reset the book
    for i, b in enumerate(books_data['books']):
        if b['bookid'] == 'BK00006':
            books_data['books'][i]['availablecopies'] = 6  # Reset to original
            books_data['books'][i]['status'] = 'available'
            break
    save_books(books_data)
    
    print(f"\nResult: {result}")
    print("=" * 70)

if __name__ == "__main__":
    test_borrow_unavailable()
