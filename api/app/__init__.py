# app/__init__.py
from flask import Flask, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os
import base64
from functools import wraps
from flask import request

# Create extensions first (but don't import from app yet)
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
jwt = JWTManager()
cors = CORS()

# Create CSRF protection functions
def generate_csrf_token():
    """Generate CSRF token"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = base64.b64encode(os.urandom(32)).decode('utf-8')
    return session['_csrf_token']

def csrf_protect():
    """CSRF protection decorator factory"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip CSRF for GET, HEAD, OPTIONS
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                return f(*args, **kwargs)
                
            # Skip CSRF for API endpoints that use JWT
            if request.path.startswith('/api/'):
                return f(*args, **kwargs)
                
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not token or token != session.get('_csrf_token'):
                if request.is_json:
                    return jsonify({
                        'success': False, 
                        'message': 'Invalid CSRF token'
                    }), 403
                else:
                    flash('Invalid CSRF token', 'danger')
                    return redirect(request.referrer or url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
    
    # User loader - import inside function to avoid circular imports
    @login_manager.user_loader
    def load_user(user_id):
        # Import here to avoid circular import
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
    
    # Context processor for has_endpoint
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
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token())
    
    # Register blueprints - import inside function to avoid circular imports
    from .auth import auth_bp
    from .admin import admin_bp
    from .routes import main_bp
    from .api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Only register test blueprint in development mode
    if app.config['DEBUG'] or os.environ.get('ENABLE_TEST_ROUTES', 'false').lower() == 'true':
        try:
            # Import test blueprint inside the condition
            from .test_routes import test_bp
            app.register_blueprint(test_bp, url_prefix='/test')
            app.logger.info("Test blueprint registered - available at /test/*")
        except ImportError as e:
            app.logger.warning(f"Test blueprint not available: {e}")
    
    # Add development-only error handlers
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
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'debug': app.config['DEBUG']
        })
    
    return app