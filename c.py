# create_admin.py
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mega_pizza_admin:SecurePass123!@localhost:5432/mega_pizza_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'temp-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Define User model inline
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # Update existing admin with Flask-bcrypt hash
        admin.password = 'Admin@123'
        db.session.commit()
        print("✅ Updated admin password to use Flask-Bcrypt")
    else:
        # Create new admin
        admin = User(
            username='admin',
            email='admin@megapizza.com',
            role='admin',
            is_active=True
        )
        admin.password = 'Admin@123'
        db.session.add(admin)
        db.session.commit()
        print("✅ Created new admin with Flask-Bcrypt password")
    
    print("\n🔑 Login Credentials:")
    print("   Username: admin")
    print("   Password: Admin@123")
    print("\n🎉 Done! You can now login to your Flask app.")
