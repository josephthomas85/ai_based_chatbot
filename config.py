import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # CORS Configuration
    CORS_ORIGINS = ['*']
    
    # Database paths
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database')
    USERS_DB = os.path.join(DATABASE_PATH, 'users.json')
    BOOKS_DB = os.path.join(DATABASE_PATH, 'books.json')
    TRANSACTIONS_DB = os.path.join(DATABASE_PATH, 'transactions.json')
    NOTIFICATIONS_DB = os.path.join(DATABASE_PATH, 'notifications.json')
    
    # NLP Configuration
    NLP_MODEL = 'en_core_web_sm'
    MIN_CONFIDENCE = 0.5
