import json
import os
import bcrypt

USERS_DB = 'database/users.json'

def load_json(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    users_data = load_json(USERS_DB) or {"users": []}

    # Ensure all existing users have role="student"
    for u in users_data['users']:
        if 'role' not in u:
            u['role'] = 'student'

    # Check if admin already exists
    admin_exists = any(u.get('username') == 'admin' for u in users_data['users'])
    if not admin_exists:
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw(b"admin", salt).decode('utf-8')
        
        uid = f"USR{str(len(users_data['users']) + 1).zfill(3)}_STAFF"
        admin_user = {
            "userid": uid,
            "username": "admin",
            "password": pwd_hash,
            "fullname": "Library Administrator",
            "email": "admin@library.com",
            "registereddate": "2026-01-01",
            "borrowedbooks": [],
            "unpaid_fines": 0,
            "role": "staff"
        }
        users_data['users'].append(admin_user)
        save_json(USERS_DB, users_data)
        print("Successfully seeded the 'admin' staff account.")
    else:
        save_json(USERS_DB, users_data)
        print("Admin account already exists. Backfilled existing user roles.")

if __name__ == '__main__':
    main()
