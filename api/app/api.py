# api/app/api.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, create_access_token, 
    get_jwt_identity
)
import logging
from datetime import datetime
import json
from sqlalchemy import text
import uuid
import traceback

# Import from shared models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from shared.models import db, User, Customer, Restaurant, MenuItem, Order, Driver, OrderItem, Address, OrderStatusHistory


# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def json_response(data=None, message="", status=200):
    """Standard JSON response format"""
    response = {
        "success": status < 400,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    return jsonify(response), status

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
        
        if not user or not user.verify_password(data['password']):
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
            }
        )
        
        return json_response({
            "access_token": access_token,
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

# ============================================
# RESTAURANT ENDPOINTS
# ============================================

@api_bp.route('/restaurants', methods=['GET'])
def get_restaurants():
    """Get list of restaurants"""
    try:
        restaurants = Restaurant.query.filter_by(is_active=True).order_by(Restaurant.name).all()
        
        return json_response({
            "restaurants": [
                {
                    "restaurant_id": r.restaurant_id,
                    "name": r.name,
                    "description": r.description,
                    "address": r.address,
                    "phone": r.phone,
                    "is_open": r.is_open,
                    "delivery_fee": float(r.delivery_fee) if r.delivery_fee else 0,
                    "rating": float(r.rating) if r.rating else 0,
                    "estimated_prep_time": r.estimated_prep_time
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
        
        menu_items = MenuItem.query.filter_by(
            restaurant_id=restaurant_id, 
            is_available=True
        ).order_by(MenuItem.category, MenuItem.name).all()
        
        return json_response({
            "restaurant": {
                "restaurant_id": restaurant.restaurant_id,
                "name": restaurant.name
            },
            "menu_items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "description": item.description,
                    "price": float(item.price) if item.price else 0,
                    "category": item.category,
                    "image_url": item.image_url
                }
                for item in menu_items
            ]
        })
        
    except Exception as e:
        logger.error(f"Get restaurant menu error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# ORDER ENDPOINTS
# ============================================

@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_id', 'restaurant_id', 'items']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return json_response(
                message=f"Missing required fields: {', '.join(missing_fields)}",
                status=400
            )
        
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
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
        
        # Calculate order total
        subtotal = 0
        order_items = []
        
        for item_data in data['items']:
            menu_item = MenuItem.query.filter_by(
                item_id=item_data['item_id'],
                restaurant_id=data['restaurant_id']
            ).first()
            
            if not menu_item:
                return json_response(message=f"Item {item_data['item_id']} not found", status=404)
            
            if not menu_item.is_available:
                return json_response(message=f"Item {menu_item.name} is not available", status=400)
            
            quantity = item_data.get('quantity', 1)
            if quantity <= 0:
                return json_response(message="Quantity must be greater than 0", status=400)
            
            subtotal += float(menu_item.price) * quantity
            order_items.append({
                'menu_item': menu_item,
                'quantity': quantity
            })
        
        # Calculate totals
        tax = subtotal * 0.08  # 8% tax
        delivery_fee = float(restaurant.delivery_fee) if restaurant.delivery_fee else 0
        total_amount = subtotal + tax + delivery_fee
        
        # Generate order ID
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=data['customer_id'],
            restaurant_id=data['restaurant_id'],
            order_status='pending',
            delivery_type=data.get('delivery_type', 'delivery'),
            special_instructions=data.get('special_instructions'),
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            payment_method=data.get('payment_method', 'cash'),
            payment_status='pending'
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item in order_items:
            order_item = OrderItem(
                order_id=order_id,
                item_id=item['menu_item'].item_id,
                quantity=item['quantity'],
                unit_price=item['menu_item'].price
            )
            db.session.add(order_item)
        
        # Add to order status history
        status_history = OrderStatusHistory(
            order_id=order_id,
            old_status=None,
            new_status='pending',
            actor_type='customer',
            public_notes="Order placed successfully"
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        logger.info(f"Order created: {order_id} by customer {data['customer_id']}")
        
        return json_response({
            "order_id": order_id,
            "status": "pending",
            "total_amount": total_amount,
            "estimated_prep_time": restaurant.estimated_prep_time
        }, "Order created successfully", 201)
        
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
        status_history = OrderStatusHistory.query.filter_by(order_id=order_id)\
            .order_by(OrderStatusHistory.changed_at.desc()).all()
        
        return json_response({
            "order": {
                "order_id": order.order_id,
                "order_status": order.order_status,
                "delivery_type": order.delivery_type,
                "subtotal": float(order.subtotal),
                "tax": float(order.tax),
                "delivery_fee": float(order.delivery_fee),
                "total_amount": float(order.total_amount),
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                "items": [
                    {
                        "item_id": item.item_id,
                        "name": MenuItem.query.filter_by(item_id=item.item_id).first().name if MenuItem.query.filter_by(item_id=item.item_id).first() else "Unknown",
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "total": float(item.unit_price * item.quantity)
                    }
                    for item in order_items
                ],
                "status_history": [
                    {
                        "status": history.new_status,
                        "timestamp": history.changed_at.isoformat() if history.changed_at else None,
                        "notes": history.public_notes
                    }
                    for history in status_history
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Get order error: {str(e)}")
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
                    "rating": float(driver.rating) if driver.rating else 0,
                    "current_location": driver.current_location
                }
        
        return json_response({
            "order_id": order_id,
            "order_status": order.order_status,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "driver": driver_info,
            "status_timeline": [
                {
                    "status": history.new_status,
                    "timestamp": history.changed_at.isoformat() if history.changed_at else None,
                    "notes": history.public_notes
                }
                for history in OrderStatusHistory.query.filter_by(order_id=order_id)
                .order_by(OrderStatusHistory.changed_at.asc()).all()
            ]
        })
        
    except Exception as e:
        logger.error(f"Track order error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# DRIVER ENDPOINTS
# ============================================

@api_bp.route('/drivers/available', methods=['GET'])
@jwt_required()
def get_available_drivers():
    """Get list of available drivers"""
    try:
        drivers = Driver.query.filter_by(is_available=True, is_on_shift=True)\
            .order_by(Driver.rating.desc()).all()
        
        available_drivers = []
        for driver in drivers:
            user = User.query.get(driver.user_id)
            if user and user.is_active:
                available_drivers.append({
                    "driver_id": driver.driver_id,
                    "name": user.username,
                    "vehicle_type": driver.vehicle_type,
                    "vehicle_model": driver.vehicle_model,
                    "rating": float(driver.rating) if driver.rating else 0,
                    "current_location": driver.current_location,
                    "avg_delivery_time": driver.avg_delivery_time
                })
        
        return json_response({
            "drivers": available_drivers,
            "count": len(available_drivers)
        })
        
    except Exception as e:
        logger.error(f"Get available drivers error: {str(e)}")
        return json_response(message="Internal server error", status=500)

# ============================================
# SYSTEM HEALTH
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

# ============================================
# API DOCUMENTATION
# ============================================

@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API Documentation"""
    docs = {
        "version": "1.0.0",
        "base_url": "/api/v1",
        "authentication": "Use JWT Bearer token in Authorization header",
        "endpoints": {
            "authentication": {
                "POST /auth/login": "User login"
            },
            "restaurants": {
                "GET /restaurants": "Get list of restaurants",
                "GET /restaurants/{id}/menu": "Get restaurant menu"
            },
            "orders": {
                "POST /orders": "Create new order (JWT required)",
                "GET /orders/{id}": "Get order details (JWT required)",
                "GET /orders/{id}/track": "Track order (JWT required)"
            },
            "drivers": {
                "GET /drivers/available": "Get available drivers (JWT required)"
            },
            "system": {
                "GET /health": "Health check"
            }
        }
    }
    return jsonify(docs)

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
