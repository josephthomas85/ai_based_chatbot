#!/usr/bin/env python
"""
Simulate the exact flow that happens when user navigates to history page
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from app import app

print("=" * 80)
print("🧪 SIMULATING ACTUAL BROWSER FLOW")
print("=" * 80)

with app.test_client() as client:
    # Step 1: Set session directly (simulating logged-in user)
    print("\n1️⃣  Setting up logged-in session...")
    with client.session_transaction() as sess:
        sess['userid'] = 'USR001'
        sess['username'] = 'arjun'
        sess['fullname'] = 'ARJUN R'
    print("   ✅ Session set with userid=USR001")
    
    # Step 2: Navigate to history page
    print("\n2️⃣  GET /history page...")
    history_resp = client.get('/history')
    print(f"   Status: {history_resp.status_code}")
    html = history_resp.data.decode()
    
    # Check if data attributes are in HTML
    if 'data-userid=' in html:
        print(f"   ✅ data-userid found in HTML")
        import re
        match = re.search(r'data-userid="([^"]+)"', html)
        if match:
            print(f"   📊 Value: data-userid=\"{match.group(1)}\"")
    else:
        print(f"   ❌ data-userid NOT found in HTML")
        print(f"   First 500 chars of HTML: {html[:500]}")
    
    # Check container exists
    if 'historyContainer' in html:
        print(f"   ✅ historyContainer exists in HTML")
    else:
        print(f"   ❌ historyContainer NOT found in HTML")
    
    # Step 3: Call the API directly like the JavaScript would
    print("\n3️⃣  Call API GET /api/books/user/USR001/history...")
    api_resp = client.get('/api/books/user/USR001/history')
    print(f"   Status: {api_resp.status_code}")
    api_data = api_resp.get_json()
    print(f"   Response structure:")
    print(f"     - success: {api_data.get('success')}")
    print(f"     - total: {api_data.get('total')}")
    print(f"     - history count: {len(api_data.get('history', []))}")
    
    if api_data.get('success'):
        hist = api_data.get('history', [])
        if hist:
            print(f"\n   ✅ Found {len(hist)} history entries!")
            print(f"\n   First 3 entries:")
            for i, entry in enumerate(hist[:3]):
                print(f"     [{i}] {entry.get('title')} by {entry.get('author')} ({entry.get('status')})")
        else:
            print(f"   ⚠️ No history entries returned (empty list)")
    else:
        print(f"   ❌ API error: {api_data.get('message')}")
    
    print("\n" + "=" * 80)

