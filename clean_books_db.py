#!/usr/bin/env python
"""
Automatically remove duplicate books with same name but different authors.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, save_books


def remove_duplicates_auto():
    """
    Automatically remove duplicate titles, keeping first occurrence.
    """
    books_data = load_books()
    original_count = len(books_data['books'])
    
    # Group by title
    by_title = defaultdict(list)
    for i, book in enumerate(books_data['books']):
        by_title[book['title']].append((i, book))
    
    # Find duplicates to remove
    indices_to_remove = []
    removed_entries = []
    
    for title, entries in by_title.items():
        if len(entries) > 1:
            # Check if different authors
            authors = set(b['author'] for i, b in entries)
            
            if len(authors) > 1:
                # Keep first, remove rest
                for idx, book in entries[1:]:
                    indices_to_remove.append(idx)
                    removed_entries.append({
                        'bookid': book['bookid'],
                        'title': book['title'],
                        'author': book['author'],
                        'kept_bookid': entries[0][1]['bookid'],
                        'kept_author': entries[0][1]['author']
                    })
    
    if not indices_to_remove:
        print("✓ No duplicates found - all titles are unique or have same author!")
        return
    
    # Create new book list
    new_books = [b for i, b in enumerate(books_data['books']) if i not in indices_to_remove]
    
    print("=" * 80)
    print("🗑️  REMOVING DUPLICATE BOOKS (same name, different authors)")
    print("=" * 80)
    print(f"\nTotal books before: {original_count}")
    print(f"Duplicates found & removed: {len(removed_entries)}\n")
    
    print("REMOVED ENTRIES:")
    print("-" * 80)
    for entry in removed_entries:
        print(f"  ❌ {entry['bookid']:9} '{entry['title']}'")
        print(f"     Removed: {entry['author']}")
        print(f"     Kept:    {entry['kept_author']} (ID: {entry['kept_bookid']})\n")
    
    # Save
    books_data['books'] = new_books
    save_books(books_data)
    
    print("-" * 80)
    print(f"✅ SUCCESS! Total books after: {len(new_books)}")
    print(f"   Removed: {len(removed_entries)} duplicates")


if __name__ == '__main__':
    remove_duplicates_auto()
