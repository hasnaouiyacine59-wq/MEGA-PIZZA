from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os

# Create extensions first
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
jwt = JWTManager()
cors = CORS()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mega-pizza-secret-key-2024-dev')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-mega-pizza-secret-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Database configuration
    if os.environ.get('FLASK_ENV') == 'production':
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
            'postgresql://mega_pizza_admin:SecurePass123!@localhost:5432/mega_pizza_db_prod')
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
            'postgresql://mega_pizza_admin:SecurePass123!@localhost:5432/mega_pizza_db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
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
    
    # Context processor for has_endpoint (from original version)
    @app.context_processor
    def utility_processor():
        from flask import url_for
        def has_endpoint(endpoint):
            try:
                url_for(endpoint)
                return True
            except:
                return False
        return dict(has_endpoint=has_endpoint)
    
    # Register blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    from .routes import main_bp
    from .api import api_bp  # Import the new API blueprint
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')  # Register API blueprint with prefix
    
    # Only register test blueprint in development mode
    if app.config['DEBUG'] or os.environ.get('ENABLE_TEST_ROUTES', 'false').lower() == 'true':
        try:
            from .test_routes import test_bp
            app.register_blueprint(test_bp, url_prefix='/test')
            app.logger.info("Test blueprint registered - available at /test/*")
        except ImportError as e:
            app.logger.warning(f"Test blueprint not available: {e}")
    
    # Add development-only error handlers (from original version)
    if app.config['DEBUG']:
        @app.errorhandler(404)
        def not_found_error(error):
            return f"""
            <h1>404 - Page Not Found</h1>
            <p>Available routes:</p>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/admin/dashboard">Admin Dashboard</a></li>
                <li><a href="/test/dashboard">Test Dashboard</a></li>
                <li><a href="/auth/login">Login</a></li>
                <li><a href="/api">API Base</a></li>
            </ul>
            """, 404
    
    # Add health check endpoint (recommended addition)
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'debug': app.config['DEBUG']
        })
    
    return app