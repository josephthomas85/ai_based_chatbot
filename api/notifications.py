import json
from flask import request, jsonify, session
from datetime import datetime, timedelta
from config import Config
from api.auth import require_login, load_users, save_users

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

    def save_transactions(data):
        with open(Config.TRANSACTIONS_DB, 'w') as f:
            json.dump(data, f, indent=2)

    books_data = load_books()
    tr_data = load_transactions()
    users_data = load_users()
    now = datetime.now().date()
    
    databases_updated = False
    
    for t in tr_data['transactions']:
        if t['userid'] == userid and t['status'] == 'borrowed':
            try:
                due = datetime.fromisoformat(t['duedate']).date()
            except Exception:
                due = datetime.strptime(t['duedate'], '%Y-%m-%d').date()
            
            days_left = (due - now).days
            
            book = next((b for b in books_data['books'] if b['bookid'] == t['bookid']), None)
            if not book:
                continue

            if days_left > 0:
                msg = f"Daily Reminder: '{book['title']}' is due in {days_left} days ({t['duedate']})"
            elif days_left == 0:
                msg = f"URGENT: '{book['title']}' is due TODAY! Please return it."
            else:
                msg = f"OVERDUE: '{book['title']}' was due {abs(days_left)} days ago!"
                
                # Fines Calculation
                last_fine = t.get('last_fine_date')
                if last_fine != now.isoformat():
                    fine_amount = 1 # $1 per day
                    
                    if last_fine:
                        try:
                            last_fine_dt = datetime.fromisoformat(last_fine).date()
                        except Exception:
                            last_fine_dt = datetime.strptime(last_fine, '%Y-%m-%d').date()
                        days_to_fine = (now - last_fine_dt).days
                    else:
                        days_to_fine = (now - due).days
                    
                    if days_to_fine > 0:
                        total_fine = days_to_fine * fine_amount
                        t['last_fine_date'] = now.isoformat()
                        
                        # Add fine to user's unpaid_fines
                        for u in users_data['users']:
                            if u['userid'] == userid:
                                current_fines = float(u.get('unpaid_fines', 0))
                                u['unpaid_fines'] = current_fines + total_fine
                                break
                        
                        databases_updated = True

            # Add the date to the ID so it creates a unique notification each day
            # This effectively gives them a new daily notification
            notif_id = f"due-{t['transactionid']}-{now.strftime('%Y%m%d')}"
            user_notifs.append({
                "id": notif_id,
                "userid": userid,
                "message": msg,
                "read": False,
                "timestamp": t['duedate']
            })

    if databases_updated:
        save_users(users_data)
        save_transactions(tr_data)

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
