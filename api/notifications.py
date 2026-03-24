import json
from flask import request, jsonify, session
from datetime import datetime, timedelta
from config import Config
from api.auth import require_login, load_users

# Notification data helpers

def load_notifications():
    try:
        with open(Config.NOTIFICATIONS_DB, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"notifications": [], "watchers": []}


def save_notifications(data):
    with open(Config.NOTIFICATIONS_DB, 'w') as f:
        json.dump(data, f, indent=2)


def add_notification(userid, message):
    """Add a simple notification for a user."""
    data = load_notifications()
    nid = f"NTF{str(len(data['notifications']) + 1).zfill(3)}"
    data['notifications'].append({
        "id": nid,
        "userid": userid,
        "message": message,
        "read": False,
        "timestamp": datetime.now().isoformat()
    })
    save_notifications(data)
    return nid


def notify_staff(message):
    """Add a notification for all staff members."""
    users_data = load_users()
    staff_ids = [u['userid'] for u in users_data['users'] if u.get('role') == 'staff']
    
    data = load_notifications()
    for sid in staff_ids:
        nid = f"NTF{str(len(data['notifications']) + 1).zfill(3)}"
        data['notifications'].append({
            "id": nid,
            "userid": sid,
            "message": message,
            "read": False,
            "timestamp": datetime.now().isoformat()
        })
    save_notifications(data)


def add_watcher(userid, bookid):
    """Keep track of a user wanting to be notified when a book is restocked."""
    data = load_notifications()
    watchers = data.get("watchers", [])
    # avoid duplicate watchers for same book/user
    if not any(w for w in watchers if w['userid'] == userid and w['bookid'] == bookid):
        watchers.append({
            "userid": userid,
            "bookid": bookid,
            "requested_on": datetime.now().isoformat()
        })
        data['watchers'] = watchers
        save_notifications(data)


def notify_watchers(book):
    """Generate restock notifications for users watching a given book.

    This helper modifies the notification data directly instead of calling
    :func:`add_notification`, because ``add_notification`` reloads and saves
    the file; if we call it while holding an earlier copy of ``data`` we
    would overwrite the newly added entries when we save again. Keeping the
    work in one place prevents lost notifications.
    """
    data = load_notifications()
    watchers = data.get("watchers", [])
    to_notify = [w for w in watchers if w['bookid'] == book['bookid']]

    # append notifications directly to same data object
    for w in to_notify:
        nid = f"NTF{str(len(data['notifications']) + 1).zfill(3)}"
        data['notifications'].append({
            "id": nid,
            "userid": w['userid'],
            "message": f"Good news! '{book['title']}' is back in stock.",
            "read": False,
            "timestamp": datetime.now().isoformat()
        })

    # remove watchers for this book and save
    data['watchers'] = [w for w in watchers if w['bookid'] != book['bookid']]
    save_notifications(data)


# API endpoints
@require_login
def get_notifications():
    userid = session['userid']
    data = load_notifications()
    user_notifs = [n for n in data['notifications'] if n['userid'] == userid]

    # calculate upcoming due-date reminders (within 3 days)
    def load_books():
        try:
            with open(Config.BOOKS_DB, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"books": []}

    def load_transactions():
        try:
            with open(Config.TRANSACTIONS_DB, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"transactions": []}

    books_data = load_books()
    tr_data = load_transactions()
    now = datetime.now().date()
    for t in tr_data['transactions']:
        if t['userid'] == userid and t['status'] == 'borrowed':
            try:
                due = datetime.fromisoformat(t['duedate']).date()
            except Exception:
                due = datetime.strptime(t['duedate'], '%Y-%m-%d').date()
            if due <= now + timedelta(days=3):
                book = next((b for b in books_data['books'] if b['bookid'] == t['bookid']), None)
                if book:
                    user_notifs.append({
                        "id": f"due-{t['transactionid']}",
                        "userid": userid,
                        "message": f"Reminder: '{book['title']}' is due on {t['duedate']}",
                        "read": False,
                        "timestamp": t['duedate']
                    })

    return jsonify({"success": True, "notifications": user_notifs}), 200


@require_login
def mark_read():
    data = load_notifications()
    body = request.get_json()
    ids = body.get('ids', [])
    for n in data['notifications']:
        if n['id'] in ids:
            n['read'] = True
    save_notifications(data)
    return jsonify({"success": True}), 200


# register routes
from api import api_bp
api_bp.add_url_rule('/notifications', 'get_notifications', get_notifications, methods=['GET'])
api_bp.add_url_rule('/notifications/mark_read', 'mark_read', mark_read, methods=['POST'])
