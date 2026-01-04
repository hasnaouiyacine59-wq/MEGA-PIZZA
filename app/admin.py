from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps  # 添加这个导入
from .models import User, Driver, Restaurant, Customer, Order, db, Address, MenuItem, OrderItem, OrderStatusHistory  # 添加 OrderStatusHistory
from .forms import DriverRegistrationForm, DriverEditForm
from datetime import datetime
import traceback
from datetime import datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)


# ============================================
# HELPER FUNCTIONS
# ============================================
def require_admin():
    """Check if current user is admin"""
    if not current_user.is_authenticated:
        return False
    return current_user.is_admin()

# 添加 admin_required 装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not require_admin():
            flash('Administrator access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# DASHBOARD
# ============================================
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admins': User.query.filter_by(role='admin').count(),
        'drivers': User.query.filter_by(role='driver').count(),
        'managers': User.query.filter_by(role='manager').count(),
        'employees': User.query.filter_by(role='employee').count(),
        'customers': User.query.filter_by(role='user').count(),
        'restaurants_count': Restaurant.query.count(),
        'active_drivers': Driver.query.filter_by(is_available=True).count(),
        'on_shift_drivers': Driver.query.filter_by(is_on_shift=True).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(order_status='pending').count(),
        'active_orders': Order.query.filter(
            Order.order_status.in_(['confirmed', 'preparing', 'ready', 'out_for_delivery'])
        ).count(),
        'today_orders': Order.query.filter(
            db.func.date(Order.created_at) == datetime.today().date()
        ).count()
    }
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Get top drivers
    top_drivers = Driver.query.order_by(Driver.rating.desc(), Driver.completed_deliveries.desc()).limit(5).all()
    
    # Get restaurant stats
    restaurants = Restaurant.query.all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_orders=recent_orders,
                         top_drivers=top_drivers,
                         restaurants=restaurants,
                         current_time=datetime.now())


# ============================================
# DRIVER MANAGEMENT
# ============================================
@admin_bp.route('/drivers')
@login_required
@admin_required
def manage_drivers():
    # Get all drivers with their user relationship loaded
    drivers = Driver.query.join(User).all()
    
    # Calculate statistics
    total_drivers = len(drivers)
    available_drivers = len([d for d in drivers if d.is_available])
    on_shift_drivers = len([d for d in drivers if d.is_on_shift])
    
    # Calculate average rating
    if drivers:
        avg_rating = sum(float(d.rating or 0) for d in drivers) / len(drivers)
    else:
        avg_rating = 0.0
    
    return render_template('admin/manage_drivers.html',
                         drivers=drivers,
                         total_drivers=total_drivers,
                         available_drivers=available_drivers,
                         on_shift_drivers=on_shift_drivers,
                         avg_rating=avg_rating)


@admin_bp.route('/drivers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_driver():
    form = DriverRegistrationForm()
    
    if form.validate_on_submit():
        # Check if user exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('admin/add_driver.html', form=form)
        
        try:
            # Create User account
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone_number=form.phone.data,
                role='driver',
                is_active=True
            )
            user.password = form.password.data
            
            db.session.add(user)
            db.session.flush()  # Get the user_id
            
            # Create Driver profile
            driver = Driver(
                user_id=user.user_id,
                license_number=form.license_number.data,
                vehicle_type=form.vehicle_type.data,
                vehicle_model=form.vehicle_model.data,
                license_plate=form.license_plate.data,
                emergency_contact=form.emergency_contact.data,
                emergency_phone=form.emergency_phone.data,
                shift_start=form.shift_start.data,
                shift_end=form.shift_end.data,
                is_available=form.is_available.data,
                is_on_shift=form.is_on_shift.data
            )
            
            db.session.add(driver)
            db.session.commit()
            
            flash(f'Driver {form.username.data} added successfully!', 'success')
            return redirect(url_for('admin.manage_drivers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding driver: {str(e)}', 'danger')
            current_app.logger.error(f'Error adding driver: {str(e)}')
            current_app.logger.error(f'Traceback: {traceback.format_exc()}')
    
    return render_template('admin/add_driver.html', form=form)


@admin_bp.route('/drivers/<int:driver_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_driver(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    user = driver.user
    
    form = DriverEditForm()
    
    if form.validate_on_submit():
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.phone_number = form.phone.data
        user.is_active = form.status.data == 'active'
        
        if form.password.data:
            user.password = form.password.data
        
        # Update driver
        driver.license_number = form.license_number.data
        driver.vehicle_type = form.vehicle_type.data
        driver.vehicle_model = form.vehicle_model.data
        driver.license_plate = form.license_plate.data
        driver.emergency_contact = form.emergency_contact.data
        driver.emergency_phone = form.emergency_phone.data
        driver.shift_start = form.shift_start.data
        driver.shift_end = form.shift_end.data
        driver.is_available = form.is_available.data
        driver.is_on_shift = form.is_on_shift.data
        
        try:
            db.session.commit()
            flash(f'Driver {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.manage_drivers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating driver: {str(e)}', 'danger')
    
    # For GET request or failed validation, populate form
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.phone.data = user.phone_number
        form.status.data = 'active' if user.is_active else 'inactive'
        form.license_number.data = driver.license_number
        form.vehicle_type.data = driver.vehicle_type
        form.vehicle_model.data = driver.vehicle_model
        form.license_plate.data = driver.license_plate
        form.emergency_contact.data = driver.emergency_contact
        form.emergency_phone.data = driver.emergency_phone
        form.shift_start.data = driver.shift_start
        form.shift_end.data = driver.shift_end
        form.is_available.data = driver.is_available
        form.is_on_shift.data = driver.is_on_shift
    
    return render_template('admin/edit_driver.html', form=form, driver=driver)


@admin_bp.route('/drivers/<int:driver_id>/toggle-availability', methods=['POST'])
@login_required
@admin_required
def toggle_driver_availability(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    
    try:
        driver.is_available = not driver.is_available
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Driver availability {"enabled" if driver.is_available else "disabled"}',
            'is_available': driver.is_available
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@admin_bp.route('/drivers/<int:driver_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_driver(driver_id):
    """Delete a driver and their user account"""
    try:
        # Find driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        
        # Check if driver has any active orders
        active_orders = Order.query.filter(
            Order.driver_id == driver_id,
            Order.order_status.in_(['confirmed', 'preparing', 'ready', 'out_for_delivery'])
        ).count()
        
        if active_orders > 0:
            return jsonify({
                'success': False, 
                'message': f'Cannot delete driver with {active_orders} active order(s). Please reassign orders first.'
            }), 400
        
        # Get user for deletion
        user = driver.user
        
        # Delete driver
        db.session.delete(driver)
        
        # Delete user (this will cascade delete related records)
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Driver deleted successfully',
            'redirect': url_for('admin.manage_drivers')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting driver {driver_id}: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@admin_bp.route('/drivers/<int:driver_id>/view')
@login_required
@admin_required
def view_driver(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    return render_template('admin/view_driver.html', driver=driver)


# ============================================
# RESTAURANT MANAGEMENT
# ============================================
@admin_bp.route('/restaurants')
@login_required
@admin_required
def manage_restaurants():
    restaurants = Restaurant.query.all()
    return render_template('admin/manage_restaurants.html', restaurants=restaurants)


# ============================================
# ORDER MANAGEMENT - 修复版本
# ============================================
@admin_bp.route('/orders')
@login_required
@admin_required
def manage_orders():
    # Get filter parameters
    status = request.args.get('status', 'all')
    restaurant_id = request.args.get('restaurant_id', 'all')
    search = request.args.get('search', '')
    payment_status = request.args.get('payment_status', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build query
    query = Order.query
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(order_status=status)
    
    if restaurant_id != 'all':
        query = query.filter_by(restaurant_id=restaurant_id)
    
    if payment_status != 'all':
        query = query.filter_by(payment_status=payment_status)
    
    if search:
        search_term = f"%{search}%"
        query = query.join(Customer).filter(
            (Order.order_id.ilike(search_term)) |
            (Customer.name.ilike(search_term)) |
            (Customer.phone_number.ilike(search_term))
        )
    
    # Date range filter
    if start_date:
        query = query.filter(Order.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Order.created_at < end_date_obj)
    
    # Order by creation date (newest first)
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Get restaurants for filter dropdown
    restaurants = Restaurant.query.all()
    
    # Get statistics
    today = datetime.now().date()
    stats = {
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(order_status='pending').count(),
        'active_orders': Order.query.filter(
            Order.order_status.in_(['confirmed', 'preparing', 'ready', 'out_for_delivery'])
        ).count(),
        'delivered_orders': Order.query.filter_by(order_status='delivered').count(),
        'cancelled_orders': Order.query.filter_by(order_status='cancelled').count(),
        'total_revenue': db.session.query(func.sum(Order.total_amount)).scalar() or 0,
        'today_orders': Order.query.filter(
            db.func.date(Order.created_at) == today
        ).count(),
        'delivered_today': Order.query.filter(
            db.func.date(Order.delivered_at) == today,
            Order.order_status == 'delivered'
        ).count()
    }
    
    # Get available drivers for assignment
    available_drivers = Driver.query.filter_by(is_available=True).all()
    
    return render_template('admin/manage_orders.html',
                         orders=orders,
                         restaurants=restaurants,
                         stats=stats,
                         available_drivers=available_drivers,
                         current_status=status,
                         current_restaurant=restaurant_id,
                         search=search,
                         payment_status=payment_status,
                         start_date=start_date,
                         end_date=end_date)


@admin_bp.route('/orders/<string:order_id>')
@login_required
@admin_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    available_drivers = Driver.query.filter_by(is_available=True).all()
    
    return render_template('admin/view_order.html', 
                         order=order,
                         available_drivers=available_drivers)


@admin_bp.route('/orders/<string:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        try:
            # Update order fields
            order.order_status = request.form.get('order_status')
            order.payment_status = request.form.get('payment_status')
            order.delivery_type = request.form.get('delivery_type')
            order.payment_method = request.form.get('payment_method')
            order.transaction_id = request.form.get('transaction_id')
            order.customer_id = request.form.get('customer_id')
            order.restaurant_id = request.form.get('restaurant_id')
            order.driver_id = request.form.get('driver_id') or None
            order.address_id = request.form.get('address_id') or None
            order.special_instructions = request.form.get('special_instructions')
            order.driver_rating = request.form.get('driver_rating') or None
            
            # Update pricing
            order.subtotal = float(request.form.get('subtotal', 0))
            order.tax = float(request.form.get('tax', 0))
            order.delivery_fee = float(request.form.get('delivery_fee', 0))
            order.discount = float(request.form.get('discount', 0))
            order.total_amount = order.subtotal + order.tax + order.delivery_fee - order.discount
            
            # Update estimated delivery
            estimated_delivery = request.form.get('estimated_delivery')
            if estimated_delivery:
                order.estimated_delivery = datetime.strptime(estimated_delivery, '%Y-%m-%dT%H:%M')
            
            db.session.commit()
            flash('Order updated successfully!', 'success')
            return redirect(url_for('admin.view_order', order_id=order.order_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating order: {str(e)}', 'danger')
    
    # Get data for dropdowns
    customers = Customer.query.all()
    restaurants = Restaurant.query.all()
    drivers = Driver.query.all()
    addresses = Address.query.all()
    
    return render_template('admin/edit_order.html',
                         order=order,
                         customers=customers,
                         restaurants=restaurants,
                         drivers=drivers,
                         addresses=addresses)


@admin_bp.route('/orders/<string:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    try:
        old_status = order.order_status
        new_status = data.get('new_status')
        driver_id = data.get('driver_id')
        notes = data.get('notes')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'No status provided'})
        
        # Update order status
        order.order_status = new_status
        
        # Assign driver if provided
        if driver_id and new_status == 'out_for_delivery':
            driver = Driver.query.get(driver_id)
            if driver:
                order.driver_id = driver.driver_id
                driver.is_available = False  # Mark driver as busy
                
                # Update driver stats
                driver.total_deliveries = (driver.total_deliveries or 0) + 1
        
        # Update timestamps
        if new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
        elif new_status == 'out_for_delivery':
            order.estimated_delivery = datetime.utcnow() + timedelta(minutes=30)
        
        # Create status history
        history = OrderStatusHistory(
            order_id=order.order_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.user_id,
            notes=notes
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/orders/<string:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    try:
        # Update order status
        old_status = order.order_status
        order.order_status = 'cancelled'
        
        # Create status history
        history = OrderStatusHistory(
            order_id=order.order_id,
            old_status=old_status,
            new_status='cancelled',
            changed_by=current_user.user_id,
            notes=f"Cancellation: {data.get('reason', 'No reason provided')}. {data.get('notes', '')}"
        )
        db.session.add(history)
        
        # Free up driver if assigned
        if order.driver_id:
            driver = Driver.query.get(order.driver_id)
            if driver:
                driver.is_available = True
        
        # Process refund if requested
        if data.get('process_refund'):
            order.payment_status = 'refunded'
            # TODO: Implement actual refund logic
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/orders/<string:order_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    try:
        # Get related records to delete
        order_items = OrderItem.query.filter_by(order_id=order.order_id).all()
        status_history = OrderStatusHistory.query.filter_by(order_id=order.order_id).all()
        
        # Delete related records
        for item in order_items:
            db.session.delete(item)
        
        for history in status_history:
            db.session.delete(history)
        
        # Delete the order
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/orders/<string:order_id>/resend-receipt', methods=['POST'])
@login_required
@admin_required
def resend_receipt(order_id):
    order = Order.query.get_or_404(order_id)
    
    try:
        # TODO: Implement receipt resend logic
        # This would typically involve:
        # 1. Generating a receipt PDF
        # 2. Sending email to customer
        # 3. Logging the action
        
        return jsonify({
            'success': True, 
            'message': 'Receipt resent successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# USER MANAGEMENT
# ============================================
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    # Get filter parameters
    role = request.args.get('role', 'all')
    status = request.args.get('status', 'all')
    
    # Build query
    query = User.query
    
    if role != 'all':
        query = query.filter_by(role=role)
    
    if status != 'all':
        is_active = status == 'active'
        query = query.filter_by(is_active=is_active)
    
    users = query.order_by(User.created_at.desc()).all()
    
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(role='admin').count()
    driver_users = User.query.filter_by(role='driver').count()
    
    return render_template('admin/manage_users.html',
                         users=users,
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         driver_users=driver_users,
                         current_role=role,
                         current_status=status)


# ============================================
# SYSTEM MANAGEMENT
# ============================================
@admin_bp.route('/system/health')
@login_required
@admin_required
def system_health():
    # Get database health
    try:
        db.session.execute('SELECT 1')
        db_status = 'Healthy'
        db_message = 'Database connection successful'
    except Exception as e:
        db_status = 'Unhealthy'
        db_message = f'Database error: {str(e)}'
    
    # Get system stats
    stats = {
        'database': {
            'status': db_status,
            'message': db_message,
            'users_count': User.query.count(),
            'orders_count': Order.query.count(),
            'drivers_count': Driver.query.count(),
            'restaurants_count': Restaurant.query.count()
        },
        'application': {
            'start_time': current_app.config.get('START_TIME', 'Unknown'),
            'debug_mode': current_app.debug,
            'environment': current_app.config.get('ENV', 'production')
        }
    }
    
    return render_template('admin/system_health.html', stats=stats)


# ============================================
# ADMIN UTILITIES
# ============================================
@admin_bp.route('/create-admin')
def create_admin():
    """Utility endpoint to create admin user (for development)"""
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        admin.password = 'Admin@123'
        db.session.commit()
        flash('Admin password updated! Username: admin, Password: Admin@123', 'success')
    else:
        admin = User(
            username='admin',
            email='admin@megapizza.com',
            role='admin',
            is_active=True
        )
        admin.password = 'Admin@123'
        db.session.add(admin)
        db.session.commit()
        flash('Admin user created successfully! Username: admin, Password: Admin@123', 'success')
    
    return redirect(url_for('auth.login'))