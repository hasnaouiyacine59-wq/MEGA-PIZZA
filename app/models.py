from flask_login import UserMixin
from . import db, bcrypt
from datetime import datetime
import time as time_module
# REMOVE THIS LINE: from app.models import Order
# REMOVE THESE LINES: print(dir(Order)) and print(Order.__table__.columns.keys())

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    phone_number = db.Column(db.String(20))
    
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

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    driver_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    
    # Driver-specific fields
    license_number = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(20))  # car, motorcycle, bicycle, scooter
    vehicle_model = db.Column(db.String(50))
    license_plate = db.Column(db.String(20))
    
    # Driver status
    is_available = db.Column(db.Boolean, default=True)
    current_location = db.Column(db.String(100))  # For tracking
    rating = db.Column(db.Float, default=0.0)
    
    # Statistics
    total_deliveries = db.Column(db.Integer, default=0)
    completed_deliveries = db.Column(db.Integer, default=0)
    failed_deliveries = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    avg_delivery_time = db.Column(db.Integer)  # in minutes
    
    # Working hours
    shift_start = db.Column(db.Time)
    shift_end = db.Column(db.Time)
    is_on_shift = db.Column(db.Boolean, default=False)
    
    # Contact info (can be different from user account)
    emergency_contact = db.Column(db.String(50))
    emergency_phone = db.Column(db.String(20))
    
    # Documents
    license_expiry = db.Column(db.Date)
    insurance_expiry = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('driver_profile', lazy=True))
    deliveries = db.relationship('Order', backref='assigned_driver', lazy=True)
    
    def __repr__(self):
        return f'<Driver {self.user.username if self.user else "No User"}>'
    
    def get_status_badge(self):
        if not self.is_available:
            return '<span class="badge bg-danger">Busy</span>'
        elif self.is_on_shift:
            return '<span class="badge bg-success">On Duty</span>'
        else:
            return '<span class="badge bg-secondary">Off Duty</span>'
    
    def calculate_rating_stars(self):
        stars = ""
        full_stars = int(self.rating)
        half_star = self.rating - full_stars >= 0.5
        
        for _ in range(full_stars):
            stars += '<i class="fas fa-star text-warning"></i>'
        
        if half_star:
            stars += '<i class="fas fa-star-half-alt text-warning"></i>'
        
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        for _ in range(empty_stars):
            stars += '<i class="far fa-star text-warning"></i>'
        
        return stars

class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.String(30), primary_key=True, default=lambda: f"ORD-{int(time_module.time()*1000)}")
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'), index=True)
    
    # Basic order info
    order_status = db.Column(db.String(20), default='pending', nullable=False)  # Note: field is order_status, not status
    delivery_type = db.Column(db.String(10), default='delivery')  # delivery/pickup
    
    # Pricing
    subtotal = db.Column(db.Numeric(10, 2), default=0.00)
    tax = db.Column(db.Numeric(10, 2), default=0.00)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0.00)
    discount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Payment
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    estimated_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (only to existing models)
    user = db.relationship('User', backref='orders', lazy=True)
    driver = db.relationship('Driver', backref='orders', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.order_id} - {self.order_status}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False, index=True)
    item_id = db.Column(db.String(20), db.ForeignKey('menu_items.item_id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Customizations
    customizations = db.Column(db.JSON)  # Store as JSON: {"extra_cheese": true, "no_onions": true}
    special_instructions = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    menu_item = db.relationship('MenuItem', backref='order_items', lazy=True)
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id} for Order {self.order_id}>'
    
    def calculate_total(self):
        """Calculate total price for this item"""
        return float(self.unit_price) * self.quantity

class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False, index=True)
    
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    
    changed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    changer = db.relationship('User', backref='status_changes', lazy=True)
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.old_status} -> {self.new_status}>'

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    
    restaurant_id = db.Column(db.String(20), primary_key=True, default=lambda: f"REST-{int(time_module.time()*1000)}")
    
    # Basic info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Contact info
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Location
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    delivery_radius = db.Column(db.Integer, default=5000)  # in meters
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_open = db.Column(db.Boolean, default=True)
    
    # Timing
    opening_time = db.Column(db.Time, default=datetime.strptime("10:00", "%H:%M").time())
    closing_time = db.Column(db.Time, default=datetime.strptime("22:00", "%H:%M").time())
    
    # Delivery info
    min_order_amount = db.Column(db.Numeric(10, 2), default=0.00)
    delivery_fee = db.Column(db.Numeric(10, 2), default=2.99)
    estimated_prep_time = db.Column(db.Integer, default=20)  # minutes
    
    # Ratings
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Images
    logo_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'
    
    def is_open_now(self):
        """Check if restaurant is open now"""
        if not self.is_open:
            return False
        
        now = datetime.now().time()
        return self.opening_time <= now <= self.closing_time

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    item_id = db.Column(db.String(20), primary_key=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    category = db.Column(db.String(50), index=True)
    subcategory = db.Column(db.String(50))
    
    is_available = db.Column(db.Boolean, default=True, index=True)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_spicy = db.Column(db.Boolean, default=False)
    
    preparation_time = db.Column(db.Integer)  # in minutes
    calories = db.Column(db.Integer)
    
    image_url = db.Column(db.String(255))
    tags = db.Column(db.JSON)  # ["popular", "new", "chef_special"]
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = db.relationship('Restaurant', backref='menu_items', lazy=True)
    
    def __repr__(self):
        return f'<MenuItem {self.name} - ${self.price}>'