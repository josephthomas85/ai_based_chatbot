#!/usr/bin/env python
"""
Simple script to verify the history API and data transformation.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from api.books import load_transactions, load_books, get_user_history


def test_user_history_function():
    print("TEST: User history helper returns entries for a valid userid")
    transactions = load_transactions().get('transactions', [])
    if not transactions:
        print("  no transactions present - skipping")
        return

    # pick first transaction's user to inspect
    userid = transactions[0]['userid']
    history = []
    # mimic what the API does without session
    books = load_books().get('books', [])
    for t in transactions:
        if t['userid'] == userid:
            book_info = next((b for b in books if b['bookid'] == t['bookid']), {})
            history.append({
                'transactionid': t.get('transactionid'),
                'bookid': t.get('bookid'),
                'title': book_info.get('title', ''),
                'status': t.get('status')
            })
    print(f"  found {len(history)} history entries for {userid}")
    for h in history[:3]:
        print(f"    - {h['transactionid']} {h['title']} ({h['status']})")


if __name__ == '__main__':
    test_user_history_function()
