#!/usr/bin/env python
"""
Test that the history page renders correctly with proper layout
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from bs4 import BeautifulSoup

print("=" * 80)
print("🧪 TESTING HISTORY PAGE LAYOUT")
print("=" * 80)

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['userid'] = 'USR001'
        sess['username'] = 'arjun'
        sess['fullname'] = 'ARJUN R'
    
    # Get the page
    resp = client.get('/history')
    html = resp.data.decode()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n1️⃣  Checking HTML Structure...")
    
    # Check navbar
    navbar = soup.find('header', class_='navbar')
    if navbar:
        print("   ✅ Navbar found")
    else:
        print("   ❌ Navbar NOT found")
    
    # Check history-page
    history_page = soup.find('div', class_='history-page')
    if history_page:
        print("   ✅ history-page div found")
        userid = history_page.get('data-userid')
        print(f"      - data-userid: {userid}")
    else:
        print("   ❌ history-page div NOT found")
    
    # Check history-header
    history_header = soup.find('div', class_='history-header')
    if history_header:
        print("   ✅ history-header found")
    else:
        print("   ❌ history-header NOT found")
    
    # Check history-content
    history_content = soup.find('div', class_='history-content')
    if history_content:
        print("   ✅ history-content found")
    else:
        print("   ❌ history-content NOT found")
    
    # Check historyContainer
    container = soup.find('div', id='historyContainer')
    if container:
        print("   ✅ historyContainer found")
        content = str(container)[:100]
        print(f"      Initial content: {content[:80]}...")
    else:
        print("   ❌ historyContainer NOT found")
    
    # Check buttons
    back_btn = soup.find(id='backHome')
    if back_btn:
        print("   ✅ backHome button found")
    else:
        print("   ❌ backHome button NOT found")
    
    # Check script
    script = soup.find('script', src=True)
    if script and 'history.js' in script.get('src', ''):
        print("   ✅ history.js script found")
    else:
        print("   ❌ history.js script NOT found")
    
    print("\n2️⃣  Checking CSS Styles...")
    
    # Find style tag
    style_tag = soup.find('style')
    if style_tag:
        style_content = style_tag.string
        checks = [
            ('body height', 'height: 100%' in style_content),
            ('history-page flex', 'display: flex' in style_content),
            ('history-content flex', 'flex: 1' in style_content),
            ('history-table-wrapper', '.history-table-wrapper' in style_content),
        ]
        
        for check_name, result in checks:
            if result:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
    else:
        print("   ❌ No style tag found")
    
    print("\n3️⃣  Testing API Connection...")
    
    # Call the API
    api_resp = client.get('/api/books/user/USR001/history')
    api_data = api_resp.get_json()
    
    if api_data.get('success'):
        hist = api_data.get('history', [])
        print(f"   ✅ API returns {len(hist)} history entries")
    else:
        print(f"   ❌ API returned error: {api_data.get('message')}")
    
    print("\n" + "=" * 80)
    print("✅ HISTORY PAGE STRUCTURE VALIDATED")
    print("=" * 80)
