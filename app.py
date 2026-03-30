"""
Library Management System with AI Chatbot
Main Flask Application
"""

from flask import Flask, render_template, redirect, url_for, session, request
from flask_cors import CORS
from config import Config
from api import api_bp
from api.staff import staff_bp
from api.books import load_books, load_transactions, save_books
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

def validate_book_availability():
    """
    Validate and fix book availability counts on startup.
    Recalculates availablecopies based on active transactions.
    """
    try:
        books_data = load_books()
        transactions_data = load_transactions()
        
        # Count active borrows per book
        borrow_counts = {}
        for transaction in transactions_data['transactions']:
            if transaction['status'] == 'borrowed':
                bookid = transaction['bookid']
                borrow_counts[bookid] = borrow_counts.get(bookid, 0) + 1
        
        # Check for discrepancies
        fixed_count = 0
        for i, book in enumerate(books_data['books']):
            bookid = book['bookid']
            active_borrows = borrow_counts.get(bookid, 0)
            correct_available = book['totalcopies'] - active_borrows
            
            if book['availablecopies'] != correct_available:
                books_data['books'][i]['availablecopies'] = correct_available
                books_data['books'][i]['status'] = 'available' if correct_available > 0 else 'unavailable'
                fixed_count += 1
        
        if fixed_count > 0:
            save_books(books_data)
            app.logger.warning(f"Fixed {fixed_count} book availability counts on startup")
        
        return True
    except Exception as e:
        app.logger.error(f"Error validating book availability: {str(e)}")
        return False

# Register blueprints
app.register_blueprint(api_bp)
app.register_blueprint(staff_bp)

# Staff Routes
@app.route('/staff', methods=['GET'])
def staff_login_page():
    if 'staff_id' in session:
        return redirect(url_for('staff_dashboard_page'))
    return render_template('staff_login.html')

@app.route('/staff/dashboard', methods=['GET'])
def staff_dashboard_page():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login_page'))
    return render_template('staff_dashboard.html')

@app.route('/staff/book/<bookid>', methods=['GET'])
def staff_book_details_page(bookid):
    if 'staff_id' not in session:
        return redirect(url_for('staff_login_page'))
    return render_template('staff_book_details.html', bookid=bookid)

# Routes
@app.route('/')
def index():
    """Public landing page"""
    userid = session.get('userid')
    return render_template('landing.html', userid=userid)

@app.route('/login', methods=['GET'])
def login():
    """Login page"""
    if 'userid' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/home', methods=['GET'])
def home():
    """Home page - requires login"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/profile', methods=['GET'])
def profile_page():
    """Render user profile management page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')


@app.route('/history', methods=['GET'])
def history():
    """Render borrowing/return history page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('history.html')


@app.route('/notifications', methods=['GET'])
def notifications_page():
    """Render notifications listing page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('notifications.html')


@app.route('/overdue', methods=['GET'])
def overdue_page():
    """Render overdue books page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('overdue.html')


@app.route('/chatbot', methods=['GET'])
def chatbot_page():
    """Render library chatbot page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('chatbot.html')


@app.route('/recommendations', methods=['GET'])
def recommendations_page():
    """Render AI recommendations page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('recommendations.html')


@app.route('/mybooks', methods=['GET'])
def mybooks_page():
    """Render user's borrowed books page"""
    if 'userid' not in session:
        return redirect(url_for('login'))
    return render_template('mybooks.html')
@app.errorhandler(404)
def not_found(error):
    return {'success': False, 'message': 'Resource not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'success': False, 'message': 'Internal server error'}, 500

@app.errorhandler(401)
def unauthorized(error):
    return {'success': False, 'message': 'Unauthorized access'}, 401

# Context processors
@app.context_processor
def inject_user():
    """Make user info available in templates"""
    userid = session.get('userid')
    if userid:
        try:
            import json
            with open(Config.USERS_DB, 'r') as f:
                users_data = json.load(f)
                user = next((u for u in users_data.get('users', []) if u['userid'] == userid), None)
                if user:
                    return {
                        'userid': userid,
                        'username': user.get('username'),
                        'fullname': user.get('fullname'),
                        'unpaid_fines': user.get('unpaid_fines', 0)
                    }
        except Exception as e:
            app.logger.error(f"Error fetching live user data: {e}")
            
    return {
        'userid': session.get('userid'),
        'username': session.get('username'),
        'fullname': session.get('fullname')
    }

# CLI Commands
@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    from database_init import init_databases
    init_databases()
    print('Database initialized successfully!')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(Config.DATABASE_PATH, exist_ok=True)
    
    # Validate book availability on startup
    app.logger.info("Validating book availability counts...")
    validate_book_availability()
    
    # Run the app
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=5002,
        threaded=True
    )
