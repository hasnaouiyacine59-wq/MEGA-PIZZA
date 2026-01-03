# app/routes.py - ADD THIS AT THE TOP
# from flask import render_template, Blueprint, redirect, url_for, flash
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app

from flask_login import login_required, current_user
from app.models import User, Driver
from app.forms import DriverRegistrationForm
from app import db

from datetime import datetime
from flask import current_app  # Add this import

# Add main_bp for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
    
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_driver():
        return render_template('driver/dashboard.html')
    return render_template('dashboard.html')

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admins = User.query.filter_by(role='admin').count()
    drivers = User.query.filter_by(role='driver').count()
    customers = User.query.filter_by(role='user').count()
    restaurants_count = 0  # You can add Restaurant model count
    orders_count = 0  # You can add Order model count
    
    # Get current time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         admins=admins,
                         drivers=drivers,
                         customers=customers,
                         restaurants_count=restaurants_count,
                         orders_count=orders_count,
                         current_time=current_time)

@admin_bp.route('/drivers/add', methods=['GET', 'POST'])
@login_required
def add_driver():
    if not current_user.is_admin():
        flash('Administrator access required.', 'danger')
        return redirect(url_for('auth.login'))
    
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
            db.session.flush()
            
            # Create Driver profile - SET THE STATUS FIELDS!
            driver = Driver(
                user_id=user.user_id,
                license_number=form.license_number.data,
                vehicle_type=form.vehicle_type.data,
                vehicle_model=form.vehicle_model.data,
                license_plate=form.license_plate.data,
                emergency_contact=form.emergency_contact.data,
                emergency_phone=form.emergency_phone.data,
                
                # ADD THESE LINES:
                is_available=True,  # Default to available
                is_on_shift=False,   # Default to not on shift
                
                # Set other defaults if needed:
                rating=0.0,
                total_deliveries=0,
                completed_deliveries=0,
                failed_deliveries=0,
                total_earnings=0.0
            )
            
            db.session.add(driver)
            db.session.commit()
            
            flash(f'Driver {form.username.data} added successfully!', 'success')
            return redirect(url_for('admin.manage_drivers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding driver: {str(e)}', 'danger')
            current_app.logger.error(f'Error adding driver: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return render_template('admin/add_driver.html', form=form)