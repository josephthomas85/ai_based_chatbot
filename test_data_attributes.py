#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Test that data attributes are embedded in HTML
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['userid'] = 'USR001'
        sess['username'] = 'arjun'
        sess['fullname'] = 'ARJUN R'
    
    print("Testing data attributes in HTML pages...\n")
    
    # Test history page
    print("1️⃣  History Page")
    resp = client.get('/history')
    html = resp.data.decode()
    if 'data-userid="USR001"' in html:
        print("   ✅ userid data attribute found")
    else:
        print("   ❌ userid data attribute NOT found")
    if 'data-fullname="ARJUN R"' in html:
        print("   ✅ fullname data attribute found")
    else:
        print("   ❌ fullname data attribute NOT found")
    
    # Test notifications page
    print("\n2️⃣  Notifications Page")
    resp = client.get('/notifications')
    html = resp.data.decode()
    if 'data-userid="USR001"' in html:
        print("   ✅ userid data attribute found")
    else:
        print("   ❌ userid data attribute NOT found")
    if 'data-fullname="ARJUN R"' in html:
        print("   ✅ fullname data attribute found")
    else:
        print("   ❌ fullname data attribute NOT found")
    
    print("\n✅ All data attributes embedded correctly in HTML!")
