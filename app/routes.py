from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models import Order, Restaurant, Customer
from app import db

main_bp = Blueprint('main', __name__)

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_access_driver():
            flash('Driver access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_driver():
            return redirect(url_for('driver.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_driver():
        return redirect(url_for('driver.dashboard'))
    
    # Regular user dashboard
    customer = Customer.query.filter_by(user_id=current_user.user_id).first()
    orders = Order.query.filter_by(customer_id=customer.customer_id).order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('user/dashboard.html', orders=orders)

@main_bp.route('/driver/dashboard')
@login_required
@driver_required
def driver_dashboard():
    # Driver dashboard - show assigned orders
    assigned_orders = Order.query.filter_by(driver_id=current_user.user_id).order_by(Order.created_at.desc()).all()
    available_orders = Order.query.filter_by(order_status='ready', driver_id=None).order_by(Order.created_at.desc()).all()
    
    return render_template('driver/dashboard.html', 
                         assigned_orders=assigned_orders,
                         available_orders=available_orders)

@main_bp.route('/driver/orders/<string:order_id>/accept', methods=['POST'])
@login_required
@driver_required
def accept_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.driver_id:
        flash('This order has already been accepted by another driver.', 'warning')
    else:
        order.driver_id = current_user.user_id
        order.order_status = 'out_for_delivery'
        db.session.commit()
        flash(f'Order {order_id} accepted for delivery.', 'success')
    
    return redirect(url_for('main.driver_dashboard'))

@main_bp.route('/driver/orders/<string:order_id>/complete', methods=['POST'])
@login_required
@driver_required
def complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.driver_id != current_user.user_id:
        flash('You are not assigned to this order.', 'danger')
    else:
        order.order_status = 'delivered'
        order.delivered_at = db.func.current_timestamp()
        db.session.commit()
        flash(f'Order {order_id} marked as delivered.', 'success')
    
    return redirect(url_for('main.driver_dashboard'))