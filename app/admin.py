from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Restaurant, Order, Customer
from app.forms import AdminCreateUserForm
import logging

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Administrator access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_restaurants': Restaurant.query.count(),
        'total_orders': Order.query.count(),
        'total_customers': Customer.query.count(),
        'active_drivers': User.query.filter_by(role='driver', is_active=True).count(),
        'pending_orders': Order.query.filter_by(order_status='pending').count()
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_users=recent_users,
                         recent_orders=recent_orders)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = AdminCreateUserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,  # Uses the setter to hash password
            role=form.role.data,
            phone_number=form.phone_number.data,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        logging.info(f'Admin {current_user.username} created user {user.username}')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/create_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating self
    if user.user_id == current_user.user_id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    logging.info(f'Admin {current_user.username} {status} user {user.username}')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.user_id == current_user.user_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted.', 'success')
    logging.info(f'Admin {current_user.username} deleted user {user.username}')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/restaurants')
@login_required
@admin_required
def manage_restaurants():
    restaurants = Restaurant.query.all()
    return render_template('admin/restaurants.html', restaurants=restaurants)

@admin_bp.route('/orders')
@login_required
@admin_required
def manage_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)