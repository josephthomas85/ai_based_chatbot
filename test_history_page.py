#!/usr/bin/env python
"""Quick test to verify history page is working correctly"""

from app import app

print("=" * 80)
print("🧪 TESTING HISTORY PAGE")
print("=" * 80)

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['userid'] = 'USR001'
        sess['username'] = 'arjun'
        sess['fullname'] = 'ARJUN R'
    
    # Test the history page route
    resp = client.get('/history')
    print(f"\n✅ History page response status: {resp.status_code}")
    
    # Check if data attributes are in HTML
    html = resp.data.decode()
    
    if 'data-userid="USR001"' in html:
        print('✅ data-userid attribute found in HTML')
    else:
        print('❌ data-userid attribute NOT found in HTML')
    
    if 'data-fullname="ARJUN R"' in html:
        print('✅ data-fullname attribute found in HTML')
    else:
        print('❌ data-fullname attribute NOT found in HTML')
    
    if 'history.js' in html:
        print('✅ history.js script is included')
    else:
        print('❌ history.js script NOT found')
    
    if 'id="historyContainer"' in html:
        print('✅ historyContainer element found')
    else:
        print('❌ historyContainer element NOT found')
    
    # Test the API endpoint
    print("\n" + "-" * 80)
    api_resp = client.get('/api/books/user/USR001/history')
    api_data = api_resp.get_json()
    print(f'✅ API response status: {api_resp.status_code}')
    print(f'✅ API success: {api_data.get("success")}')
    if api_data.get('success'):
        hist = api_data.get("history", [])
        print(f'✅ History entries returned: {len(hist)}')
        if len(hist) > 0:
            print(f'\n📖 First entry: {hist[0].get("title")} by {hist[0].get("author")}')
            print(f'   Status: {hist[0].get("status")}')
    else:
        print(f'❌ API error: {api_data.get("message")}')

print("\n" + "=" * 80)
print("✅ TESTS COMPLETE")
print("=" * 80)
