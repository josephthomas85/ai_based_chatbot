import json
import bcrypt
from flask import request, jsonify, session
from functools import wraps
from config import Config

# Load users database
def load_users():
    try:
        with open(Config.USERS_DB, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": []}

# Save users database
def save_users(data):
    with open(Config.USERS_DB, 'w') as f:
        json.dump(data, f, indent=2)

# Authentication decorator
def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'userid' not in session:
            return jsonify({"success": False, "message": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function

# POST /api/login
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "message": "Missing username or password"}), 400
    
    users_data = load_users()
    
    # Find user
    user = None
    for u in users_data['users']:
        if u['username'] == data['username']:
            user = u
            break
    
    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    # Verify password (bcrypt comparison)
    if not bcrypt.checkpw(data['password'].encode(), user['password'].encode()):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    # Set session
    session['userid'] = user['userid']
    session['username'] = user['username']
    session['fullname'] = user['fullname']
    
    return jsonify({
        "success": True,
        "userid": user['userid'],
        "username": user['username'],
        "fullname": user['fullname'],
        "message": "Login successful"
    }), 200

# POST /api/logout
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

# Register new user
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('fullname'):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    users_data = load_users()
    
    # Check if user exists
    for u in users_data['users']:
        if u['username'] == data['username']:
            return jsonify({"success": False, "message": "Username already exists"}), 409
    
    # Hash password
    hashed_password = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    
    # Generate userid
    userid = f"USR{str(len(users_data['users']) + 1).zfill(3)}"
    
    # Create new user
    new_user = {
        "userid": userid,
        "username": data['username'],
        "password": hashed_password,
        "fullname": data['fullname'],
        "email": data.get('email', ''),
        "registereddate": data.get('registereddate', ''),
        "borrowedbooks": []
    }
    
    users_data['users'].append(new_user)
    save_users(users_data)
    
    return jsonify({
        "success": True,
        "userid": userid,
        "message": "User registered successfully"
    }), 201

# Export functions
from api import api_bp

api_bp.add_url_rule('/login', 'login', login, methods=['POST'])
api_bp.add_url_rule('/logout', 'logout', logout, methods=['POST'])
api_bp.add_url_rule('/register', 'register', register, methods=['POST'])
