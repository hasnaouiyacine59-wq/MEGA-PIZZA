"""
Mega Pizza Delivery System - REST API
Production-ready API with authentication, order management, and live tracking
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, 
    create_refresh_token, get_jwt_identity, get_jwt,
    verify_jwt_in_request, get_jwt_header
)
from functools import wraps
import logging
from datetime import datetime, timedelta
from app import db, bcrypt
from app.models import User, Customer, Restaurant, MenuItem, Order, Driver, OrderItem, Address
import json
from sqlalchemy import text
from decimal import Decimal
import uuid

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS & DECORATORS
# ============================================

def role_required(roles):
    """Decorator to require specific user roles"""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user:
                return jsonify({"error": "User not found"}), 404
            
            if current_user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def validate_request_data(required_fields):
    """Decorator to validate request data"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    "error": "Missing required fields",
                    "missing_fields": missing_fields
                }), 400
            
            return fn(data, *args, **kwargs)
        return decorator
    return wrapper

def json_response(data=None, message="", status=200):
    """Standard JSON response format"""
    response = {
        "success": status < 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    return jsonify(response), status

def log_api_call():
    """Log API calls for monitoring"""
    if hasattr(g, 'user_id'):
        logger.info(f"API Call - User: {g.user_id}, Path: {request.path}, Method: {request.method}")

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return json_response(message="Username and password required", status=400)
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
            return json_response(message="Invalid credentials", status=401)
        
        if not user.is_active:
            return json_response(message="Account is disabled", status=403)
        
        # Update last login
        user.last_login = datetime.now()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                "role": user.role,
                "username": user.username,
                "restaurant_id": user.restaurant_id
            },
            expires_delta=timedelta(hours=24)
        )
        
        refresh_token = create_refresh_token(identity=str(user.user_id))
        
        return json_response({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "restaurant_id": user.restaurant_id
            }
        }, "Login successful")
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return json_response(message="User not found", status=404)
        
        new_access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                "role": user.role,
                "username": user.username,
                "restaurant_id": user.restaurant_id
            },
            expires_delta=timedelta(hours=24)
        )
        
        return json_response({
            "access_token": new_access_token
        }, "Token refreshed")
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout (client should discard tokens)"""
    return json_response(message="Logout successful")

# ============================================
# CUSTOMER ENDPOINTS
# ============================================

@api_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer account"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'phone_number']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return json_response(
                message=f"Missing required fields: {', '.join(missing_fields)}",
                status=400
            )
        
        # Check if customer already exists with this phone number
        existing_customer = Customer.query.filter_by(phone_number=data['phone_number']).first()
        if existing_customer:
            return json_response(
                message="Customer with this phone number already exists",
                status=409
            )
        
        # Generate customer ID
        customer_id = f"CUST-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create customer
        customer = Customer(
            customer_id=customer_id,
            name=data['name'],
            phone_number=data['phone_number'],
            email=data.get('email'),
            user_id=data.get('user_id')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return json_response({
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "email": customer.email
            }
        }, "Customer created successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create customer error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/customers/<customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Get customer details"""
    try:
        customer = Customer.query.filter_by(customer_id=customer_id).first()
        
        if not customer:
            return json_response(message="Customer not found", status=404)
        
        # Get customer addresses
        addresses = Address.query.filter_by(customer_id=customer_id).all()
        
        return json_response({
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "phone_number": customer.phone_number,
                "email": customer.email,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
                "addresses": [
                    {
                        "address_id": addr.address_id,
                        "street": addr.street,
                        "city": addr.city,
                        "state": addr.state,
                        "postal_code": addr.postal_code,
                        "country": addr.country,
                        "is_default": addr.is_default,
                        "latitude": float(addr.latitude) if addr.latitude else None,
                        "longitude": float(addr.longitude) if addr.longitude else None
                    }
                    for addr in addresses
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Get customer error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# RESTAURANT ENDPOINTS
# ============================================

@api_bp.route('/restaurants', methods=['GET'])
def get_restaurants():
    """Get list of restaurants"""
    try:
        # Get query parameters
        is_open = request.args.get('is_open', type=lambda v: v.lower() == 'true')
        is_active = request.args.get('is_active', True, type=lambda v: v.lower() == 'true')
        
        # Build query
        query = Restaurant.query
        
        if is_open is not None:
            query = query.filter_by(is_open=is_open)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        # Execute query
        restaurants = query.order_by(Restaurant.name).all()
        
        return json_response({
            "restaurants": [
                {
                    "restaurant_id": r.restaurant_id,
                    "name": r.name,
                    "description": r.description,
                    "address": r.address,
                    "phone": r.phone,
                    "email": r.email,
                    "latitude": float(r.latitude) if r.latitude else None,
                    "longitude": float(r.longitude) if r.longitude else None,
                    "delivery_radius": r.delivery_radius,
                    "is_active": r.is_active,
                    "is_open": r.is_open,
                    "opening_time": str(r.opening_time) if r.opening_time else None,
                    "closing_time": str(r.closing_time) if r.closing_time else None,
                    "min_order_amount": float(r.min_order_amount) if r.min_order_amount else 0,
                    "delivery_fee": float(r.delivery_fee) if r.delivery_fee else 0,
                    "estimated_prep_time": r.estimated_prep_time,
                    "rating": float(r.rating) if r.rating else 0,
                    "total_reviews": r.total_reviews,
                    "logo_url": r.logo_url,
                    "banner_url": r.banner_url
                }
                for r in restaurants
            ],
            "count": len(restaurants)
        })
        
    except Exception as e:
        logger.error(f"Get restaurants error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/restaurants/<restaurant_id>/menu', methods=['GET'])
def get_restaurant_menu(restaurant_id):
    """Get restaurant menu items"""
    try:
        restaurant = Restaurant.query.filter_by(restaurant_id=restaurant_id).first()
        
        if not restaurant:
            return json_response(message="Restaurant not found", status=404)
        
        # Get query parameters
        category = request.args.get('category')
        is_available = request.args.get('is_available', True, type=lambda v: v.lower() == 'true')
        
        # Build query
        query = MenuItem.query.filter_by(restaurant_id=restaurant_id)
        
        if category:
            query = query.filter_by(category=category)
        
        if is_available is not None:
            query = query.filter_by(is_available=is_available)
        
        # Execute query
        menu_items = query.order_by(MenuItem.category, MenuItem.name).all()
        
        # Group by category
        menu_by_category = {}
        for item in menu_items:
            category = item.category or "Other"
            if category not in menu_by_category:
                menu_by_category[category] = []
            
            menu_by_category[category].append({
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "price": float(item.price) if item.price else 0,
                "category": item.category,
                "is_available": item.is_available,
                "image_url": item.image_url,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        
        return json_response({
            "restaurant": {
                "restaurant_id": restaurant.restaurant_id,
                "name": restaurant.name
            },
            "menu_by_category": menu_by_category,
            "categories": list(menu_by_category.keys())
        })
        
    except Exception as e:
        logger.error(f"Get restaurant menu error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# ORDER ENDPOINTS
# ============================================

@api_bp.route('/orders', methods=['POST'])
@jwt_required()
@validate_request_data(['customer_id', 'restaurant_id', 'items', 'delivery_type'])
def create_order(data):
    """Create a new order"""
    try:
        # Get current user info
        current_user_id = get_jwt_identity()
        
        # Validate customer
        customer = Customer.query.filter_by(customer_id=data['customer_id']).first()
        if not customer:
            return json_response(message="Customer not found", status=404)
        
        # Validate restaurant
        restaurant = Restaurant.query.filter_by(restaurant_id=data['restaurant_id']).first()
        if not restaurant:
            return json_response(message="Restaurant not found", status=404)
        
        # Check if restaurant is open
        if not restaurant.is_open or not restaurant.is_active:
            return json_response(message="Restaurant is currently closed", status=400)
        
        # Validate delivery type
        if data['delivery_type'] not in ['delivery', 'pickup']:
            return json_response(message="Invalid delivery type", status=400)
        
        # If delivery, validate address
        address_id = data.get('address_id')
        if data['delivery_type'] == 'delivery' and not address_id:
            return json_response(message="Address ID required for delivery", status=400)
        
        if address_id:
            address = Address.query.filter_by(address_id=address_id, customer_id=data['customer_id']).first()
            if not address:
                return json_response(message="Address not found", status=404)
        
        # Validate items
        items = data['items']
        if not isinstance(items, list) or len(items) == 0:
            return json_response(message="Order must contain at least one item", status=400)
        
        subtotal = Decimal('0.00')
        order_items_data = []
        
        # Validate each item
        for item_data in items:
            if 'item_id' not in item_data or 'quantity' not in item_data:
                return json_response(message="Each item must have item_id and quantity", status=400)
            
            menu_item = MenuItem.query.filter_by(
                item_id=item_data['item_id'],
                restaurant_id=data['restaurant_id']
            ).first()
            
            if not menu_item:
                return json_response(message=f"Item {item_data['item_id']} not found", status=404)
            
            if not menu_item.is_available:
                return json_response(message=f"Item {menu_item.name} is not available", status=400)
            
            try:
                quantity = int(item_data['quantity'])
                if quantity <= 0:
                    return json_response(message="Quantity must be greater than 0", status=400)
            except ValueError:
                return json_response(message="Invalid quantity", status=400)
            
            # Calculate item total
            item_total = menu_item.price * quantity
            subtotal += item_total
            
            order_items_data.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'unit_price': menu_item.price,
                'customizations': item_data.get('customizations')
            })
        
        # Check minimum order amount
        if subtotal < restaurant.min_order_amount:
            return json_response(
                message=f"Minimum order amount is ${restaurant.min_order_amount:.2f}",
                status=400
            )
        
        # Calculate totals
        tax_rate = Decimal('0.08')  # 8% tax
        tax = subtotal * tax_rate
        
        delivery_fee = Decimal('0.00')
        if data['delivery_type'] == 'delivery':
            delivery_fee = restaurant.delivery_fee
        
        discount = Decimal(data.get('discount', '0.00'))
        total_amount = subtotal + tax + delivery_fee - discount
        
        # Generate order ID
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=data['customer_id'],
            restaurant_id=data['restaurant_id'],
            address_id=address_id if data['delivery_type'] == 'delivery' else None,
            order_status='pending',
            delivery_type=data['delivery_type'],
            special_instructions=data.get('special_instructions'),
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            discount=discount,
            total_amount=total_amount,
            payment_method=data.get('payment_method', 'cash'),
            payment_status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.order_id,
                item_id=item_data['menu_item'].item_id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                customizations=json.dumps(item_data['customizations']) if item_data['customizations'] else None
            )
            db.session.add(order_item)
        
        # Add to order status history
        from app.models import OrderStatusHistory
        status_history = OrderStatusHistory(
            order_id=order.order_id,
            old_status=None,
            new_status='pending',
            actor_type='customer',
            public_notes="Order placed successfully"
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        # Prepare response
        order_data = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "restaurant_id": order.restaurant_id,
            "order_status": order.order_status,
            "delivery_type": order.delivery_type,
            "subtotal": float(order.subtotal),
            "tax": float(order.tax),
            "delivery_fee": float(order.delivery_fee),
            "discount": float(order.discount),
            "total_amount": float(order.total_amount),
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "items": [
                {
                    "item_id": item_data['menu_item'].item_id,
                    "name": item_data['menu_item'].name,
                    "quantity": item_data['quantity'],
                    "unit_price": float(item_data['unit_price']),
                    "total": float(item_data['unit_price'] * item_data['quantity'])
                }
                for item_data in order_items_data
            ]
        }
        
        logger.info(f"Order created: {order.order_id} by customer {data['customer_id']}")
        
        return json_response(order_data, "Order created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create order error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get order details"""
    try:
        order = Order.query.filter_by(order_id=order_id).first()
        
        if not order:
            return json_response(message="Order not found", status=404)
        
        # Get order items
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        
        # Get status history
        from app.models import OrderStatusHistory
        status_history = OrderStatusHistory.query.filter_by(order_id=order_id)\
            .order_by(OrderStatusHistory.changed_at.desc()).all()
        
        # Get restaurant info
        restaurant = Restaurant.query.filter_by(restaurant_id=order.restaurant_id).first()
        
        # Get customer info
        customer = Customer.query.filter_by(customer_id=order.customer_id).first()
        
        # Get driver info if assigned
        driver_info = None
        if order.driver_id:
            driver = Driver.query.get(order.driver_id)
            if driver:
                user = User.query.get(driver.user_id)
                driver_info = {
                    "driver_id": driver.driver_id,
                    "name": user.username if user else "Unknown",
                    "vehicle_type": driver.vehicle_type,
                    "phone_number": user.phone_number if user else None,
                    "rating": float(driver.rating) if driver.rating else 0
                }
        
        # Get address info if delivery
        address_info = None
        if order.address_id:
            address = Address.query.get(order.address_id)
            if address:
                address_info = {
                    "street": address.street,
                    "city": address.city,
                    "state": address.state,
                    "postal_code": address.postal_code,
                    "country": address.country
                }
        
        return json_response({
            "order": {
                "order_id": order.order_id,
                "order_status": order.order_status,
                "delivery_type": order.delivery_type,
                "special_instructions": order.special_instructions,
                "subtotal": float(order.subtotal),
                "tax": float(order.tax),
                "delivery_fee": float(order.delivery_fee),
                "discount": float(order.discount),
                "total_amount": float(order.total_amount),
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "transaction_id": order.transaction_id,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                "customer": {
                    "customer_id": customer.customer_id if customer else None,
                    "name": customer.name if customer else None,
                    "phone_number": customer.phone_number if customer else None
                },
                "restaurant": {
                    "restaurant_id": restaurant.restaurant_id if restaurant else None,
                    "name": restaurant.name if restaurant else None,
                    "address": restaurant.address if restaurant else None,
                    "phone": restaurant.phone if restaurant else None
                },
                "driver": driver_info,
                "address": address_info,
                "items": [
                    {
                        "item_id": item.item_id,
                        "name": MenuItem.query.filter_by(item_id=item.item_id).first().name if MenuItem.query.filter_by(item_id=item.item_id).first() else "Unknown",
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "total": float(item.unit_price * item.quantity),
                        "customizations": json.loads(item.customizations) if item.customizations else None
                    }
                    for item in order_items
                ],
                "status_history": [
                    {
                        "old_status": history.old_status,
                        "new_status": history.new_status,
                        "changed_at": history.changed_at.isoformat() if history.changed_at else None,
                        "actor_type": history.actor_type,
                        "public_notes": history.public_notes
                    }
                    for history in status_history
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Get order error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/orders/<order_id>/status', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'manager', 'driver', 'restaurant'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return json_response(message="Status is required", status=400)
        
        new_status = data['status']
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered', 'cancelled']
        
        if new_status not in valid_statuses:
            return json_response(message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}", status=400)
        
        order = Order.query.filter_by(order_id=order_id).first()
        
        if not order:
            return json_response(message="Order not found", status=404)
        
        old_status = order.order_status
        
        # Validate status transition
        status_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing', 'cancelled'],
            'preparing': ['ready', 'cancelled'],
            'ready': ['out_for_delivery', 'cancelled'],
            'out_for_delivery': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        if new_status not in status_transitions.get(old_status, []):
            return json_response(
                message=f"Cannot transition from {old_status} to {new_status}",
                status=400
            )
        
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Update order status
        order.order_status = new_status
        order.updated_at = datetime.now()
        
        # Handle special cases
        if new_status == 'out_for_delivery':
            order.estimated_delivery = datetime.now() + timedelta(minutes=30)  # Estimate 30 minutes
        
        if new_status == 'delivered':
            order.delivered_at = datetime.now()
        
        # Add to status history
        from app.models import OrderStatusHistory
        status_history = OrderStatusHistory(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user_id,
            actor_type=current_user.role if current_user else 'system',
            public_notes=data.get('public_notes'),
            internal_notes=data.get('internal_notes'),
            reason_code=data.get('reason_code')
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        logger.info(f"Order {order_id} status updated from {old_status} to {new_status} by user {current_user_id}")
        
        return json_response({
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": order.updated_at.isoformat()
        }, "Order status updated successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update order status error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# LIVE TRACKING ENDPOINTS
# ============================================

@api_bp.route('/orders/<order_id>/track', methods=['GET'])
@jwt_required()
def track_order(order_id):
    """Get real-time order tracking information"""
    try:
        order = Order.query.filter_by(order_id=order_id).first()
        
        if not order:
            return json_response(message="Order not found", status=404)
        
        # Get driver location if assigned
        driver_location = None
        driver_info = None
        
        if order.driver_id:
            driver = Driver.query.get(order.driver_id)
            if driver:
                user = User.query.get(driver.user_id)
                driver_info = {
                    "driver_id": driver.driver_id,
                    "name": user.username if user else "Unknown",
                    "vehicle_type": driver.vehicle_type,
                    "phone_number": user.phone_number if user else None,
                    "rating": float(driver.rating) if driver.rating else 0
                }
                
                # Simulate driver location (in production, this would come from GPS)
                if driver.current_location:
                    driver_location = driver.current_location
        
        # Calculate ETA
        eta_minutes = None
        if order.estimated_delivery:
            time_diff = order.estimated_delivery - datetime.now()
            eta_minutes = max(0, int(time_diff.total_seconds() / 60))
        
        # Get status history for timeline
        from app.models import OrderStatusHistory
        status_timeline = OrderStatusHistory.query.filter_by(order_id=order_id)\
            .order_by(OrderStatusHistory.changed_at.asc()).all()
        
        # Get restaurant location
        restaurant = Restaurant.query.filter_by(restaurant_id=order.restaurant_id).first()
        restaurant_location = {
            "latitude": float(restaurant.latitude) if restaurant.latitude else None,
            "longitude": float(restaurant.longitude) if restaurant.longitude else None,
            "address": restaurant.address
        } if restaurant else None
        
        # Get delivery address if applicable
        delivery_address = None
        if order.delivery_type == 'delivery' and order.address_id:
            address = Address.query.get(order.address_id)
            if address:
                delivery_address = {
                    "street": address.street,
                    "city": address.city,
                    "state": address.state,
                    "postal_code": address.postal_code,
                    "latitude": float(address.latitude) if address.latitude else None,
                    "longitude": float(address.longitude) if address.longitude else None
                }
        
        return json_response({
            "order_id": order_id,
            "order_status": order.order_status,
            "delivery_type": order.delivery_type,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "driver": driver_info,
            "driver_location": driver_location,
            "restaurant_location": restaurant_location,
            "delivery_address": delivery_address,
            "eta_minutes": eta_minutes,
            "status_timeline": [
                {
                    "status": history.new_status,
                    "timestamp": history.changed_at.isoformat() if history.changed_at else None,
                    "notes": history.public_notes
                }
                for history in status_timeline
            ]
        })
        
    except Exception as e:
        logger.error(f"Track order error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/drivers/<driver_id>/location', methods=['PUT'])
@jwt_required()
@role_required(['driver', 'admin'])
def update_driver_location(driver_id):
    """Update driver's current location (GPS)"""
    try:
        data = request.get_json()
        
        if not data or 'location' not in data:
            return json_response(message="Location is required", status=400)
        
        driver = Driver.query.get(driver_id)
        
        if not driver:
            return json_response(message="Driver not found", status=404)
        
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Verify driver ownership (drivers can only update their own location)
        if current_user.role == 'driver' and driver.user_id != current_user_id:
            return json_response(message="Cannot update other driver's location", status=403)
        
        # Update location
        driver.current_location = data['location']
        driver.updated_at = datetime.now()
        
        # Optionally update latitude/longitude if provided
        if 'latitude' in data and 'longitude' in data:
            driver.current_latitude = data['latitude']
            driver.current_longitude = data['longitude']
        
        db.session.commit()
        
        return json_response({
            "driver_id": driver_id,
            "location": driver.current_location,
            "updated_at": driver.updated_at.isoformat()
        }, "Driver location updated")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update driver location error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# DRIVER ENDPOINTS
# ============================================

@api_bp.route('/drivers/available', methods=['GET'])
@jwt_required()
def get_available_drivers():
    """Get list of available drivers"""
    try:
        # Get query parameters
        vehicle_type = request.args.get('vehicle_type')
        min_rating = request.args.get('min_rating', type=float)
        
        # Build query
        query = Driver.query.filter_by(is_available=True, is_on_shift=True)
        
        if vehicle_type:
            query = query.filter_by(vehicle_type=vehicle_type)
        
        if min_rating:
            query = query.filter(Driver.rating >= min_rating)
        
        # Execute query
        drivers = query.order_by(Driver.rating.desc()).all()
        
        # Get user info for each driver
        available_drivers = []
        for driver in drivers:
            user = User.query.get(driver.user_id)
            if user and user.is_active:
                available_drivers.append({
                    "driver_id": driver.driver_id,
                    "user_id": driver.user_id,
                    "name": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "vehicle_type": driver.vehicle_type,
                    "vehicle_model": driver.vehicle_model,
                    "license_plate": driver.license_plate,
                    "rating": float(driver.rating) if driver.rating else 0,
                    "current_location": driver.current_location,
                    "total_deliveries": driver.total_deliveries,
                    "completed_deliveries": driver.completed_deliveries,
                    "avg_delivery_time": driver.avg_delivery_time,
                    "is_on_shift": driver.is_on_shift,
                    "shift_start": str(driver.shift_start) if driver.shift_start else None,
                    "shift_end": str(driver.shift_end) if driver.shift_end else None
                })
        
        return json_response({
            "drivers": available_drivers,
            "count": len(available_drivers)
        })
        
    except Exception as e:
        logger.error(f"Get available drivers error: {str(e)}")
        return json_response(message="Internal server error", status=500)

@api_bp.route('/drivers/<driver_id>/assign-order', methods=['POST'])
@jwt_required()
@role_required(['admin', 'manager'])
def assign_order_to_driver(driver_id, order_id):
    """Assign an order to a driver"""
    try:
        data = request.get_json()
        
        if not data or 'order_id' not in data:
            return json_response(message="Order ID is required", status=400)
        
        order_id = data['order_id']
        
        # Get driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return json_response(message="Driver not found", status=404)
        
        # Check if driver is available
        if not driver.is_available or not driver.is_on_shift:
            return json_response(message="Driver is not available", status=400)
        
        # Get order
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return json_response(message="Order not found", status=404)
        
        # Check if order is ready for delivery
        if order.order_status not in ['ready', 'confirmed']:
            return json_response(message="Order is not ready for delivery", status=400)
        
        # Check if order already has a driver
        if order.driver_id:
            return json_response(message="Order already has a driver assigned", status=400)
        
        # Assign driver to order
        order.driver_id = driver_id
        order.order_status = 'out_for_delivery'
        order.estimated_delivery = datetime.now() + timedelta(minutes=30)  # Estimate 30 minutes
        order.updated_at = datetime.now()
        
        # Mark driver as unavailable
        driver.is_available = False
        driver.updated_at = datetime.now()
        
        # Add to status history
        from app.models import OrderStatusHistory
        status_history = OrderStatusHistory(
            order_id=order_id,
            old_status='ready',
            new_status='out_for_delivery',
            driver_id=driver_id,
            actor_type='admin',
            public_notes=f"Order assigned to driver {driver_id}"
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        logger.info(f"Order {order_id} assigned to driver {driver_id}")
        
        return json_response({
            "order_id": order_id,
            "driver_id": driver_id,
            "assigned_at": datetime.now().isoformat(),
            "estimated_delivery": order.estimated_delivery.isoformat()
        }, "Order assigned to driver successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Assign order to driver error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# SYSTEM HEALTH & MONITORING
# ============================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        # Get basic stats
        orders_count = Order.query.count()
        active_orders = Order.query.filter(Order.order_status.notin_(['delivered', 'cancelled'])).count()
        available_drivers = Driver.query.filter_by(is_available=True, is_on_shift=True).count()
        
        return json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "statistics": {
                "total_orders": orders_count,
                "active_orders": active_orders,
                "available_drivers": available_drivers
            }
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return json_response({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }, "Service is unhealthy", 503)

@api_bp.route('/metrics', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_metrics():
    """Get system metrics (admin only)"""
    try:
        # Get time range
        days = request.args.get('days', 7, type=int)
        since_date = datetime.now() - timedelta(days=days)
        
        # Calculate metrics
        with db.engine.connect() as conn:
            # Order metrics
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
                    SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
                    AVG(total_amount) as avg_order_value,
                    SUM(total_amount) as total_revenue
                FROM orders 
                WHERE created_at >= :since_date
            """), {"since_date": since_date})
            order_metrics = result.fetchone()
            
            # Driver metrics
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_drivers,
                    SUM(CASE WHEN is_available = true AND is_on_shift = true THEN 1 ELSE 0 END) as available_drivers,
                    AVG(rating) as avg_driver_rating
                FROM drivers
            """))
            driver_metrics = result.fetchone()
            
            # Customer metrics
            result = conn.execute(text("""
                SELECT 
                    COUNT(DISTINCT customer_id) as unique_customers,
                    COUNT(*) as total_orders
                FROM orders 
                WHERE created_at >= :since_date
            """), {"since_date": since_date})
            customer_metrics = result.fetchone()
            
            # Daily orders for chart
            result = conn.execute(text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as order_count,
                    SUM(total_amount) as daily_revenue
                FROM orders 
                WHERE created_at >= :since_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """), {"since_date": since_date})
            daily_stats = result.fetchall()
        
        return json_response({
            "period": f"last_{days}_days",
            "since_date": since_date.isoformat(),
            "orders": {
                "total": order_metrics[0] if order_metrics else 0,
                "delivered": order_metrics[1] if order_metrics else 0,
                "cancelled": order_metrics[2] if order_metrics else 0,
                "avg_value": float(order_metrics[3]) if order_metrics and order_metrics[3] else 0,
                "total_revenue": float(order_metrics[4]) if order_metrics and order_metrics[4] else 0
            },
            "drivers": {
                "total": driver_metrics[0] if driver_metrics else 0,
                "available": driver_metrics[1] if driver_metrics else 0,
                "avg_rating": float(driver_metrics[2]) if driver_metrics and driver_metrics[2] else 0
            },
            "customers": {
                "unique": customer_metrics[0] if customer_metrics else 0,
                "total_orders": customer_metrics[1] if customer_metrics else 0
            },
            "daily_stats": [
                {
                    "date": str(stat[0]),
                    "order_count": stat[1],
                    "daily_revenue": float(stat[2]) if stat[2] else 0
                }
                for stat in daily_stats
            ]
        })
        
    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# ERROR HANDLERS
# ============================================

@api_bp.errorhandler(404)
def not_found(error):
    return json_response(message="Resource not found", status=404)

@api_bp.errorhandler(405)
def method_not_allowed(error):
    return json_response(message="Method not allowed", status=405)

@api_bp.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return json_response(message="Internal server error", status=500)

# ============================================
# REQUEST HOOKS
# ============================================

@api_bp.before_request
def before_request():
    """Log API requests"""
    g.start_time = datetime.now()
    g.request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"Request {g.request_id}: {request.method} {request.path}")

@api_bp.after_request
def after_request(response):
    """Log API responses"""
    if hasattr(g, 'start_time'):
        duration = (datetime.now() - g.start_time).total_seconds() * 1000
        logger.info(f"Response {g.request_id}: {response.status_code} ({duration:.2f}ms)")
    
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response
