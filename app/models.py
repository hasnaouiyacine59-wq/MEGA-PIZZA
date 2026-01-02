from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime
import uuid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # admin, user, driver
    is_active = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'))
    phone_number = db.Column(db.String(20))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = db.relationship('Restaurant', backref='staff')
    orders_as_driver = db.relationship('Order', foreign_keys='Order.driver_id', backref='driver')
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True)
    
    def get_id(self):
        return str(self.user_id)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_driver(self):
        return self.role == 'driver'
    
    def is_user(self):
        return self.role == 'user'
    
    def can_access_admin(self):
        """Only admin can access admin panel"""
        return self.role == 'admin'
    
    def can_access_driver(self):
        """Driver and admin can access driver panel"""
        return self.role in ['driver', 'admin']
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

# Keep your existing models (Customer, Restaurant, etc.) below
# ... [Your existing models from earlier]