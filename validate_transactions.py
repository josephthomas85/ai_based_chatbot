#!/usr/bin/env python
"""
Validate that all transactions reference existing books.
Clean up any orphaned transactions if needed.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, load_transactions, save_transactions


def validate_transactions():
    """Check if all transaction book IDs exist in books.json"""
    books_data = load_books()
    trans_data = load_transactions()
    
    # Create set of valid book IDs
    valid_ids = {b['bookid'] for b in books_data['books']}
    
    # Find orphaned transactions
    orphaned = []
    valid_trans = []
    
    for t in trans_data['transactions']:
        if t['bookid'] in valid_ids:
            valid_trans.append(t)
        else:
            orphaned.append(t)
    
    print("=" * 80)
    print("📋 TRANSACTION VALIDATION")
    print("=" * 80)
    print(f"\nTotal books in database: {len(valid_ids)}")
    print(f"Total transactions: {len(trans_data['transactions'])}")
    print(f"Valid transactions: {len(valid_trans)}")
    print(f"Orphaned transactions (referencing deleted books): {len(orphaned)}")
    
    if orphaned:
        print("\n⚠️  ORPHANED TRANSACTIONS (will be removed):\n")
        for t in orphaned[:10]:  # Show first 10
            print(f"  - {t['transactionid']}: User {t['userid']} borrowed {t['bookid']} ({t['status']})")
        if len(orphaned) > 10:
            print(f"  ... and {len(orphaned) - 10} more\n")
        
        # Remove orphaned transactions
        trans_data['transactions'] = valid_trans
        save_transactions(trans_data)
        print(f"\n✅ Removed {len(orphaned)} orphaned transactions")
        print(f"   Total transactions now: {len(valid_trans)}")
    else:
        print("\n✓ All transactions reference valid books - no cleanup needed!")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    validate_transactions()
