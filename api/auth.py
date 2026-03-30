import json
import bcrypt
import os
from werkzeug.utils import secure_filename
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
    userid = session.get('userid')
    if userid:
        try:
            from api.chat import USER_CHAT_MEMORY
            USER_CHAT_MEMORY.pop(userid, None)
        except Exception as e:
            pass

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
# POST /api/pay_fines
@require_login
def pay_fines():
    userid = session.get('userid')
    users_data = load_users()
    
    for u in users_data['users']:
        if u['userid'] == userid:
            if u.get('unpaid_fines', 0) == 0:
                return jsonify({"success": False, "message": "No outstanding fines to pay"}), 400
            u['unpaid_fines'] = 0
            break
            
    save_users(users_data)
    return jsonify({"success": True, "message": "Fines paid successfully"}), 200

# GET /api/user/profile
@require_login
def get_profile():
    userid = session.get('userid')
    users_data = load_users()
    for u in users_data['users']:
        if u['userid'] == userid:
            profile = u.copy()
            if 'password' in profile:
                del profile['password']
            return jsonify({"success": True, "user": profile}), 200
    return jsonify({"success": False, "message": "User not found"}), 404

# POST /api/user/update_profile
@require_login
def update_profile():
    userid = session.get('userid')
    data = request.get_json()
    users_data = load_users()
    
    new_username = data.get('username')
    for u in users_data['users']:
        if u['username'] == new_username and u['userid'] != userid:
            return jsonify({"success": False, "message": "Username already taken"}), 409
            
    for u in users_data['users']:
        if u['userid'] == userid:
            if data.get('fullname'): u['fullname'] = data['fullname']
            if data.get('username'): u['username'] = data['username']
            if data.get('email') is not None: u['email'] = data['email']
            if data.get('phone') is not None: u['phone'] = data['phone']
            
            if data.get('fullname'): session['fullname'] = data['fullname']
            if data.get('username'): session['username'] = data['username']
            
            save_users(users_data)
            return jsonify({"success": True, "message": "Profile updated"}), 200
            
    return jsonify({"success": False, "message": "User not found"}), 404

# POST /api/user/upload_photo
@require_login
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({"success": False, "message": "No photo provided"}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
        
    if file:
        userid = session.get('userid')
        filename = secure_filename(file.filename)
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        new_filename = f"{userid}_avatar.{ext}"
        
        upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, new_filename)
        
        file.save(file_path)
        
        photo_url = f"/static/uploads/profiles/{new_filename}"
        
        users_data = load_users()
        for u in users_data['users']:
            if u['userid'] == userid:
                u['profile_photo'] = photo_url
                save_users(users_data)
                return jsonify({"success": True, "photo_url": photo_url}), 200
                
    return jsonify({"success": False, "message": "Error uploading file"}), 500

# Export functions
from api import api_bp

api_bp.add_url_rule('/login', 'login', login, methods=['POST'])
api_bp.add_url_rule('/logout', 'logout', logout, methods=['POST'])
api_bp.add_url_rule('/register', 'register', register, methods=['POST'])
api_bp.add_url_rule('/pay_fines', 'pay_fines', pay_fines, methods=['POST'])
api_bp.add_url_rule('/user/profile', 'get_profile', get_profile, methods=['GET'])
api_bp.add_url_rule('/user/update_profile', 'update_profile', update_profile, methods=['POST'])
api_bp.add_url_rule('/user/upload_photo', 'upload_photo', upload_photo, methods=['POST'])
