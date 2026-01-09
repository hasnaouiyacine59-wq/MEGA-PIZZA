# shared/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='employee')
    is_active = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'))
    phone_number = db.Column(db.String(20))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    def __repr__(self):
        return f'<User {self.username}>'


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
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0)
    estimated_prep_time = db.Column(db.Integer)
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_reviews = db.Column(db.Integer, default=0)
    logo_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'


class Customer(db.Model):
    __tablename__ = 'customers'
    
    customer_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Customer {self.name}>'


class Driver(db.Model):
    __tablename__ = 'drivers'
    
    driver_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    license_number = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(20))
    vehicle_model = db.Column(db.String(50))
    license_plate = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)
    current_location = db.Column(db.String(100))
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_deliveries = db.Column(db.Integer, default=0)
    completed_deliveries = db.Column(db.Integer, default=0)
    failed_deliveries = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Numeric(10, 2), default=0.00)
    avg_delivery_time = db.Column(db.Integer)
    shift_start = db.Column(db.Time)
    shift_end = db.Column(db.Time)
    is_on_shift = db.Column(db.Boolean, default=False)
    emergency_contact = db.Column(db.String(50))
    emergency_phone = db.Column(db.String(20))
    license_expiry = db.Column(db.Date)
    insurance_expiry = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='driver_profile', lazy=True)
    
    def __repr__(self):
        return f'<Driver {self.driver_id}>'


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    item_id = db.Column(db.String(20), primary_key=True)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    restaurant = db.relationship('Restaurant', backref='menu_items', lazy=True)
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'


class Address(db.Model):
    __tablename__ = 'addresses'
    
    address_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.customer_id'), nullable=False)
    street = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50), default='USA')
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='addresses', lazy=True)
    
    def __repr__(self):
        return f'<Address {self.street[:20]}...>'


class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.String(30), primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.customer_id'), nullable=False)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    order_status = db.Column(db.String(20), default='pending')
    delivery_type = db.Column(db.String(10))
    special_instructions = db.Column(db.Text)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'))
    driver_rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='orders', lazy=True)
    restaurant = db.relationship('Restaurant', backref='orders', lazy=True)
    address = db.relationship('Address', lazy=True)
    driver = db.relationship('Driver', backref='orders', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.order_id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.String(20), db.ForeignKey('menu_items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    customizations = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order', backref='order_items', lazy=True)
    menu_item = db.relationship('MenuItem', lazy=True)
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(30), db.ForeignKey('orders.order_id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    actor_type = db.Column(db.String(20), default='system')
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'))
    location_lat = db.Column(db.Numeric(10, 8))
    location_lng = db.Column(db.Numeric(11, 8))
    estimated_arrival = db.Column(db.DateTime)
    customer_notified = db.Column(db.Boolean, default=False)
    notification_method = db.Column(db.String(20))
    public_notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    reason_code = db.Column(db.String(50))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    effective_from = db.Column(db.DateTime, default=datetime.utcnow)
    effective_until = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    source = db.Column(db.String(50), default='web')
    time_in_previous_status = db.Column(db.Integer)
    predicted_time_in_status = db.Column(db.Integer)
    
    order = db.relationship('Order', backref='status_history', lazy=True)
    user = db.relationship('User', foreign_keys=[changed_by], lazy=True)
    driver = db.relationship('Driver', lazy=True)
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.history_id} for {self.order_id}>'
