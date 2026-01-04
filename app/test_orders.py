# app/test_orders.py - Virtual Order Testing Blueprint
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Restaurant, Customer, Order, OrderItem, MenuItem, Address, Driver, db
from datetime import datetime, timedelta
import random
import string
from sqlalchemy import func
from sqlalchemy.orm import joinedload  # Add this import

test_bp = Blueprint('test', __name__, url_prefix='/test')

# Predefined test data
TEST_PIZZAS = [
    {"name": "Margherita Pizza", "description": "Classic tomato sauce, mozzarella, fresh basil", "price": 12.99},
    {"name": "Pepperoni Pizza", "description": "Tomato sauce, mozzarella, pepperoni", "price": 14.99},
    {"name": "Hawaiian Pizza", "description": "Tomato sauce, mozzarella, ham, pineapple", "price": 15.99},
    {"name": "BBQ Chicken Pizza", "description": "BBQ sauce, chicken, red onions, cilantro", "price": 16.99},
    {"name": "Vegetarian Pizza", "description": "Tomato sauce, mixed vegetables, mushrooms, olives", "price": 13.99},
    {"name": "Meat Lovers Pizza", "description": "Tomato sauce, pepperoni, sausage, ham, bacon", "price": 18.99},
    {"name": "Four Cheese Pizza", "description": "Mozzarella, parmesan, gorgonzola, goat cheese", "price": 17.99},
    {"name": "Spicy Pizza", "description": "Tomato sauce, jalapeños, spicy sausage, chili oil", "price": 16.99},
]

TEST_SIDES = [
    {"name": "Garlic Bread", "price": 4.99},
    {"name": "Chicken Wings (6 pcs)", "price": 8.99},
    {"name": "Caesar Salad", "price": 6.99},
    {"name": "French Fries", "price": 3.99},
    {"name": "Onion Rings", "price": 4.99},
]

TEST_DRINKS = [
    {"name": "Coca-Cola", "price": 2.49},
    {"name": "Sprite", "price": 2.49},
    {"name": "Fanta", "price": 2.49},
    {"name": "Water", "price": 1.99},
    {"name": "Orange Juice", "price": 3.49},
]

TEST_CUSTOMERS = [
    {"name": "John Smith", "phone": "555-0101", "email": "john.smith@email.com"},
    {"name": "Emma Johnson", "phone": "555-0102", "email": "emma.j@email.com"},
    {"name": "Michael Brown", "phone": "555-0103", "email": "m.brown@email.com"},
    {"name": "Sarah Davis", "phone": "555-0104", "email": "sarah.d@email.com"},
    {"name": "Robert Wilson", "phone": "555-0105", "email": "rob.wilson@email.com"},
    {"name": "Lisa Taylor", "phone": "555-0106", "email": "lisa.t@email.com"},
    {"name": "David Miller", "phone": "555-0107", "email": "d.miller@email.com"},
    {"name": "Jennifer Lee", "phone": "555-0108", "email": "j.lee@email.com"},
]

TEST_ADDRESSES = [
    {"street": "123 Main Street", "city": "New York", "state": "NY", "zip_code": "10001"},
    {"street": "456 Oak Avenue", "city": "New York", "state": "NY", "zip_code": "10002"},
    {"street": "789 Pine Road", "city": "New York", "state": "NY", "zip_code": "10003"},
    {"street": "321 Elm Street", "city": "New York", "state": "NY", "zip_code": "10004"},
    {"street": "654 Maple Drive", "city": "New York", "state": "NY", "zip_code": "10005"},
]

# Helper functions
def generate_order_id():
    """Generate a random order ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TEST-{timestamp}-{random_str}"

def get_random_restaurant():
    """Get a random active restaurant"""
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    if restaurants:
        return random.choice(restaurants)
    return None

def get_random_driver():
    """Get a random available driver"""
    drivers = Driver.query.filter_by(is_available=True, is_on_shift=True).all()
    if drivers:
        return random.choice(drivers)
    return None

def get_random_customer():
    """Get or create a random customer"""
    customers = Customer.query.all()
    if customers:
        return random.choice(customers)
    
    # Create a new test customer
    test_customer = TEST_CUSTOMERS[random.randint(0, len(TEST_CUSTOMERS)-1)]
    
    # Create user first
    user = User(
        username=f"test_{test_customer['name'].lower().replace(' ', '_')}",
        email=test_customer['email'],
        phone_number=test_customer['phone'],
        role='user',
        is_active=True
    )
    user.password = 'Test@123'
    db.session.add(user)
    db.session.flush()
    
    # Create customer
    customer = Customer(
        user_id=user.user_id,
        name=test_customer['name']
    )
    db.session.add(customer)
    db.session.commit()
    
    return customer

def get_random_address(customer_id):
    """Get or create a random address for customer"""
    addresses = Address.query.filter_by(customer_id=customer_id).all()
    if addresses:
        return random.choice(addresses)
    
    # Create a new address
    test_address = TEST_ADDRESSES[random.randint(0, len(TEST_ADDRESSES)-1)]
    address = Address(
        customer_id=customer_id,
        street=test_address['street'],
        city=test_address['city'],
        state=test_address['state'],
        zip_code=test_address['zip_code'],
        is_primary=True
    )
    db.session.add(address)
    db.session.commit()
    
    return address

def create_test_menu_items():
    """Create test menu items if they don't exist"""
    restaurant = get_random_restaurant()
    if not restaurant:
        return []
    
    # Check if menu items already exist
    existing_items = MenuItem.query.filter_by(restaurant_id=restaurant.restaurant_id).count()
    if existing_items > 0:
        return MenuItem.query.filter_by(restaurant_id=restaurant.restaurant_id).all()
    
    # Create pizza items
    menu_items = []
    for pizza in TEST_PIZZAS:
        item = MenuItem(
            restaurant_id=restaurant.restaurant_id,
            name=pizza['name'],
            description=pizza['description'],
            price=pizza['price'],
            category='pizza',
            is_available=True,
            preparation_time=random.randint(15, 25)
        )
        db.session.add(item)
        menu_items.append(item)
    
    # Create side items
    for side in TEST_SIDES:
        item = MenuItem(
            restaurant_id=restaurant.restaurant_id,
            name=side['name'],
            price=side['price'],
            category='side',
            is_available=True,
            preparation_time=random.randint(5, 10)
        )
        db.session.add(item)
        menu_items.append(item)
    
    # Create drink items
    for drink in TEST_DRINKS:
        item = MenuItem(
            restaurant_id=restaurant.restaurant_id,
            name=drink['name'],
            price=drink['price'],
            category='drink',
            is_available=True,
            preparation_time=2
        )
        db.session.add(item)
        menu_items.append(item)
    
    db.session.commit()
    return menu_items

# ============================================
# TEST ROUTES
# ============================================

@test_bp.route('/')
def test_index():
    """Redirect to dashboard or show simple test page"""
    # Check if user is authenticated and admin
    is_authenticated = current_user.is_authenticated
    is_admin = is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin()
    
    if is_admin:
        return redirect(url_for('test.test_dashboard'))
    
    # Build HTML response
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mega Pizza Test System</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
            h1 {{ color: #e63946; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .endpoint {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; }}
            .btn {{ display: inline-block; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 10px 5px; }}
            .btn-primary {{ background: #007bff; color: white; }}
            .btn-danger {{ background: #e63946; color: white; }}
        </style>
    </head>
    <body>
        <h1>🍕 Mega Pizza Test System</h1>
        <div class="card">
            <h3>Virtual Order Testing Platform</h3>
            <p>This system allows you to simulate Android app orders for testing purposes.</p>
    '''
    
    if is_authenticated:
        if is_admin:
            html += '''
            <p>✅ You are logged in as an administrator.</p>
            <a href="/test/dashboard" class="btn btn-danger">Go to Test Dashboard</a>
            '''
        else:
            html += '''
            <p>⚠️ You need administrator privileges to access the test dashboard.</p>
            <a href="/admin/dashboard" class="btn btn-primary">Go to Admin Dashboard</a>
            '''
    else:
        html += '''
        <p>🔒 Please login to access the test system.</p>
        <a href="/auth/login" class="btn btn-primary">Login Now</a>
        '''
    
    html += '''
        </div>
        
        <div class="card">
            <h3>Available API Endpoints</h3>
            <div class="endpoint">
                <strong>GET</strong> <code>/test/test-api</code>
                <p>Check API connectivity and status</p>
            </div>
            <div class="endpoint">
                <strong>POST</strong> <code>/test/api/simulate-android-order</code>
                <p>Simulate Android app order (JSON required)</p>
                <p><small>Example JSON:</small></p>
                <pre style="background: #eee; padding: 10px; font-size: 12px;">{
  "customer_id": 1,
  "restaurant_id": 1,
  "items": [
    {"menu_item_id": 1, "quantity": 2, "price": 12.99}
  ],
  "subtotal": 25.98,
  "total_amount": 31.05
}</pre>
            </div>
            <div class="endpoint">
                <strong>POST</strong> <code>/test/create-order</code>
                <p>Create a random test order (admin only)</p>
            </div>
        </div>
        
        <p><small>This is a testing system. All orders created here are virtual and for testing only.</small></p>
    </body>
    </html>
    '''
    
    return html


@test_bp.route('/dashboard')
@login_required
def test_dashboard():
    """Test dashboard for order simulation"""
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        # Get statistics
        stats = {
            'total_test_orders': Order.query.filter(Order.order_id.like('TEST-%')).count(),
            'today_test_orders': Order.query.filter(
                Order.order_id.like('TEST-%'),
                db.func.date(Order.created_at) == datetime.today().date()
            ).count(),
            'active_restaurants': Restaurant.query.filter_by(is_active=True).count(),
            'available_drivers': Driver.query.filter_by(is_available=True).count(),
        }
        
        # Recent test orders - with proper relationship loading
        recent_orders = Order.query.filter(
            Order.order_id.like('TEST-%')
        ).order_by(Order.created_at.desc()).limit(10).all()
        
        # Pre-load related objects to avoid template errors
        orders_with_details = []
        for order in recent_orders:
            # Try to get customer and restaurant by ID if relationships not loaded
            customer = None
            restaurant = None
            
            if hasattr(order, 'customer') and order.customer:
                customer = order.customer
            else:
                # Fallback: query directly
                customer = Customer.query.get(order.customer_id)
            
            if hasattr(order, 'restaurant') and order.restaurant:
                restaurant = order.restaurant
            else:
                # Fallback: query directly
                restaurant = Restaurant.query.get(order.restaurant_id)
            
            orders_with_details.append({
                'order': order,
                'customer': customer,
                'restaurant': restaurant
            })
        
        # Get menu items for display
        menu_items = create_test_menu_items()
        
        return render_template('test/dashboard.html',
                             stats=stats,
                             orders_with_details=orders_with_details,  # Pass the new structure
                             recent_orders=recent_orders,  # Keep for compatibility
                             menu_items=menu_items,
                             test_pizzas=TEST_PIZZAS,
                             test_sides=TEST_SIDES,
                             test_drinks=TEST_DRINKS)
    except Exception as e:
        flash(f'Error loading test dashboard: {str(e)}', 'danger')
        import traceback
        print(f"Error in test_dashboard: {e}")
        print(traceback.format_exc())
        return redirect(url_for('admin.dashboard'))

@test_bp.route('/create-order', methods=['POST'])
@login_required
def create_test_order():
    """Create a test order (simulating Android app order)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Administrator access required'}), 403
    
    try:
        # Get order data from request
        data = request.get_json()
        
        # Create order ID
        order_id = generate_order_id()
        
        # Get random customer or use provided one
        if data.get('customer_id'):
            customer = Customer.query.get(data['customer_id'])
        else:
            customer = get_random_customer()
        
        # Get random restaurant
        restaurant = get_random_restaurant()
        if not restaurant:
            return jsonify({'success': False, 'message': 'No active restaurants available'}), 400
        
        # Get or create address
        address = get_random_address(customer.customer_id)
        
        # Create menu items if needed
        menu_items = create_test_menu_items()
        
        # Calculate order details
        subtotal = 0
        items_data = []
        
        # Add random pizzas
        num_pizzas = random.randint(1, 3)
        pizza_items = [item for item in menu_items if item.category == 'pizza']
        
        for _ in range(num_pizzas):
            pizza = random.choice(pizza_items)
            quantity = random.randint(1, 2)
            subtotal += pizza.price * quantity
            items_data.append({
                'menu_item_id': pizza.menu_item_id,
                'quantity': quantity,
                'price': float(pizza.price),
                'name': pizza.name
            })
        
        # Add random side (50% chance)
        if random.random() > 0.5:
            side_items = [item for item in menu_items if item.category == 'side']
            side = random.choice(side_items)
            quantity = random.randint(1, 2)
            subtotal += side.price * quantity
            items_data.append({
                'menu_item_id': side.menu_item_id,
                'quantity': quantity,
                'price': float(side.price),
                'name': side.name
            })
        
        # Add random drinks
        num_drinks = random.randint(1, 4)
        drink_items = [item for item in menu_items if item.category == 'drink']
        
        for _ in range(num_drinks):
            drink = random.choice(drink_items)
            quantity = random.randint(1, 3)
            subtotal += drink.price * quantity
            items_data.append({
                'menu_item_id': drink.menu_item_id,
                'quantity': quantity,
                'price': float(drink.price),
                'name': drink.name
            })
        
        # Calculate fees
        delivery_fee = 2.99 if data.get('delivery_type', 'delivery') == 'delivery' else 0
        tax = subtotal * 0.08  # 8% tax
        total_amount = subtotal + delivery_fee + tax
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=customer.customer_id,
            restaurant_id=restaurant.restaurant_id,
            address_id=address.address_id,
            delivery_type=data.get('delivery_type', 'delivery'),
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            order_status='pending',
            payment_method=data.get('payment_method', 'cash'),
            payment_status='pending',
            special_instructions=data.get('special_instructions', '')
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item_data in items_data:
            order_item = OrderItem(
                order_id=order.order_id,
                menu_item_id=item_data['menu_item_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(order_item)
        
        # Assign driver for delivery orders
        if order.delivery_type == 'delivery':
            driver = get_random_driver()
            if driver:
                order.driver_id = driver.driver_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': f'Test order created successfully: {order_id}',
            'order_details': {
                'customer': customer.name,
                'restaurant': restaurant.name,
                'address': f"{address.street}, {address.city}",
                'subtotal': float(subtotal),
                'tax': float(tax),
                'delivery_fee': float(delivery_fee),
                'total': float(total_amount),
                'items': items_data
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating order: {str(e)}'}), 500

@test_bp.route('/create-bulk-orders', methods=['POST'])
@login_required
def create_bulk_orders():
    """Create multiple test orders at once"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Administrator access required'}), 403
    
    try:
        data = request.get_json()
        num_orders = min(data.get('count', 5), 20)  # Max 20 orders at once
        
        results = []
        for i in range(num_orders):
            # Generate order ID
            order_id = generate_order_id()
            
            # Get random customer
            customer = get_random_customer()
            
            # Get random restaurant
            restaurant = get_random_restaurant()
            if not restaurant:
                continue  # Skip if no restaurant
            
            # Get or create address
            address = get_random_address(customer.customer_id)
            
            # Calculate random prices
            subtotal = random.uniform(20, 50)
            tax = subtotal * 0.08
            delivery_type = random.choice(['delivery', 'pickup'])
            delivery_fee = 2.99 if delivery_type == 'delivery' else 0
            total_amount = subtotal + tax + delivery_fee
            
            # Create order data
            order_data = {
                'delivery_type': delivery_type,
                'payment_method': random.choice(['cash', 'card']),
                'special_instructions': random.choice([
                    '', 
                    'Extra cheese please',
                    'No onions',
                    'Please ring doorbell',
                    'Leave at door'
                ])
            }
            
            # Create order
            order = Order(
                order_id=order_id,
                customer_id=customer.customer_id,
                restaurant_id=restaurant.restaurant_id,
                address_id=address.address_id,
                delivery_type=order_data['delivery_type'],
                subtotal=subtotal,
                tax=tax,
                delivery_fee=delivery_fee,
                total_amount=total_amount,
                order_status='pending',
                payment_method=order_data['payment_method'],
                payment_status='pending',
                special_instructions=order_data['special_instructions']
            )
            
            db.session.add(order)
            
            results.append({
                'order_id': order_id,
                'customer': customer.name,
                'restaurant': restaurant.name,
                'total': f"${total_amount:.2f}",
                'status': 'created'
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(results)} test orders',
            'orders': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/simulate-order-flow/<order_id>', methods=['POST'])
@login_required
def simulate_order_flow(order_id):
    """Simulate order flow (update status step by step)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Administrator access required'}), 403
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # Define order flow
        status_flow = {
            'pending': 'confirmed',
            'confirmed': 'preparing',
            'preparing': 'ready',
            'ready': 'out_for_delivery' if order.delivery_type == 'delivery' else 'ready_for_pickup',
            'out_for_delivery': 'delivered',
            'ready_for_pickup': 'delivered'
        }
        
        current_status = order.order_status
        
        if current_status in status_flow:
            new_status = status_flow[current_status]
            order.order_status = new_status
            
            # Update timestamps
            now = datetime.utcnow()
            if new_status == 'confirmed':
                order.confirmed_at = now
            elif new_status == 'preparing':
                order.preparing_at = now
            elif new_status == 'ready':
                order.ready_at = now
            elif new_status == 'delivered':
                order.delivered_at = now
                order.payment_status = 'paid'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Order status updated from {current_status} to {new_status}',
                'new_status': new_status
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Cannot update from status: {current_status}'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/clear-test-data', methods=['POST'])
@login_required
def clear_test_data():
    """Clear all test orders (for cleanup)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Administrator access required'}), 403
    
    try:
        # Delete test orders and related data
        test_orders = Order.query.filter(Order.order_id.like('TEST-%')).all()
        
        for order in test_orders:
            # Delete order items
            OrderItem.query.filter_by(order_id=order.order_id).delete()
            # Delete order
            db.session.delete(order)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cleared {len(test_orders)} test orders'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/api/simulate-android-order', methods=['POST'])
def simulate_android_api():
    """Simulate Android app API request (no login required for testing)"""
    try:
        # This simulates what your Android app would send
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['customer_id', 'restaurant_id', 'items']):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Generate order ID
        order_id = generate_order_id()
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=data['customer_id'],
            restaurant_id=data['restaurant_id'],
            address_id=data.get('address_id'),
            delivery_type=data.get('delivery_type', 'delivery'),
            subtotal=data['subtotal'],
            tax=data.get('tax', 0),
            delivery_fee=data.get('delivery_fee', 0),
            total_amount=data['total_amount'],
            order_status='pending',
            payment_method=data.get('payment_method', 'cash'),
            payment_status='pending',
            special_instructions=data.get('special_instructions', '')
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        for item in data['items']:
            order_item = OrderItem(
                order_id=order.order_id,
                menu_item_id=item['menu_item_id'],
                quantity=item['quantity'],
                price=item['price'],
                special_instructions=item.get('special_instructions')
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Return response similar to what Android app expects
        return jsonify({
            'success': True,
            'order_id': order_id,
            'estimated_delivery': (datetime.utcnow() + timedelta(minutes=45)).isoformat(),
            'message': 'Order placed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Order failed: {str(e)}'
        }), 500

@test_bp.route('/test-api', methods=['GET'])
def test_api_endpoint():
    """Simple API endpoint for testing connectivity"""
    return jsonify({
        'status': 'online',
        'service': 'Mega Pizza Test API',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'create_order': '/test/api/simulate-android-order',
            'order_status': '/test/simulate-order-flow/<order_id>'
        }
    })
@test_bp.route('/android-simulator')
@login_required
def android_simulator():
    """Android app simulator page"""
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        # Get menu items for display
        menu_items = create_test_menu_items()
        
        # Get customers for the simulator
        customers = Customer.query.all()
        
        # Get restaurants
        restaurants = Restaurant.query.filter_by(is_active=True).all()
        
        return render_template('test/android_simulator.html',
                             menu_items=menu_items,
                             customers=customers,
                             restaurants=restaurants)
    except Exception as e:
        flash(f'Error loading Android simulator: {str(e)}', 'danger')
        return redirect(url_for('test.test_dashboard'))