#!/usr/bin/env python
"""
Identify and remove duplicate books with same name but different authors.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from api.books import load_books, save_books


def find_duplicate_titles():
    """Find all books with same title but different authors."""
    books_data = load_books()
    
    # Group by title
    by_title = defaultdict(list)
    for book in books_data['books']:
        by_title[book['title']].append(book)
    
    # Find duplicates
    duplicates = {title: books for title, books in by_title.items() if len(books) > 1}
    
    if not duplicates:
        print("✓ No duplicates found - all titles are unique!")
        return []
    
    print(f"\n🔍 Found {len(duplicates)} titles with multiple entries:\n")
    
    dup_list = []
    for title, books_with_title in sorted(duplicates.items()):
        authors = [b['author'] for b in books_with_title]
        if len(set(authors)) > 1:  # Different authors
            print(f"📚 '{title}':")
            for i, book in enumerate(books_with_title):
                print(f"   [{i}] {book['bookid']}: {book['author']} ({book['publicationyear']}) - {book['isbn']}")
            dup_list.append({'title': title, 'books': books_with_title})
        else:
            print(f"✓ '{title}': Same author, different book IDs (OK)")
    
    return dup_list


def remove_duplicates(keep_strategy='first'):
    """
    Remove duplicate titles, keeping only one per title.
    keep_strategy: 'first', 'latest' (by publication year), or 'most_copies'
    """
    books_data = load_books()
    
    # Group by title
    by_title = defaultdict(list)
    for i, book in enumerate(books_data['books']):
        by_title[book['title']].append((i, book))
    
    # Find which indices to keep
    indices_to_remove = []
    kept = 0
    removed = 0
    
    for title, entries in by_title.items():
        if len(entries) > 1:
            # Check if different authors
            authors = set(b['author'] for i, b in entries)
            
            if len(authors) > 1:
                # Select which one to keep based on strategy
                if keep_strategy == 'first':
                    keep_idx = entries[0][0]
                elif keep_strategy == 'latest':
                    keep_idx = max(entries, key=lambda x: x[1]['publicationyear'])[0]
                elif keep_strategy == 'most_copies':
                    keep_idx = max(entries, key=lambda x: x[1]['totalcopies'])[0]
                else:
                    keep_idx = entries[0][0]
                
                # Mark others for removal
                for idx, book in entries:
                    if idx != keep_idx:
                        indices_to_remove.append(idx)
                        removed += 1
                
                kept += 1
    
    if not indices_to_remove:
        print("✓ No duplicates to remove (different authors or same book)")
        return False
    
    print(f"\n🗑️  Will remove {removed} duplicate entries (keeping {kept} titles with 1 copy each)")
    
    # Create new book list without duplicates
    new_books = [b for i, b in enumerate(books_data['books']) if i not in indices_to_remove]
    
    # Show what's being removed
    print("\nRemoving:")
    for idx in sorted(indices_to_remove, reverse=True):  # reverse to show nicely
        removed_book = books_data['books'][idx]
        print(f"  - {removed_book['bookid']}: '{removed_book['title']}' by {removed_book['author']}")
    
    # Save
    books_data['books'] = new_books
    save_books(books_data)
    print(f"\n✓ Saved! Removed {removed} duplicates. Total books: {len(new_books)}")
    return True


if __name__ == '__main__':
    print("=" * 70)
    print("DUPLICATE BOOK DETECTOR")
    print("=" * 70)
    
    print("\n1️⃣  Scanning for duplicate titles with different authors...\n")
    dups = find_duplicate_titles()
    
    if dups:
        print("\n" + "=" * 70)
        print("2️⃣  REMOVING DUPLICATES...")
        print("=" * 70)
        confirm = input("\nProceed with removal? (yes/no): ").strip().lower()
        if confirm == 'yes':
            remove_duplicates(keep_strategy='first')
        else:
            print("Cancelled.")
    else:
        print("\n✓ No action needed.")
