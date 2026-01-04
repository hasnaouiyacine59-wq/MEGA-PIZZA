from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os

# Create extensions first
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mega-pizza-secret-key-2024-dev')
    
    # Database configuration based on environment
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
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # User loader - must be defined after app context
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import inside function to avoid circular import
        return User.query.get(int(user_id))
    
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
    
    # Register blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    from .routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    
    # Only register test blueprint in development mode
    if app.config['DEBUG'] or os.environ.get('ENABLE_TEST_ROUTES', 'false').lower() == 'true':
        try:
            from .test_orders import test_bp
            app.register_blueprint(test_bp)
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
            </ul>
            """, 404
    
    return app