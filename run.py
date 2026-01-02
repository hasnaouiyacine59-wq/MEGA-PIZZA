from flask import Flask, render_template_string, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
from datetime import datetime
from datetime import datetime, time
import time as time_module  # For timestamp generation
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mega-pizza-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mega_pizza_admin:SecurePass123!@localhost:5432/mega_pizza_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
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
    # deliveries = db.relationship('Order', backref='assigned_driver', lazy=True)
    
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


# # class Order(db.Model):
#     __tablename__ = 'orders'
    
#     order_id = db.Column(db.String(30), primary_key=True, default=lambda: f"ORD-{int(time.time()*1000)}")
#     # customer_id = db.Column(db.String(20), db.ForeignKey('customers.customer_id'))
#     restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurants.restaurant_id'))
#     driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'))
#     address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    
#     # Order status
#     order_status = db.Column(db.String(20), default='pending', 
#                             nullable=False, 
#                             index=True,
#                             server_default='pending')
    
#     # Delivery info
#     delivery_type = db.Column(db.String(10), default='delivery')  # delivery or pickup
#     special_instructions = db.Column(db.Text)
    
#     # Pricing
#     subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
#     tax = db.Column(db.Numeric(10, 2), default=0.00)
#     delivery_fee = db.Column(db.Numeric(10, 2), default=0.00)
#     discount = db.Column(db.Numeric(10, 2), default=0.00)
#     total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
#     # Payment
#     payment_method = db.Column(db.String(20))  # cash, card, online
#     payment_status = db.Column(db.String(20), default='pending')
#     transaction_id = db.Column(db.String(100))
    
#     # Timestamps
#     created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
#     estimated_delivery = db.Column(db.DateTime)
#     accepted_at = db.Column(db.DateTime)
#     prepared_at = db.Column(db.DateTime)
#     out_for_delivery_at = db.Column(db.DateTime)
#     delivered_at = db.Column(db.DateTime)
#     cancelled_at = db.Column(db.DateTime)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
#     # Ratings
#     restaurant_rating = db.Column(db.Integer)  # 1-5
#     driver_rating = db.Column(db.Integer)      # 1-5
#     customer_feedback = db.Column(db.Text)
    
#     # Relationships
#     # customer = db.relationship('Customer', backref='orders', lazy=True)
#     # restaurant = db.relationship('Restaurant', backref='orders', lazy=True)
#     driver = db.relationship('Driver', backref='orders', lazy=True)
#     # address = db.relationship('Address', backref='orders', lazy=True)
#     items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
#     status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    
#     def __repr__(self):
#         return f'<Order {self.order_id} - {self.order_status}>'
    
#     def get_status_badge(self):
#         status_colors = {
#             'pending': 'warning',
#             'confirmed': 'info',
#             'preparing': 'primary',
#             'ready': 'success',
#             'out_for_delivery': 'dark',
#             'delivered': 'success',
#             'cancelled': 'danger'
#         }
#         color = status_colors.get(self.order_status, 'secondary')
#         return f'<span class="badge bg-{color}">{self.order_status.replace("_", " ").title()}</span>'
    
#     def calculate_total(self):
#         """Calculate total amount"""
#         return float(self.subtotal) + float(self.tax) + float(self.delivery_fee) - float(self.discount)
    
#     def estimated_time_remaining(self):
#         """Get estimated time remaining for delivery"""
#         if not self.estimated_delivery:
#             return None
#         now = datetime.utcnow()
#         if now > self.estimated_delivery:
#             return "Overdue"
        
#         diff = self.estimated_delivery - now
#         hours, remainder = divmod(diff.seconds, 3600)
#         minutes = remainder // 60
        
#         if hours > 0:
#             return f"{hours}h {minutes}m"
#         return f"{minutes}m"
    
#     def can_be_cancelled(self):
#         """Check if order can be cancelled"""
#         non_cancellable_statuses = ['out_for_delivery', 'delivered', 'cancelled']
#         return self.order_status not in non_cancellable_statuses

class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.String(30), primary_key=True, default=lambda: f"ORD-{int(time_module.time()*1000)}")
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'), index=True)
    
    # Basic order info
    order_status = db.Column(db.String(20), default='pending', nullable=False)
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



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mega Pizza - Best Pizza Delivery</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #ff6b35;
                --secondary-color: #ffa500;
                --dark-color: #1a1a2e;
                --light-color: #f8f9fa;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: white;
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            .hero-section {
                min-height: 100vh;
                display: flex;
                align-items: center;
                position: relative;
                padding: 80px 20px;
            }
            
            .hero-bg {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    radial-gradient(circle at 20% 80%, rgba(255, 107, 53, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 165, 0, 0.1) 0%, transparent 50%);
                z-index: -1;
            }
            
            .container-custom {
                max-width: 1200px;
                margin: 0 auto;
                width: 100%;
            }
            
            .hero-content {
                max-width: 600px;
                animation: fadeInUp 1s ease-out;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .hero-logo {
                font-size: 4rem;
                margin-bottom: 20px;
                animation: bounce 2s infinite;
                display: inline-block;
            }
            
            @keyframes bounce {
                0%, 100% { transform: translateY(0) rotate(0deg); }
                25% { transform: translateY(-10px) rotate(-5deg); }
                75% { transform: translateY(-10px) rotate(5deg); }
            }
            
            .hero-title {
                font-size: 3.5rem;
                font-weight: 800;
                line-height: 1.2;
                margin-bottom: 20px;
                background: linear-gradient(135deg, #ff6b35, #ffa500);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            
            .hero-subtitle {
                font-size: 1.2rem;
                line-height: 1.6;
                margin-bottom: 30px;
                color: rgba(255, 255, 255, 0.8);
                max-width: 500px;
            }
            
            .btn-hero {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 15px 30px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
            }
            
            .btn-hero:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(255, 107, 53, 0.4);
                color: white;
            }
            
            .btn-hero-secondary {
                background: transparent;
                border: 2px solid rgba(255, 255, 255, 0.2);
                margin-left: 15px;
            }
            
            .btn-hero-secondary:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            .features {
                display: flex;
                gap: 30px;
                margin-top: 60px;
                flex-wrap: wrap;
            }
            
            .feature-item {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 25px;
                flex: 1;
                min-width: 250px;
                transition: all 0.3s ease;
            }
            
            .feature-item:hover {
                transform: translateY(-10px);
                background: rgba(255, 255, 255, 0.1);
                border-color: var(--primary-color);
            }
            
            .feature-icon {
                font-size: 2.5rem;
                color: var(--primary-color);
                margin-bottom: 15px;
            }
            
            .feature-title {
                font-size: 1.3rem;
                font-weight: 600;
                margin-bottom: 10px;
            }
            
            .feature-text {
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.95rem;
                line-height: 1.5;
            }
            
            .floating-pizzas {
                position: absolute;
                right: 50px;
                top: 50%;
                transform: translateY(-50%);
                animation: float 6s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(-50%) rotate(0deg); }
                50% { transform: translateY(-55%) rotate(10deg); }
            }
            
            .pizza {
                font-size: 8rem;
                filter: drop-shadow(0 10px 20px rgba(0,0,0,0.3));
            }
            
            @media (max-width: 1200px) {
                .floating-pizzas {
                    position: relative;
                    right: 0;
                    top: 0;
                    transform: none;
                    text-align: center;
                    margin-top: 50px;
                }
                
                .hero-content {
                    text-align: center;
                    margin: 0 auto;
                }
                
                .hero-title {
                    font-size: 2.8rem;
                }
            }
            
            @media (max-width: 768px) {
                .hero-title {
                    font-size: 2.2rem;
                }
                
                .hero-subtitle {
                    font-size: 1rem;
                }
                
                .features {
                    flex-direction: column;
                }
                
                .btn-hero {
                    width: 100%;
                    margin-bottom: 10px;
                    justify-content: center;
                }
                
                .btn-hero-secondary {
                    margin-left: 0;
                }
                
                .pizza {
                    font-size: 5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="hero-section">
            <div class="hero-bg"></div>
            <div class="container-custom">
                <div class="hero-content">
                    <div class="hero-logo">🍕</div>
                    <h1 class="hero-title">Mega Pizza Delivery</h1>
                    <p class="hero-subtitle">
                        Order delicious, freshly baked pizzas delivered straight to your door. 
                        Experience the taste of perfection with our handcrafted recipes and 
                        premium ingredients.
                    </p>
                    
                    <div class="hero-buttons">
                        <a href="/login" class="btn-hero">
                            <i class="fas fa-sign-in-alt"></i> Login to Order
                        </a>
                        <a href="/login" class="btn-hero btn-hero-secondary">
                            <i class="fas fa-user-plus"></i> Create Account
                        </a>
                    </div>
                    
                    <div class="features">
                        <div class="feature-item">
                            <div class="feature-icon">
                                <i class="fas fa-bolt"></i>
                            </div>
                            <h3 class="feature-title">Fast Delivery</h3>
                            <p class="feature-text">Hot pizza delivered in 30 minutes or less</p>
                        </div>
                        
                        <div class="feature-item">
                            <div class="feature-icon">
                                <i class="fas fa-star"></i>
                            </div>
                            <h3 class="feature-title">Premium Quality</h3>
                            <p class="feature-text">Fresh ingredients, handcrafted with love</p>
                        </div>
                        
                        <div class="feature-item">
                            <div class="feature-icon">
                                <i class="fas fa-truck"></i>
                            </div>
                            <h3 class="feature-title">Track Order</h3>
                            <p class="feature-text">Real-time tracking of your delivery</p>
                        </div>
                    </div>
                </div>
                
                <div class="floating-pizzas">
                    <div class="pizza">🍕</div>
                </div>
            </div>
        </div>
        
        <script>
            // Add floating animation to feature items with delay
            document.querySelectorAll('.feature-item').forEach((item, index) => {
                item.style.animationDelay = `${index * 0.2}s`;
            });
            
            // Add scroll effect
            window.addEventListener('scroll', () => {
                const scrolled = window.pageYOffset;
                const hero = document.querySelector('.hero-section');
                hero.style.transform = `translateY(${scrolled * 0.5}px)`;
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password) and user.is_active:
            login_user(user)
            flash('🎉 Login successful! Welcome back!', 'success')
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid username or password', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #ff6b35;
                --secondary-color: #ffa500;
                --dark-color: #1a1a2e;
                --light-color: #f8f9fa;
                --success-color: #28a745;
                --danger-color: #dc3545;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .login-container {
                width: 100%;
                max-width: 450px;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
                animation: slideUp 0.6s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .login-header {
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 40px 30px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .login-header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 30px 30px;
                opacity: 0.1;
            }
            
            .logo {
                font-size: 3rem;
                margin-bottom: 10px;
                animation: bounce 2s infinite;
            }
            
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            .login-header h1 {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 5px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            
            .login-header p {
                font-size: 0.9rem;
                opacity: 0.9;
            }
            
            .login-body {
                padding: 40px 30px;
            }
            
            .form-floating {
                margin-bottom: 20px;
                position: relative;
            }
            
            .form-control {
                border: 2px solid #e1e5eb;
                border-radius: 10px;
                padding: 15px;
                font-size: 1rem;
                transition: all 0.3s ease;
                background: #fff;
            }
            
            .form-control:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.2);
                transform: translateY(-2px);
            }
            
            .form-label {
                color: #666;
                font-weight: 500;
            }
            
            .input-icon {
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                color: #999;
                z-index: 5;
            }
            
            .btn-login {
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                border: none;
                color: white;
                padding: 15px;
                font-size: 1.1rem;
                font-weight: 600;
                border-radius: 10px;
                width: 100%;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            .btn-login:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(255, 107, 53, 0.3);
            }
            
            .btn-login:active {
                transform: translateY(-1px);
            }
            
            .alert {
                border-radius: 10px;
                border: none;
                padding: 15px;
                margin-bottom: 20px;
                animation: fadeIn 0.5s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .alert-success {
                background: linear-gradient(135deg, #d4edda, #c3e6cb);
                color: #155724;
                border-left: 4px solid var(--success-color);
            }
            
            .alert-danger {
                background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                color: #721c24;
                border-left: 4px solid var(--danger-color);
            }
            
            .login-footer {
                text-align: center;
                padding: 20px 30px;
                background: #f8f9fa;
                border-top: 1px solid #e1e5eb;
            }
            
            .demo-credentials {
                background: #e9ecef;
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                border-left: 4px solid var(--primary-color);
            }
            
            .demo-credentials h6 {
                color: var(--dark-color);
                margin-bottom: 10px;
                font-weight: 600;
            }
            
            .demo-credentials p {
                margin-bottom: 5px;
                font-size: 0.9rem;
            }
            
            .demo-credentials code {
                background: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: 600;
                color: var(--primary-color);
            }
            
            .back-home {
                color: var(--primary-color);
                text-decoration: none;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                margin-top: 15px;
                transition: color 0.3s ease;
            }
            
            .back-home:hover {
                color: var(--secondary-color);
            }
            
            .password-toggle {
                position: absolute;
                right: 45px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: #999;
                cursor: pointer;
                z-index: 10;
            }
            
            @media (max-width: 768px) {
                .login-container {
                    max-width: 100%;
                }
                
                .login-header, .login-body {
                    padding: 30px 20px;
                }
                
                .logo {
                    font-size: 2.5rem;
                }
                
                .login-header h1 {
                    font-size: 1.8rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <div class="logo">🍕</div>
                <h1>Mega Pizza</h1>
                <p>Delicious pizza delivered to your door</p>
            </div>
            
            <div class="login-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST" action="/login" id="loginForm">
                    <div class="form-floating">
                        <input type="text" class="form-control" id="username" name="username" 
                               placeholder="Username" required autofocus>
                        <label for="username"><i class="fas fa-user me-2"></i>Username</label>
                        <span class="input-icon">
                            <i class="fas fa-user"></i>
                        </span>
                    </div>
                    
                    <div class="form-floating">
                        <input type="password" class="form-control" id="password" name="password" 
                               placeholder="Password" required>
                        <label for="password"><i class="fas fa-lock me-2"></i>Password</label>
                        <span class="input-icon">
                            <i class="fas fa-lock"></i>
                        </span>
                        <button type="button" class="password-toggle" id="togglePassword">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                    
                    <button type="submit" class="btn-login">
                        <i class="fas fa-sign-in-alt"></i> Sign In
                    </button>
                </form>
                
                <div class="demo-credentials">
                    <h6><i class="fas fa-key me-2"></i>Demo Credentials</h6>
                    <p><strong>Admin:</strong> <code>admin</code> / <code>Admin@123</code></p>
                    <p><small class="text-muted">Try different roles in your app</small></p>
                </div>
            </div>
            
            <div class="login-footer">
                <a href="/" class="back-home">
                    <i class="fas fa-arrow-left"></i> Back to Home
                </a>
            </div>
        </div>
        
        <script>
            // Toggle password visibility
            document.getElementById('togglePassword').addEventListener('click', function() {
                const passwordInput = document.getElementById('password');
                const icon = this.querySelector('i');
                
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
            
            // Form validation and animation
            document.getElementById('loginForm').addEventListener('submit', function(e) {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                if (!username || !password) {
                    e.preventDefault();
                    // Add shake animation to empty fields
                    const inputs = document.querySelectorAll('input[required]');
                    inputs.forEach(input => {
                        if (!input.value) {
                            input.style.animation = 'shake 0.5s';
                            input.addEventListener('animationend', () => {
                                input.style.animation = '';
                            });
                        }
                    });
                }
            });
            
            // Add shake animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-5px); }
                    75% { transform: translateX(5px); }
                }
            `;
            document.head.appendChild(style);
            
            // Focus effect
            const inputs = document.querySelectorAll('.form-control');
            inputs.forEach(input => {
                input.addEventListener('focus', function() {
                    this.parentElement.classList.add('focused');
                });
                
                input.addEventListener('blur', function() {
                    if (!this.value) {
                        this.parentElement.classList.remove('focused');
                    }
                });
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{
                --primary-color: #ff6b35;
                --secondary-color: #ffa500;
                --dark-color: #1a1a2e;
            }}
            
            body {{
                font-family: 'Poppins', sans-serif;
                background: #f8f9fa;
            }}
            
            .navbar {{
                background: var(--dark-color) !important;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}
            
            .dashboard-container {{
                padding: 30px;
            }}
            
            .welcome-card {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🍕 Mega Pizza</a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text me-3">{current_user.username} ({current_user.role})</span>
                    <a class="nav-link" href="/logout">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="dashboard-container">
            <div class="welcome-card">
                <h1>Welcome, {current_user.username}!</h1>
                <p class="lead">You are logged in as a {current_user.role}.</p>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-history"></i> Order History</h5>
                            <p>View your past orders and receipts</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-shopping-cart"></i> New Order</h5>
                            <p>Place a new pizza order</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-user"></i> Profile</h5>
                            <p>Update your account information</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    # Get stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admins = User.query.filter_by(role='admin').count()
    drivers = User.query.filter_by(role='driver').count()
    customers = User.query.filter_by(role='user').count()
    restaurants_count = 0  # You can add Restaurant model count
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #ff6b35;
                --secondary-color: #ffa500;
                --dark-color: #1a1a2e;
                --sidebar-width: 250px;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Poppins', sans-serif;
                background: #f8f9fa;
                overflow-x: hidden;
            }}
            
            /* Top Navbar */
            .navbar-admin {{
                background: var(--dark-color) !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                height: 60px;
                position: fixed;
                top: 0;
                right: 0;
                left: 0;
                z-index: 1030;
            }}
            
            .navbar-brand {{
                color: white !important;
                font-weight: 700;
                font-size: 1.5rem;
            }}
            
            /* Sidebar */
            .sidebar {{
                width: var(--sidebar-width);
                background: white;
                height: calc(100vh - 60px);
                position: fixed;
                top: 60px;
                left: 0;
                overflow-y: auto;
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                z-index: 1020;
            }}
            
            .sidebar-header {{
                padding: 20px;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                text-align: center;
            }}
            
            .sidebar-header h5 {{
                margin: 0;
                font-weight: 600;
            }}
            
            .sidebar-menu {{
                padding: 20px 0;
            }}
            
            .menu-item {{
                display: flex;
                align-items: center;
                padding: 12px 20px;
                color: #333;
                text-decoration: none;
                transition: all 0.3s ease;
                border-left: 3px solid transparent;
            }}
            
            .menu-item:hover {{
                background: rgba(255, 107, 53, 0.1);
                color: var(--primary-color);
                border-left: 3px solid var(--primary-color);
            }}
            
            .menu-item.active {{
                background: rgba(255, 107, 53, 0.1);
                color: var(--primary-color);
                border-left: 3px solid var(--primary-color);
                font-weight: 600;
            }}
            
            .menu-icon {{
                width: 30px;
                font-size: 1.1rem;
            }}
            
            .menu-text {{
                flex: 1;
            }}
            
            .menu-badge {{
                background: var(--primary-color);
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.8rem;
            }}
            
            .menu-divider {{
                margin: 15px 20px;
                border-top: 1px solid #e1e5eb;
            }}
            
            .menu-section {{
                padding: 10px 20px;
                color: #6c757d;
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            /* Main Content */
            .main-content {{
                margin-left: var(--sidebar-width);
                margin-top: 60px;
                padding: 30px;
                transition: all 0.3s ease;
            }}
            
            @media (max-width: 768px) {{
                .sidebar {{
                    transform: translateX(-100%);
                }}
                
                .sidebar.active {{
                    transform: translateX(0);
                }}
                
                .main-content {{
                    margin-left: 0;
                }}
            }}
            
            /* Dashboard Cards */
            .welcome-card {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
            }}
            
            .stat-card {{
                border-radius: 15px;
                border: none;
                color: white;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }}
            
            .stat-card::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 30px 30px;
                opacity: 0.1;
                pointer-events: none;
            }}
            
            .stat-icon {{
                font-size: 2.5rem;
                margin-bottom: 15px;
                opacity: 0.9;
            }}
            
            .stat-number {{
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            
            .stat-label {{
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            
            /* Quick Action Buttons */
            .quick-action-btn {{
                display: flex;
                align-items: center;
                gap: 10px;
                background: white;
                border: 2px solid #e1e5eb;
                border-radius: 10px;
                padding: 15px;
                width: 100%;
                text-align: left;
                transition: all 0.3s ease;
                color: #333;
                text-decoration: none;
            }}
            
            .quick-action-btn:hover {{
                border-color: var(--primary-color);
                background: rgba(255, 107, 53, 0.05);
                color: var(--primary-color);
                transform: translateY(-3px);
            }}
            
            .quick-action-icon {{
                width: 40px;
                height: 40px;
                background: rgba(255, 107, 53, 0.1);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--primary-color);
                font-size: 1.2rem;
            }}
            
            /* Recent Activity */
            .activity-item {{
                display: flex;
                align-items: center;
                padding: 15px;
                border-bottom: 1px solid #e1e5eb;
                transition: all 0.3s ease;
            }}
            
            .activity-item:hover {{
                background: rgba(255, 107, 53, 0.05);
            }}
            
            .activity-icon {{
                width: 40px;
                height: 40px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                color: white;
            }}
            
            .activity-content {{
                flex: 1;
            }}
            
            .activity-time {{
                color: #6c757d;
                font-size: 0.85rem;
            }}
            
            /* Toggle Button for Mobile */
            .sidebar-toggle {{
                display: none;
                background: none;
                border: none;
                color: white;
                font-size: 1.5rem;
            }}
            
            @media (max-width: 768px) {{
                .sidebar-toggle {{
                    display: block;
                }}
            }}
        </style>
    </head>
    <body>
        <!-- Top Navbar -->
        <nav class="navbar navbar-admin navbar-expand-lg">
            <div class="container-fluid">
                <button class="sidebar-toggle" id="sidebarToggle">
                    <i class="fas fa-bars"></i>
                </button>
                
                <a class="navbar-brand" href="/">
                    <i class="fas fa-pizza-slice me-2"></i>Mega Pizza Admin
                </a>
                
                <div class="navbar-nav ms-auto">
                    <div class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle me-1"></i> {current_user.username}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#"><i class="fas fa-user me-2"></i>Profile</a></li>
                            <li><a class="dropdown-item" href="#"><i class="fas fa-cog me-2"></i>Settings</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h5><i class="fas fa-user-shield me-2"></i>Admin Panel</h5>
                <small>Full Control Dashboard</small>
            </div>
            
            <div class="sidebar-menu">
                <div class="menu-section">MAIN</div>
                <a href="/admin/dashboard" class="menu-item active">
                    <div class="menu-icon"><i class="fas fa-tachometer-alt"></i></div>
                    <div class="menu-text">Dashboard</div>
                </a>
                
                <div class="menu-section">MANAGEMENT</div>
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-users"></i></div>
                    <div class="menu-text">Users</div>
                    <div class="menu-badge">{total_users}</div>
                </a>
                
                <a href="/admin/drivers" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-truck"></i></div>
                    <div class="menu-text">Drivers</div>
                    <div class="menu-badge">{drivers}</div>
                </a>
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-store"></i></div>
                    <div class="menu-text">Restaurants</div>
                    <div class="menu-badge">{restaurants_count}</div>
                </a>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-shopping-cart"></i></div>
                    <div class="menu-text">Orders</div>
                    <div class="menu-badge">0</div>
                </a>
                
                <div class="menu-section">CONTENT</div>
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-pizza-slice"></i></div>
                    <div class="menu-text">Menu Items</div>
                </a>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-tags"></i></div>
                    <div class="menu-text">Categories</div>
                </a>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-star"></i></div>
                    <div class="menu-text">Reviews</div>
                </a>
                
                <div class="menu-section">REPORTS</div>
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-chart-bar"></i></div>
                    <div class="menu-text">Analytics</div>
                </a>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-file-invoice-dollar"></i></div>
                    <div class="menu-text">Revenue</div>
                </a>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-chart-line"></i></div>
                    <div class="menu-text">Sales Report</div>
                </a>
                
                <div class="menu-divider"></div>
                
                <a href="#" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-cog"></i></div>
                    <div class="menu-text">Settings</div>
                </a>
                
                <a href="/" class="menu-item">
                    <div class="menu-icon"><i class="fas fa-home"></i></div>
                    <div class="menu-text">View Site</div>
                </a>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content" id="mainContent">
            <!-- Welcome Card -->
            <div class="welcome-card">
                <h1>Welcome, {current_user.username}!</h1>
                <p class="lead">Administrator Dashboard - Manage everything from here</p>
                <div class="mt-3">
                    <span class="badge bg-light text-dark me-2"><i class="fas fa-clock me-1"></i> {datetime.now().strftime("%Y-%m-%d %H:%M")}</span>
                    <span class="badge bg-light text-dark"><i class="fas fa-database me-1"></i> PostgreSQL Connected</span>
                </div>
            </div>

            <!-- Statistics Cards -->
            <div class="row">
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="stat-card" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                        <div class="stat-icon"><i class="fas fa-users"></i></div>
                        <div class="stat-number">{total_users}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                </div>
                
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="stat-card" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <div class="stat-icon"><i class="fas fa-user-check"></i></div>
                        <div class="stat-number">{active_users}</div>
                        <div class="stat-label">Active Users</div>
                    </div>
                </div>
                
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="stat-card" style="background: linear-gradient(135deg, #17a2b8, #0dcaf0);">
                        <div class="stat-icon"><i class="fas fa-user-shield"></i></div>
                        <div class="stat-number">{admins}</div>
                        <div class="stat-label">Administrators</div>
                    </div>
                </div>
                
                <div class="col-xl-3 col-md-6 mb-4">
                    <div class="stat-card" style="background: linear-gradient(135deg, #ffc107, #fd7e14);">
                        <div class="stat-icon"><i class="fas fa-truck"></i></div>
                        <div class="stat-number">{drivers}</div>
                        <div class="stat-label">Delivery Drivers</div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions & Recent Activity -->
            <div class="row">
                <!-- Quick Actions -->
                <div class="col-lg-6 mb-4">
                    <div class="card">
                        <div class="card-header bg-white">
                            <h5 class="mb-0"><i class="fas fa-bolt me-2"></i>Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-user-plus"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">Add New User</h6>
                                            <small class="text-muted">Create customer account</small>
                                        </div>
                                    </a>
                                </div>
                                
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-truck"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">Add Driver</h6>
                                            <small class="text-muted">Register delivery driver</small>
                                        </div>
                                    </a>
                                </div>
                                
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-store"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">Add Restaurant</h6>
                                            <small class="text-muted">Register new restaurant</small>
                                        </div>
                                    </a>
                                </div>
                                
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-pizza-slice"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">Add Menu Item</h6>
                                            <small class="text-muted">Create new food item</small>
                                        </div>
                                    </a>
                                </div>
                                
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-chart-bar"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">View Reports</h6>
                                            <small class="text-muted">Sales & analytics</small>
                                        </div>
                                    </a>
                                </div>
                                
                                <div class="col-md-6">
                                    <a href="#" class="quick-action-btn">
                                        <div class="quick-action-icon">
                                            <i class="fas fa-cog"></i>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">System Settings</h6>
                                            <small class="text-muted">Configure application</small>
                                        </div>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="col-lg-6 mb-4">
                    <div class="card">
                        <div class="card-header bg-white">
                            <h5 class="mb-0"><i class="fas fa-history me-2"></i>Recent Activity</h5>
                        </div>
                        <div class="card-body p-0">
                            <div class="activity-item">
                                <div class="activity-icon" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                                    <i class="fas fa-user-plus"></i>
                                </div>
                                <div class="activity-content">
                                    <strong>New user registered</strong>
                                    <p class="mb-0 text-muted">John Doe signed up as customer</p>
                                </div>
                                <div class="activity-time">5 min ago</div>
                            </div>
                            
                            <div class="activity-item">
                                <div class="activity-icon" style="background: linear-gradient(135deg, #28a745, #20c997);">
                                    <i class="fas fa-shopping-cart"></i>
                                </div>
                                <div class="activity-content">
                                    <strong>New order placed</strong>
                                    <p class="mb-0 text-muted">Order #ORD-001 for $25.99</p>
                                </div>
                                <div class="activity-time">15 min ago</div>
                            </div>
                            
                            <div class="activity-item">
                                <div class="activity-icon" style="background: linear-gradient(135deg, #ff6b35, #ffa500);">
                                    <i class="fas fa-truck"></i>
                                </div>
                                <div class="activity-content">
                                    <strong>Driver assigned</strong>
                                    <p class="mb-0 text-muted">Mike assigned to order #ORD-001</p>
                                </div>
                                <div class="activity-time">30 min ago</div>
                            </div>
                            
                            <div class="activity-item">
                                <div class="activity-icon" style="background: linear-gradient(135deg, #17a2b8, #0dcaf0);">
                                    <i class="fas fa-check-circle"></i>
                                </div>
                                <div class="activity-content">
                                    <strong>Order delivered</strong>
                                    <p class="mb-0 text-muted">Order #ORD-000 delivered successfully</p>
                                </div>
                                <div class="activity-time">1 hour ago</div>
                            </div>
                            
                            <div class="activity-item">
                                <div class="activity-icon" style="background: linear-gradient(135deg, #6f42c1, #d63384);">
                                    <i class="fas fa-star"></i>
                                </div>
                                <div class="activity-content">
                                    <strong>New review added</strong>
                                    <p class="mb-0 text-muted">Sarah rated 5 stars for Pepperoni Pizza</p>
                                </div>
                                <div class="activity-time">2 hours ago</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Status -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-white">
                            <h5 class="mb-0"><i class="fas fa-server me-2"></i>System Status</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3 text-center mb-3">
                                    <div class="p-3 rounded" style="background: rgba(40, 167, 69, 0.1);">
                                        <i class="fas fa-database fa-2x text-success mb-2"></i>
                                        <h6>Database</h6>
                                        <span class="badge bg-success">Online</span>
                                    </div>
                                </div>
                                
                                <div class="col-md-3 text-center mb-3">
                                    <div class="p-3 rounded" style="background: rgba(40, 167, 69, 0.1);">
                                        <i class="fas fa-server fa-2x text-success mb-2"></i>
                                        <h6>API Service</h6>
                                        <span class="badge bg-success">Running</span>
                                    </div>
                                </div>
                                
                                <div class="col-md-3 text-center mb-3">
                                    <div class="p-3 rounded" style="background: rgba(255, 193, 7, 0.1);">
                                        <i class="fas fa-envelope fa-2x text-warning mb-2"></i>
                                        <h6>Email Service</h6>
                                        <span class="badge bg-warning">Setup Required</span>
                                    </div>
                                </div>
                                
                                <div class="col-md-3 text-center mb-3">
                                    <div class="p-3 rounded" style="background: rgba(40, 167, 69, 0.1);">
                                        <i class="fas fa-shield-alt fa-2x text-success mb-2"></i>
                                        <h6>Security</h6>
                                        <span class="badge bg-success">Protected</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Sidebar toggle for mobile
            document.getElementById('sidebarToggle').addEventListener('click', function() {{
                document.getElementById('sidebar').classList.toggle('active');
            }});
            
            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', function(event) {{
                const sidebar = document.getElementById('sidebar');
                const toggleBtn = document.getElementById('sidebarToggle');
                
                if (window.innerWidth <= 768) {{
                    if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {{
                        sidebar.classList.remove('active');
                    }}
                }}
            }});
            
            // Auto-update time every minute
            function updateTime() {{
                const now = new Date();
                const timeElement = document.querySelector('.badge.bg-light.text-dark i.fa-clock').parentElement;
                timeElement.innerHTML = `<i class="fas fa-clock me-1"></i> ${{now.getFullYear()}}-${{(now.getMonth()+1).toString().padStart(2, '0')}}-${{now.getDate().toString().padStart(2, '0')}} ${{now.getHours().toString().padStart(2, '0')}}:${{now.getMinutes().toString().padStart(2, '0')}}`;
            }}
            
            setInterval(updateTime, 60000);
            
            // Add animation to stat cards on load
            document.addEventListener('DOMContentLoaded', function() {{
                const statCards = document.querySelectorAll('.stat-card');
                statCards.forEach((card, index) => {{
                    card.style.animationDelay = `${{index * 0.1}}s`;
                    card.style.animation = 'slideUp 0.5s ease-out';
                }});
                
                // Add keyframes for slideUp
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes slideUp {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                `;
                document.head.appendChild(style);
            }});
        </script>
    </body>
    </html>
    ''')

@app.route('/create-admin')
def create_admin():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        admin.password = 'Admin@123'
        db.session.commit()
        message = '''
        <div class="container mt-5">
            <div class="alert alert-success">
                ✅ Admin password updated!<br>
                Username: admin<br>
                Password: Admin@123
            </div>
            <a href="/login" class="btn btn-primary">Go to Login</a>
        </div>
        '''
    else:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@megapizza.com',
            role='admin',
            is_active=True
        )
        admin.password = 'Admin@123'
        db.session.add(admin)
        db.session.commit()
        
        message = '''
        <div class="container mt-5">
            <div class="alert alert-success">
                ✅ Admin user created successfully!<br>
                Username: admin<br>
                Password: Admin@123
            </div>
            <a href="/login" class="btn btn-primary">Go to Login</a>
        </div>
        '''
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Admin - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        {message}
    </body>
    </html>
    ''')

# ============================================
# DRIVER MANAGEMENT ROUTES
# ============================================
@app.route('/admin/drivers')
@login_required
def manage_drivers():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    # Get all drivers with their user info
    drivers = Driver.query.join(User).all()
    
    # Statistics
    total_drivers = len(drivers)
    available_drivers = len([d for d in drivers if d.is_available])
    on_duty_drivers = len([d for d in drivers if d.is_on_shift])
    
    # Build HTML
    driver_cards_html = ""
    if drivers:
        for driver in drivers:
            user = driver.user
            status_badge = driver.get_status_badge()
            rating_stars = driver.calculate_rating_stars()
            
            driver_cards_html += f'''
            <div class="col-xl-3 col-lg-4 col-md-6">
                <div class="driver-card">
                    <div class="driver-header">
                        {status_badge}
                        <div class="driver-avatar">
                            <i class="fas fa-truck"></i>
                        </div>
                        <h5 class="text-center mb-1">{user.username}</h5>
                        <p class="text-center mb-2" style="opacity: 0.9;">
                            <i class="fas fa-car me-1"></i>{driver.vehicle_type or "No vehicle"}
                        </p>
                        <div class="driver-rating text-center">
                            {rating_stars}
                            <span style="color: white; margin-left: 5px;">{driver.rating:.1f}</span>
                        </div>
                    </div>
                    
                    <div class="driver-info p-3">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">License:</small>
                                <p class="mb-2"><strong>{driver.license_number or "N/A"}</strong></p>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Vehicle:</small>
                                <p class="mb-2"><strong>{driver.license_plate or "N/A"}</strong></p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="driver-stats">
                        <div class="stat-item">
                            <div class="stat-value">{driver.total_deliveries}</div>
                            <div class="stat-label">Total</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{driver.completed_deliveries}</div>
                            <div class="stat-label">Completed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${driver.total_earnings:.0f}</div>
                            <div class="stat-label">Earnings</div>
                        </div>
                    </div>
                    
                    <div class="action-buttons">
                        <button class="btn-action btn-view" onclick="viewDriver({driver.driver_id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn-action btn-edit" onclick="editDriver({driver.driver_id})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn-action btn-toggle" onclick="toggleAvailability({driver.driver_id}, {str(driver.is_available).lower()})">
                            <i class="fas fa-power-off"></i> {"Make Busy" if driver.is_available else "Make Available"}
                        </button>
                    </div>
                </div>
            </div>
            '''
    else:
        driver_cards_html = '''
        <div class="col-12">
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-truck"></i>
                </div>
                <h4>No Drivers Registered</h4>
                <p>Register your first delivery driver to start accepting orders.</p>
                <a href="/admin/drivers/register" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Register First Driver
                </a>
            </div>
        </div>
        '''
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Drivers - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{
                --primary-color: #ff6b35;
                --secondary-color: #ffa500;
            }}
            
            .driver-card {{
                background: white;
                border-radius: 15px;
                border: none;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
                overflow: hidden;
                margin-bottom: 20px;
            }}
            
            .driver-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.12);
            }}
            
            .driver-header {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 20px;
                position: relative;
            }}
            
            .driver-header .badge {{
                position: absolute;
                top: 15px;
                right: 15px;
            }}
            
            .driver-avatar {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                color: var(--primary-color);
                margin: 0 auto 15px;
                border: 4px solid white;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            
            .driver-info {{
                background: #f8f9fa;
                border-top: 1px solid #e1e5eb;
                border-bottom: 1px solid #e1e5eb;
            }}
            
            .driver-stats {{
                display: flex;
                justify-content: space-around;
                padding: 15px;
            }}
            
            .stat-item {{
                text-align: center;
            }}
            
            .stat-value {{
                font-size: 1.2rem;
                font-weight: 600;
                color: var(--dark-color);
            }}
            
            .stat-label {{
                font-size: 0.8rem;
                color: #6c757d;
            }}
            
            .action-buttons {{
                padding: 15px;
                display: flex;
                gap: 10px;
            }}
            
            .btn-action {{
                flex: 1;
                padding: 8px;
                border-radius: 8px;
                border: none;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }}
            
            .btn-view {{ background: rgba(13, 110, 253, 0.1); color: #0d6efd; }}
            .btn-view:hover {{ background: #0d6efd; color: white; }}
            
            .btn-edit {{ background: rgba(25, 135, 84, 0.1); color: #198754; }}
            .btn-edit:hover {{ background: #198754; color: white; }}
            
            .btn-toggle {{ background: rgba(255, 193, 7, 0.1); color: #ffc107; }}
            .btn-toggle:hover {{ background: #ffc107; color: white; }}
            
            .empty-state {{
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
            }}
            
            .empty-state-icon {{
                font-size: 4rem;
                color: #dee2e6;
                margin-bottom: 20px;
            }}
            
            .add-driver-btn {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                border: none;
                box-shadow: 0 5px 20px rgba(255, 107, 53, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                transition: all 0.3s ease;
                z-index: 1000;
            }}
            
            .add-driver-btn:hover {{
                transform: scale(1.1);
                box-shadow: 0 8px 25px rgba(255, 107, 53, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="container-fluid mt-4">
            <nav class="navbar navbar-dark bg-dark rounded mb-4">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/admin/dashboard">
                        <i class="fas fa-arrow-left me-2"></i>Driver Management
                    </a>
                    <div class="navbar-text text-white">
                        <i class="fas fa-user-circle me-1"></i> {current_user.username}
                    </div>
                </div>
            </nav>
            
            <!-- Statistics -->
            <div class="row mb-4">
                <div class="col-xl-3 col-md-6 mb-3">
                    <div class="card text-white" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                        <div class="card-body">
                            <h6 class="card-title">Total Drivers</h6>
                            <h2 class="mb-0">{total_drivers}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-3">
                    <div class="card text-white" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <div class="card-body">
                            <h6 class="card-title">Available Now</h6>
                            <h2 class="mb-0">{available_drivers}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-3">
                    <div class="card text-white" style="background: linear-gradient(135deg, #ff6b35, #ffa500);">
                        <div class="card-body">
                            <h6 class="card-title">On Duty</h6>
                            <h2 class="mb-0">{on_duty_drivers}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6 mb-3">
                    <div class="card text-white" style="background: linear-gradient(135deg, #17a2b8, #0dcaf0);">
                        <div class="card-body">
                            <h6 class="card-title">Avg Rating</h6>
                            <h2 class="mb-0">
                                {sum(d.rating for d in drivers)/len(drivers):.1f if drivers else 0.0} 
                                <small>/5</small>
                            </h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Drivers Grid -->
            <div class="row">
                {driver_cards_html}
            </div>
        </div>
        
        <!-- Add Driver Floating Button -->
        <button class="add-driver-btn" onclick="location.href='/admin/drivers/register'">
            <i class="fas fa-plus"></i>
        </button>
        
        <script>
            function viewDriver(driverId) {{
                window.location.href = `/admin/drivers/${{driverId}}`;
            }}
            
            function editDriver(driverId) {{
                window.location.href = `/admin/drivers/${{driverId}}/edit`;
            }}
            
            function toggleAvailability(driverId, isAvailable) {{
                fetch(`/admin/drivers/${{driverId}}/toggle-availability`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{is_available: !isAvailable}})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        location.reload();
                    }} else {{
                        alert(data.message);
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    ''')
# ============================================
@app.route('/admin/drivers/register', methods=['GET', 'POST'])
@login_required
def register_driver():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Create User account first
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Check if user exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
        else:
            # Create User
            user = User(
                username=username,
                email=email,
                phone_number=phone,
                role='driver',
                is_active=True
            )
            user.password = password
            db.session.add(user)
            db.session.flush()  # Get user_id
            
            # Create Driver profile
            driver = Driver(
                user_id=user.user_id,
                license_number=request.form.get('license_number'),
                vehicle_type=request.form.get('vehicle_type'),
                vehicle_model=request.form.get('vehicle_model'),
                license_plate=request.form.get('license_plate'),
                emergency_contact=request.form.get('emergency_contact'),
                emergency_phone=request.form.get('emergency_phone')
            )
            db.session.add(driver)
            db.session.commit()
            
            flash(f'Driver {username} registered successfully!', 'success')
            return redirect(url_for('manage_drivers'))
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register Driver - Mega Pizza</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="mb-4"><i class="fas fa-truck me-2"></i>Register New Driver</h2>
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <h5 class="card-title mb-3">Account Information</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label>Username *</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label>Email *</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label>Phone *</label>
                                <input type="tel" class="form-control" name="phone" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label>Password *</label>
                                <input type="password" class="form-control" name="password" required minlength="8">
                            </div>
                        </div>
                        
                        <h5 class="card-title mb-3 mt-4">Driver Information</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label>License Number *</label>
                                <input type="text" class="form-control" name="license_number" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label>Vehicle Type *</label>
                                <select class="form-control" name="vehicle_type" required>
                                    <option value="">Select Vehicle</option>
                                    <option value="motorcycle">Motorcycle</option>
                                    <option value="car">Car</option>
                                    <option value="bicycle">Bicycle</option>
                                    <option value="scooter">Scooter</option>
                                </select>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label>Vehicle Model</label>
                                <input type="text" class="form-control" name="vehicle_model">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label>License Plate</label>
                                <input type="text" class="form-control" name="license_plate">
                            </div>
                        </div>
                        
                        <h5 class="card-title mb-3 mt-4">Emergency Contact</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label>Emergency Contact Name</label>
                                <input type="text" class="form-control" name="emergency_contact">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label>Emergency Phone</label>
                                <input type="tel" class="form-control" name="emergency_phone">
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Register Driver
                            </button>
                            <a href="/admin/drivers" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
# ============================================

@app.route('/admin/drivers/add', methods=['GET', 'POST'])
@login_required
def add_driver():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
        else:
            # Create new driver
            driver = User(
                username=username,
                email=email,
                phone_number=phone,
                role='driver',
                is_active=True
            )
            driver.password = password
            
            db.session.add(driver)
            db.session.commit()
            
            flash(f'Driver {username} added successfully!', 'success')
            return redirect(url_for('manage_drivers'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Driver - Mega Pizza Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary-color: #ff6b35;
            }
            
            .form-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 30px;
            }
            
            .form-header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .form-icon {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, var(--primary-color), #ffa500);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                color: white;
                font-size: 2rem;
            }
            
            .form-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                padding: 30px;
            }
        </style>
    </head>
    <body style="background: #f8f9fa;">
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/admin/drivers">
                    <i class="fas fa-arrow-left me-2"></i>Add New Driver
                </a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="form-container">
                <div class="form-header">
                    <div class="form-icon">
                        <i class="fas fa-truck"></i>
                    </div>
                    <h2>Add Delivery Driver</h2>
                    <p class="text-muted">Register a new driver for pizza delivery</p>
                </div>
                
                <div class="form-card">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Username *</label>
                                <input type="text" class="form-control" name="username" required 
                                       placeholder="driver_username">
                                <small class="text-muted">Unique identifier for login</small>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email *</label>
                                <input type="email" class="form-control" name="email" required 
                                       placeholder="driver@email.com">
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone Number *</label>
                                <input type="tel" class="form-control" name="phone" required 
                                       placeholder="+1234567890">
                                <small class="text-muted">For delivery coordination</small>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Password *</label>
                                <input type="password" class="form-control" name="password" required 
                                       placeholder="••••••••" minlength="8">
                                <small class="text-muted">At least 8 characters</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Vehicle Type</label>
                            <select class="form-control" name="vehicle">
                                <option value="motorcycle">Motorcycle</option>
                                <option value="car">Car</option>
                                <option value="bicycle">Bicycle</option>
                                <option value="scooter">Scooter</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">License Plate</label>
                            <input type="text" class="form-control" name="license_plate" 
                                   placeholder="ABC-123">
                        </div>
                        
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-primary btn-lg">
                                <i class="fas fa-save me-2"></i>Add Driver
                            </button>
                            <a href="/admin/drivers" class="btn btn-outline-secondary">
                                Cancel
                            </a>
                        </div>
                    </form>
                </div>
                
                <div class="mt-4 text-center text-muted">
                    <small>
                        <i class="fas fa-info-circle me-1"></i>
                        Driver will receive login credentials via email (if configured)
                    </small>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')


@app.route('/admin/drivers/<int:driver_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_driver(driver_id):
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    driver = User.query.get_or_404(driver_id)
    
    if request.method == 'POST':
        driver.username = request.form.get('username')
        driver.email = request.form.get('email')
        driver.phone_number = request.form.get('phone')
        
        # Only update password if provided
        new_password = request.form.get('password')
        if new_password:
            driver.password = new_password
        
        db.session.commit()
        flash(f'Driver {driver.username} updated successfully!', 'success')
        return redirect(url_for('manage_drivers'))
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Driver - Mega Pizza Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{
                --primary-color: #ff6b35;
            }}
            
            .driver-avatar-large {{
                width: 120px;
                height: 120px;
                background: linear-gradient(135deg, var(--primary-color), #ffa500);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
                color: white;
                font-size: 3rem;
                border: 5px solid white;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body style="background: #f8f9fa;">
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/admin/drivers">
                    <i class="fas fa-arrow-left me-2"></i>Edit Driver
                </a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card shadow">
                        <div class="card-body p-5">
                            <div class="text-center mb-4">
                                <div class="driver-avatar-large">
                                    <i class="fas fa-truck"></i>
                                </div>
                                <h3>Edit Driver: {driver.username}</h3>
                                <p class="text-muted">Update driver information</p>
                            </div>
                            
                            <form method="POST">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Username</label>
                                        <input type="text" class="form-control" name="username" 
                                               value="{driver.username}" required>
                                    </div>
                                    
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Email</label>
                                        <input type="email" class="form-control" name="email" 
                                               value="{driver.email}" required>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone" 
                                           value="{driver.phone_number or ''}" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">New Password (leave blank to keep current)</label>
                                    <input type="password" class="form-control" name="password" 
                                           placeholder="Enter new password only if changing">
                                    <small class="text-muted">Minimum 8 characters</small>
                                </div>
                                
                                <div class="mb-4">
                                    <label class="form-label">Status</label>
                                    <div>
                                        <div class="form-check form-check-inline">
                                            <input class="form-check-input" type="radio" name="status" 
                                                   id="active" value="active" {'checked' if driver.is_active else ''}>
                                            <label class="form-check-label" for="active">
                                                <span class="badge bg-success">Active</span>
                                            </label>
                                        </div>
                                        <div class="form-check form-check-inline">
                                            <input class="form-check-input" type="radio" name="status" 
                                                   id="inactive" value="inactive" {'checked' if not driver.is_active else ''}>
                                            <label class="form-check-label" for="inactive">
                                                <span class="badge bg-danger">Inactive</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-save me-2"></i>Update Driver
                                    </button>
                                    <a href="/admin/drivers" class="btn btn-outline-secondary">
                                        Cancel
                                    </a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')



@app.route('/admin/drivers/<int:driver_id>/toggle', methods=['POST'])
@login_required
def toggle_driver_status(driver_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    driver = User.query.get_or_404(driver_id)
    
    if driver.role != 'driver':
        return jsonify({'success': False, 'message': 'User is not a driver'}), 400
    
    driver.is_active = not driver.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Driver {"activated" if driver.is_active else "deactivated"}',
        'is_active': driver.is_active
    })


@app.route('/admin/drivers/<int:driver_id>/delete', methods=['POST'])
@login_required
def delete_driver(driver_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    driver = User.query.get_or_404(driver_id)
    
    if driver.role != 'driver':
        return jsonify({'success': False, 'message': 'User is not a driver'}), 400
    
    # Prevent deleting yourself
    if driver.user_id == current_user.user_id:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    db.session.delete(driver)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Driver deleted successfully'
    })


@app.route('/admin/drivers/stats')
@login_required
def driver_statistics():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('login'))
    
    drivers = User.query.filter_by(role='driver').all()
    
    # Calculate statistics (example - implement your own)
    stats = {
        'total_drivers': len(drivers),
        'active_drivers': len([d for d in drivers if d.is_active]),
        'total_deliveries': 0,  # Implement from your Order model
        'avg_delivery_time': '25 min',
        'top_driver': drivers[0].username if drivers else 'None',
        'driver_ratings': [
            {'name': d.username, 'rating': 4.5} for d in drivers
        ]
    }
    
    return render_template_string(f'''
    <!-- Driver statistics page with charts -->
    <!-- Implement with Chart.js or similar -->
    ''')


@app.route('/admin/restaurants')
@login_required
def manage_restaurants():
    # Manage pizza restaurants
    pass



@app.route('/admin/orders')
@login_required
def manage_orders():
    # View and manage customer orders
    pass


@app.route('/admin/menu')
@login_required
def manage_menu():
    # Add/edit pizza menu items
    pass

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("⚠️  No admin user found. Visit /create-admin to create one.")
        else:
            print("✅ Admin user exists in database")
    
    app.run(host='0.0.0.0', port=5000, debug=True)