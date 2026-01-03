from flask_login import UserMixin
from . import db, bcrypt
from datetime import datetime
import time as time_module
import json

# ============================================
# USER MODEL
# ============================================
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='employee', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'))
    phone_number = db.Column(db.String(20))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver_profile = db.relationship('Driver', backref='user', uselist=False, cascade='all, delete-orphan')
    customer_profile = db.relationship('Customer', backref='user', uselist=False, cascade='all, delete-orphan')
    restaurant = db.relationship('Restaurant', backref='users')
    
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
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_employee(self):
        return self.role == 'employee'
    
    def is_customer(self):
        return self.role == 'user'


# ============================================
# RESTAURANT MODEL
# ============================================
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    
    restaurant_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    delivery_radius = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    is_open = db.Column(db.Boolean, default=True)
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    min_order_amount = db.Column(db.Numeric(10, 2), default=0.00)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0.00)
    estimated_prep_time = db.Column(db.Integer)
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_reviews = db.Column(db.Integer, default=0)
    logo_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    
    def is_open_now(self):
        """Check if restaurant is open now"""
        if not self.is_open:
            return False
        
        now = datetime.now().time()
        return self.opening_time <= now <= self.closing_time
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'


# ============================================
# DRIVER MODEL
# ============================================
class Driver(db.Model):
    __tablename__ = 'drivers'
    
    driver_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    
    # Driver-specific information
    license_number = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(20))  # car, motorcycle, bicycle, scooter
    vehicle_model = db.Column(db.String(50))
    license_plate = db.Column(db.String(20))
    
    # Driver status
    is_available = db.Column(db.Boolean, default=True)
    current_location = db.Column(db.String(100))
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    
    # Statistics
    total_deliveries = db.Column(db.Integer, default=0)
    completed_deliveries = db.Column(db.Integer, default=0)
    failed_deliveries = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Numeric(10, 2), default=0.00)
    avg_delivery_time = db.Column(db.Integer)  # in minutes
    
    # Working hours
    shift_start = db.Column(db.Time)
    shift_end = db.Column(db.Time)
    is_on_shift = db.Column(db.Boolean, default=False)
    
    # Emergency contact
    emergency_contact = db.Column(db.String(50))
    emergency_phone = db.Column(db.String(20))
    
    # Document expiry dates
    license_expiry = db.Column(db.Date)
    insurance_expiry = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='driver', lazy=True)
    
    def get_status_badge(self):
        if not self.is_available:
            return 'Busy'
        elif self.is_on_shift:
            return 'On Duty'
        else:
            return 'Off Duty'
    
    def calculate_rating_stars(self):
        if not self.rating:
            return ''
        
        stars = ""
        full_stars = int(self.rating)
        half_star = float(self.rating) - full_stars >= 0.5
        
        for _ in range(full_stars):
            stars += '<i class="fas fa-star text-warning"></i>'
        
        if half_star:
            stars += '<i class="fas fa-star-half-alt text-warning"></i>'
        
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        for _ in range(empty_stars):
            stars += '<i class="far fa-star text-warning"></i>'
        
        return stars
    
    def __repr__(self):
        return f'<Driver {self.user.username if self.user else "No User"}>'


# ============================================
# CUSTOMER MODEL
# ============================================
class Customer(db.Model):
    __tablename__ = 'customers'
    
    customer_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    addresses = db.relationship('Address', backref='customer', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name}>'


# ============================================
# ADDRESS MODEL
# ============================================
class Address(db.Model):
    __tablename__ = 'addresses'
    
    address_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.customer_id'))
    street = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='USA')
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Address {self.street[:50]}>'


# ============================================
# MENU ITEM MODEL
# ============================================
class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    item_id = db.Column(db.String(20), primary_key=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'


# ============================================
# ORDER MODEL
# ============================================
class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.String(30), primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.customer_id'), nullable=False)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    
    # Order details
    order_status = db.Column(db.String(20), default='pending', nullable=False)
    delivery_type = db.Column(db.String(10), default='delivery')
    special_instructions = db.Column(db.Text)
    
    # Pricing
    subtotal = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0.00)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0.00)
    discount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    
    # Payment
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    
    # Driver info
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'))
    driver_rating = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estimated_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_id} - {self.order_status}>'
    
    def get_status_badge_class(self):
        status_classes = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'out_for_delivery': 'info',
            'delivered': 'success',
            'cancelled': 'danger'
        }
        return status_classes.get(self.order_status, 'secondary')


# ============================================
# ORDER ITEM MODEL
# ============================================
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.String(20), db.ForeignKey('menu_items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    customizations = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_total(self):
        """Calculate total price for this item"""
        return float(self.unit_price) * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'


# ============================================
# ORDER STATUS HISTORY MODEL
# ============================================
class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    # Relationships
    changer = db.relationship('User', backref='status_changes', lazy=True)
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.old_status} -> {self.new_status}>'


# ============================================
# AUTHENTICATION MODELS
# ============================================
class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    attempt_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='login_attempts', lazy=True)


class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    session_id = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    token = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='sessions', lazy=True)


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    token_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='password_reset_tokens', lazy=True)