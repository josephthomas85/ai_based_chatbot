# API package initialization
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import auth, books, chat, notifications

__all__ = ['api_bp', 'auth', 'books', 'chat']
