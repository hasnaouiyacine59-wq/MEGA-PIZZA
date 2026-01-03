from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db
from .forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"DEBUG: Login route called. Method: {request.method}")
    print(f"DEBUG: Current user authenticated: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    print(f"DEBUG: Form created. Validate on submit: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        print(f"DEBUG: Form validated! Username: {form.username.data}")
        user = User.query.filter_by(username=form.username.data).first()
        print(f"DEBUG: User found: {user}")
        
        if user and user.verify_password(form.password.data) and user.is_active:
            print(f"DEBUG: Password verified. User active: {user.is_active}")
            login_user(user)
            flash('🎉 Login successful! Welcome back!', 'success')
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_driver():
                return redirect(url_for('driver.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('❌ Invalid username or password', 'danger')
            print(f"DEBUG: Login failed - user: {user}, verify: {user.verify_password(form.password.data) if user else 'No user'}")
    
    print(f"DEBUG: Rendering template. Form errors: {form.errors}")
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone.data,
            role='user',
            is_active=True
        )
        user.password = form.password.data
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)