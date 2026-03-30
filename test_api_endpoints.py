#!/usr/bin/env python
"""
Lightweight sanity checks for the newly added endpoints using Flask's test client.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app
import json


def test_history_endpoint():
    with app.test_client() as client:
        # set session to first user
        with client.session_transaction() as sess:
            sess['userid'] = 'USR001'
        resp = client.get('/api/books/user/USR001/history')
        data = resp.get_json()
        print('history status code', resp.status_code)
        print('response keys', list(data.keys()))
        assert resp.status_code == 200
        assert data['success']
        assert isinstance(data.get('history'), list)
        print('history entries', len(data.get('history', [])))


def test_notifications_endpoint():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['userid'] = 'USR001'
        resp = client.get('/api/notifications')
        data = resp.get_json()
        print('notifications status', resp.status_code)
        assert resp.status_code == 200
        assert data['success']
        assert 'notifications' in data
        print('notification count', len(data.get('notifications', [])))


def test_overdue_endpoint():
    with app.test_client() as client:
        # set session to first user
        with client.session_transaction() as sess:
            sess['userid'] = 'USR001'
        resp = client.get('/api/books/user/USR001/overdue')
        data = resp.get_json()
        print('overdue status code', resp.status_code)
        print('response keys', list(data.keys()))
        assert resp.status_code == 200
        assert data['success']
        assert isinstance(data.get('overduebooks'), list)
        print('overdue entries', len(data.get('overduebooks', [])))


def test_overdue_page():
    with app.test_client() as client:
        # set session to first user
        with client.session_transaction() as sess:
            sess['userid'] = 'USR001'
            sess['fullname'] = 'Test User'
        resp = client.get('/overdue')
        print('overdue page status code', resp.status_code)
        assert resp.status_code == 200
        assert b'Overdue Books' in resp.data
        print('overdue page rendered successfully')


if __name__ == '__main__':
    test_history_endpoint()
    test_notifications_endpoint()
    test_overdue_endpoint()
    test_overdue_page()
