from app import create_app, db
from app.models import User

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    with app.app_context():
        # Drop all tables first (WARNING: This deletes all data!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created!")
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("⚠️  No admin user found. Creating admin...")
            admin = User(
                username='admin',
                email='admin@megapizza.com',
                role='admin',
                is_active=True
            )
            admin.password = 'Admin@123'
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / Admin@123")
        else:
            print("✅ Admin user exists in database")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)