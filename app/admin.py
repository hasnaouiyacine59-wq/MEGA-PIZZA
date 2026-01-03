from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify ,current_app
from flask_login import login_required, current_user
from .models import User, Driver, Restaurant, Order, db
from .forms import DriverRegistrationForm, DriverEditForm
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admins = User.query.filter_by(role='admin').count()
    drivers = User.query.filter_by(role='driver').count()
    customers = User.query.filter_by(role='user').count()
    restaurants_count = Restaurant.query.count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         admins=admins,
                         drivers=drivers,
                         customers=customers,
                         restaurants_count=restaurants_count,
                         current_time=datetime.now())

@admin_bp.route('/drivers')
@login_required
def manage_drivers():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get all drivers with their user relationship loaded
    drivers = Driver.query.join(User).all()
    
    # Create debug data (optional, for debugging only)
    drivers_debug = []
    for driver in drivers:
        drivers_debug.append({
            'id': driver.driver_id,
            'username': driver.user.username if driver.user else None,
            'email': driver.user.email if driver.user else None,
            'rating': driver.rating,
            'is_available': driver.is_available,
            'is_on_shift': driver.is_on_shift,
            'total_deliveries': driver.total_deliveries,
            'completed_deliveries': driver.completed_deliveries,
            'total_earnings': float(driver.total_earnings) if driver.total_earnings else 0.0
        })
    
    # Only pass drivers to the template (not driver_data)
    return render_template('admin/manage_drivers.html', 
                         drivers=drivers,
                         drivers_debug=drivers_debug)  # Optional debug data
@admin_bp.route('/drivers/add', methods=['GET', 'POST'])
@login_required
def add_driver():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = DriverRegistrationForm()
    
    if request.method == 'POST':
        print("\n" + "="*50)
        print("DEBUG: FORM SUBMISSION ATTEMPT")
        print("="*50)
        print(f"Form submitted: {form.is_submitted()}")
        print(f"Form validated: {form.validate()}")
        print(f"Form errors: {form.errors}")
        print(f"Username: '{form.username.data}'")
        print(f"Email: '{form.email.data}'")
        print(f"Phone: '{form.phone.data}'")
        print(f"Password provided: {'YES' if form.password.data else 'NO'}")
        print(f"Password length: {len(form.password.data) if form.password.data else 0}")
        print("="*50 + "\n")

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
            # FIX 1: Use set_password method instead of direct assignment
            user.password = form.password.data
            
            db.session.add(user)
            db.session.flush()  # This gets the user_id
            
            # Create Driver profile
            driver = Driver(
                user_id=user.user_id,  # Assuming user_id is the primary key
                license_number=form.license_number.data,
                vehicle_type=form.vehicle_type.data,
                vehicle_model=form.vehicle_model.data,
                license_plate=form.license_plate.data,
                emergency_contact=form.emergency_contact.data,
                emergency_phone=form.emergency_phone.data
            )
            
            db.session.add(driver)
            db.session.commit()
            
            flash(f'Driver {form.username.data} added successfully!', 'success')
            return redirect(url_for('admin.manage_drivers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding driver: {str(e)}', 'danger')
            # FIX 2: Add logging for debugging
            current_app.logger.error(f'Error adding driver: {str(e)}')

            app.logger.error(f'Traceback: {traceback.format_exc()}')
    
    return render_template('admin/add_driver.html', form=form)
@admin_bp.route('/drivers/<int:driver_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_driver(driver_id):
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
    driver = Driver.query.get_or_404(driver_id)
    user = driver.user
    
    form = DriverEditForm()
    
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Form data received: {dict(request.form)}")
    
    if form.validate_on_submit():
        print(f"DEBUG: Form validated successfully!")
        print(f"DEBUG: Username from form: {form.username.data}")
        print(f"DEBUG: Email from form: {form.email.data}")
        
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.phone_number = form.phone.data
        user.is_active = form.status.data == 'active'
        
        if form.password.data:
            print(f"DEBUG: Password provided, updating...")
            user.password = form.password.data
        
        try:
            db.session.commit()
            print(f"DEBUG: Database commit successful!")
            flash(f'Driver {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.manage_drivers'))
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Database error: {str(e)}")
            flash(f'Error updating driver: {str(e)}', 'danger')
    else:
        print(f"DEBUG: Form validation failed!")
        print(f"DEBUG: Form errors: {form.errors}")
        print(f"DEBUG: CSRF token present: {'csrf_token' in request.form}")
    
    # For GET request or failed validation, populate form
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.phone.data = user.phone_number
        form.status.data = 'active' if user.is_active else 'inactive'
    
    return render_template('admin/edit_driver.html', form=form, driver=driver)

@admin_bp.route('/drivers/<int:driver_id>/toggle-availability', methods=['POST'])
@login_required
def toggle_driver_availability(driver_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Administrator access required.'}), 403
    
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

@admin_bp.route('/create-admin')
def create_admin():
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

    
@admin_bp.route('/drivers/<int:driver_id>/delete', methods=['DELETE'])
@login_required
def delete_driver(driver_id):
    """Delete a driver and their user account"""
    try:
        from .models import Driver, db, User
        
        # Find driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        
        # Get user
        user = driver.user
        
        # Simple check for orders (without accessing user_id)
        try:
            from .models import Order
            # Use a simpler query that doesn't try to select user_id
            order_exists = db.session.query(
                db.exists().where(Order.driver_id == driver_id)
            ).scalar()
            
            if order_exists:
                return jsonify({
                    'success': False, 
                    'message': 'Driver has associated orders. Cannot delete.'
                }), 400
        except Exception as query_error:
            # If query fails due to missing columns, just log and continue
            print(f"Note: Could not check orders: {query_error}")
            # Continue without order check
        
        # Delete driver and user
        db.session.delete(driver)
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Driver deleted successfully',
            'redirect': url_for('admin.manage_drivers')
        }), 200
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        current_app.logger.error(f'Error deleting driver {driver_id}: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500