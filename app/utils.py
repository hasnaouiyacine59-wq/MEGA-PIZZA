from app import db
from app.models import User, Restaurant
import logging

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        admin = User(
            username='admin',
            email='admin@megapizza.com',
            password='Admin@123',  # Will be hashed by setter
            role='admin',
            phone_number='+1234567890',
            is_active=True
        )
        
        db.session.add(admin)
        
        # Ensure default restaurant exists
        restaurant = Restaurant.query.filter_by(restaurant_id='REST-001').first()
        if not restaurant:
            restaurant = Restaurant(
                restaurant_id='REST-001',
                name='Mega Pizza Headquarters',
                address='123 Pizza Street, Food City',
                phone='+1234567890',
                is_active=True
            )
            db.session.add(restaurant)
        
        db.session.commit()
        logging.info('Default admin user and restaurant created')