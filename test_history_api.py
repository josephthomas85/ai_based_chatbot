#!/usr/bin/env python
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Test the history endpoint
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['userid'] = 'USR001'
    
    resp = client.get('/api/books/user/USR001/history')
    data = resp.get_json()
    print("Response Status:", resp.status_code)
    print("Response Data:")
    print(json.dumps(data, indent=2))
