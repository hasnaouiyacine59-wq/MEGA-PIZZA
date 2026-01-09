# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Driver
from app.forms import DriverRegistrationForm
from app import db
from datetime import datetime
import json
import traceback
import psycopg2

# Create Blueprint for main routes
main_bp = Blueprint('main', __name__)

# ============================================
# MAIN ROUTES
# ============================================

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Check if user is admin - make sure you have is_admin() method in User model
        if hasattr(current_user, 'is_admin') and current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
    
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - redirects based on role"""
    # Check user role
    if hasattr(current_user, 'role'):
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'driver':
            return render_template('driver/dashboard.html')
        else:
            # For all other roles (user, employee, manager, etc.)
            return render_template('user/dashboard.html')
    else:
        # Fallback
        return render_template('user/dashboard.html')

# ============================================
# TEST ROUTES FOR DASHBOARD
# ============================================

@main_bp.route('/test/dashboard')
@login_required
def test_dashboard():
    """Test dashboard page"""
    return render_template('test/dashboard.html')

@main_bp.route('/test/android-simulator')
@login_required
def android_simulator():
    """Serve the Android simulator page"""
    return render_template('test/android_simulator.html')

@main_bp.route('/test/api/test-api')
@login_required
def test_api():
    """Simple API test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'timestamp': datetime.now().isoformat(),
        'database': 'Connected'
    })

@main_bp.route('/test/api/debug-db')
@login_required
def debug_db():
    """Debug database connection"""
    try:
        # Test 1: Check database engine
        engine_info = {
            'engine': str(db.engine),
            'driver': db.engine.driver,
            'url': str(db.engine.url),
            'pool_size': db.engine.pool.size(),
            'echo': db.engine.echo
        }
        
        # Test 2: List all tables
        tables = []
        try:
            with db.engine.connect() as conn:
                result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                tables = [row[0] for row in result]
        except Exception as e:
            tables_error = str(e)
        
        # Test 3: Check if specific tables exist
        tables_to_check = ['customers', 'restaurants', 'menu_items', 'orders', 'drivers']
        table_status = {}
        
        for table in tables_to_check:
            try:
                with db.engine.connect() as conn:
                    conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
                    table_status[table] = 'exists'
            except Exception as e:
                table_status[table] = f'error: {str(e)}'
        
        return jsonify({
            'engine_info': engine_info,
            'all_tables': tables,
            'table_status': table_status,
            'python_version': '3.x'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/test/api/simulate-android-order', methods=['POST'])
@login_required
def simulate_android_order():
    """Simulate an Android app order creation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_id', 'restaurant_id', 'address_id', 'delivery_type', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Convert IDs to correct types
        customer_id = str(data['customer_id'])
        restaurant_id = str(data['restaurant_id'])
        address_id = int(data['address_id'])
        
        # Generate order ID
        order_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}-DLVR"
        
        # Call stored procedure
        with db.engine.connect() as connection:
            # Convert items to JSON string
            items_json = json.dumps(data['items'])
            
            connection.execute(
                "CALL create_order(%s, %s, %s, %s, %s, %s::jsonb, %s, %s)",
                [
                    order_id,
                    customer_id,
                    restaurant_id,
                    address_id,
                    data['delivery_type'],
                    items_json,
                    data.get('special_instructions'),
                    data.get('payment_method', 'cash')
                ]
            )
            connection.commit()
            
            # Get the created order details
            result = connection.execute("""
                SELECT order_status, total_amount, created_at
                FROM orders 
                WHERE order_id = %s
            """, (order_id,))
            
            order = result.fetchone()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order_id,
            'status': order[0] if order else 'pending',
            'total': float(order[1]) if order and order[1] else 0,
            'created_at': order[2].isoformat() if order and order[2] else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Order failed: {str(e)}'
        }), 500

# ============================================
# DATABASE API ROUTES (DIRECT PSYCOPG2)
# ============================================

@main_bp.route('/test/api/test-connection')
def test_connection():
    """Simple test endpoint"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Database connection successful',
            'test_result': result[0]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Database connection failed'
        }), 500

@main_bp.route('/test/api/get-customers')
def get_customers():
    """Get all customers"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        sql = "SELECT customer_id, name, phone_number, email FROM customers ORDER BY customer_id"
        cur.execute(sql)
        customers = cur.fetchall()
        
        result = {
            'success': True,
            'customers': [
                {
                    'customer_id': row[0],
                    'name': row[1],
                    'phone_number': row[2],
                    'email': row[3]
                }
                for row in customers
            ]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'customers': []
        }), 500

@main_bp.route('/test/api/get-restaurants')
def get_restaurants():
    """Get all restaurants"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        sql = "SELECT restaurant_id, name, address, phone, is_open FROM restaurants WHERE is_active = true ORDER BY restaurant_id"
        cur.execute(sql)
        restaurants = cur.fetchall()
        
        result = {
            'success': True,
            'restaurants': [
                {
                    'restaurant_id': row[0],
                    'name': row[1],
                    'address': row[2],
                    'phone': row[3],
                    'is_open': row[4]
                }
                for row in restaurants
            ]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'restaurants': []
        }), 500

@main_bp.route('/test/api/get-addresses')
def get_addresses():
    """Get addresses for a customer"""
    customer_id = request.args.get('customer_id')
    
    if not customer_id:
        return jsonify({'success': False, 'error': 'Customer ID required', 'addresses': []}), 400
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        sql = "SELECT address_id, street, city, state, postal_code, country, is_default FROM addresses WHERE customer_id = %s ORDER BY is_default DESC, created_at DESC"
        cur.execute(sql, (customer_id,))
        addresses = cur.fetchall()
        
        result = {
            'success': True,
            'addresses': [
                {
                    'address_id': row[0],
                    'street': row[1],
                    'city': row[2],
                    'state': row[3],
                    'postal_code': row[4],
                    'country': row[5],
                    'is_default': row[6]
                }
                for row in addresses
            ]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'addresses': []
        }), 500

@main_bp.route('/test/api/get-menu-items')
def get_menu_items():
    """Get menu items for a restaurant"""
    restaurant_id = request.args.get('restaurant_id')
    
    if not restaurant_id:
        return jsonify({'success': False, 'error': 'Restaurant ID required', 'items': []}), 400
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        sql = "SELECT item_id, name, description, price, category, is_available FROM menu_items WHERE restaurant_id = %s ORDER BY category, name"
        cur.execute(sql, (restaurant_id,))
        items = cur.fetchall()
        
        result = {
            'success': True,
            'items': [
                {
                    'item_id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'price': float(row[3]),
                    'category': row[4] or 'Uncategorized',
                    'is_available': row[5]
                }
                for row in items
            ]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500

@main_bp.route('/test/api/database-stats')
def database_stats():
    """Get database statistics"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        stats = {}
        
        # Get counts
        tables = ['restaurants', 'customers', 'menu_items', 'orders', 'drivers', 'addresses']
        for table in tables:
            sql = f"SELECT COUNT(*) FROM {table}"
            cur.execute(sql)
            stats[table] = cur.fetchone()[0]
        
        # Get active orders count
        sql = "SELECT COUNT(*) FROM orders WHERE order_status NOT IN ('delivered', 'cancelled')"
        cur.execute(sql)
        stats['active_orders'] = cur.fetchone()[0]
        
        # Get available drivers count
        sql = "SELECT COUNT(*) FROM drivers WHERE is_available = true AND is_on_shift = true"
        cur.execute(sql)
        stats['available_drivers'] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {}
        }), 500

# ============================================
# ADDITIONAL HELPER ROUTES
# ============================================

@main_bp.route('/test/api/get-customers-alchemy')
@login_required
def get_customers_alchemy():
    """Get list of customers for the simulator"""
    try:
        with db.engine.connect() as connection:
            result = connection.execute("""
                SELECT customer_id, name, phone_number, email 
                FROM customers 
                ORDER BY customer_id
            """)
            customers = []
            for row in result:
                customers.append({
                    'customer_id': row[0],
                    'name': row[1],
                    'phone_number': row[2],
                    'email': row[3]
                })
            
            return jsonify({'customers': customers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/test/api/get-restaurants-alchemy')
@login_required
def get_restaurants_alchemy():
    """Get list of restaurants for the simulator"""
    try:
        with db.engine.connect() as connection:
            result = connection.execute("""
                SELECT restaurant_id, name, address, phone, is_open, delivery_radius
                FROM restaurants 
                WHERE is_active = true
                ORDER BY name
            """)
            restaurants = []
            for row in result:
                restaurants.append({
                    'restaurant_id': row[0],
                    'name': row[1],
                    'address': row[2],
                    'phone': row[3],
                    'is_open': row[4],
                    'delivery_radius': row[5]
                })
            
            return jsonify({'restaurants': restaurants})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/test/api/get-addresses-alchemy')
@login_required
def get_addresses_alchemy():
    """Get addresses for a customer"""
    customer_id = request.args.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'customer_id required'}), 400
    
    try:
        with db.engine.connect() as connection:
            result = connection.execute("""
                SELECT address_id, street, city, state, postal_code, is_default
                FROM addresses 
                WHERE customer_id = %s
                ORDER BY is_default DESC, created_at DESC
            """, (customer_id,))
            
            addresses = []
            for row in result:
                addresses.append({
                    'address_id': row[0],
                    'street': row[1],
                    'city': row[2],
                    'state': row[3],
                    'postal_code': row[4],
                    'is_default': row[5]
                })
            
            return jsonify({'addresses': addresses})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/test/api/get-menu-items-alchemy')
@login_required
def get_menu_items_alchemy():
    """Get menu items for a restaurant"""
    restaurant_id = request.args.get('restaurant_id')
    if not restaurant_id:
        return jsonify({'error': 'restaurant_id required'}), 400
    
    try:
        with db.engine.connect() as connection:
            result = connection.execute("""
                SELECT item_id, name, description, price, category, is_available, image_url
                FROM menu_items 
                WHERE restaurant_id = %s AND is_available = true
                ORDER BY category, name
            """, (restaurant_id,))
            
            items = []
            for row in result:
                items.append({
                    'item_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': float(row[3]),
                    'category': row[4],
                    'is_available': row[5],
                    'image_url': row[6]
                })
            
            return jsonify({'items': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/test/api/database-stats-alchemy')
@login_required
def database_stats_alchemy():
    """Get database statistics"""
    try:
        with db.engine.connect() as connection:
            stats = {}
            
            # Count restaurants
            result = connection.execute("SELECT COUNT(*) FROM restaurants")
            stats['restaurants'] = result.scalar()
            
            # Count customers
            result = connection.execute("SELECT COUNT(*) FROM customers")
            stats['customers'] = result.scalar()
            
            # Count menu items
            result = connection.execute("SELECT COUNT(*) FROM menu_items WHERE is_available = true")
            stats['menu_items'] = result.scalar()
            
            # Count orders
            result = connection.execute("SELECT COUNT(*) FROM orders")
            stats['orders'] = result.scalar()
            
            # Count active orders
            result = connection.execute("""
                SELECT COUNT(*) FROM orders 
                WHERE order_status NOT IN ('delivered', 'cancelled')
            """)
            stats['active_orders'] = result.scalar()
            
            # Count available drivers
            result = connection.execute("""
                SELECT COUNT(*) FROM drivers 
                WHERE is_available = true AND is_on_shift = true
            """)
            stats['available_drivers'] = result.scalar()
            
            return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500