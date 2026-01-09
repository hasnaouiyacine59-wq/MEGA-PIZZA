# api/app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
import sys
from datetime import datetime

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Import shared models - but only db and bcrypt
from shared.models import db as shared_db, bcrypt as shared_bcrypt

# Create extensions
jwt = JWTManager()
cors = CORS()

def create_api_app():
    """Create a Flask application for the API service only"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'api-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-api-secret-key-2024')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 
        'postgresql://mega_pizza_admin:SecurePass123!@postgres:5432/mega_pizza_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'
    
    # Initialize extensions with app
    shared_db.init_app(app)
    shared_bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "message": "Token has expired",
            "error": "token_expired"
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "success": False,
            "message": "Invalid token",
            "error": "invalid_token"
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "success": False,
            "message": "Missing authorization token",
            "error": "authorization_required"
        }), 401
    
    # Register API blueprint
    from .api import api_bp
    app.register_blueprint(api_bp)
    
    # Simple root endpoint
    @app.route('/')
    def index():
        return {
            'service': 'Mega Pizza Delivery API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, 200
    
    return app