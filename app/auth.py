from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt
from app.forms import LoginForm, RegistrationForm
from app.models import User, LoginAttempt
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_driver():
            return redirect(url_for('driver.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Log login attempt
        login_attempt = LoginAttempt(
            user_id=user.user_id if user else None,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=False
        )
        
        if user and user.verify_password(form.password.data) and user.is_active:
            # Successful login
            login_attempt.success = True
            db.session.add(login_attempt)
            
            login_user(user, remember=form.remember.data)
            user.update_last_login()
            
            flash('Login successful!', 'success')
            logging.info(f'User {user.username} logged in from {request.remote_addr}')
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_driver():
                return redirect(url_for('driver.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            # Failed login
            db.session.add(login_attempt)
            db.session.commit()
            flash('Invalid username or password', 'danger')
            logging.warning(f'Failed login attempt for username: {form.username.data}')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role=form.role.data,
            phone_number=form.phone_number.data,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        logging.info(f'New user registered: {form.username.data}')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))