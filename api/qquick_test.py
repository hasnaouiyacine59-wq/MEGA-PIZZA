# quick_test.py (place in root directory)
#!/usr/bin/env python3
import sys
import os
import subprocess

def test_imports():
    """Test basic imports"""
    print("🧪 Testing imports...")
    try:
        from app import create_app, db
        print("✅ Imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test Flask app creation"""
    print("\n🧪 Testing Flask app creation...")
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully!")
        
        # Test app context
        with app.app_context():
            print("✅ App context works!")
            
        return app
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_routes(app):
    """Test basic routes"""
    print("\n🧪 Testing routes...")
    
    routes_to_test = [
        ('/', 'Home'),
        ('/health', 'Health Check'),
        ('/api', 'API Base'),
        ('/admin/dashboard', 'Admin Dashboard'),
        ('/auth/login', 'Login'),
    ]
    
    with app.test_client() as client:
        for route, name in routes_to_test:
            try:
                response = client.get(route, follow_redirects=True)
                print(f"  ✅ {name}: {response.status_code}")
            except Exception as e:
                print(f"  ❌ {name}: Error - {e}")

def test_models():
    """Test database models"""
    print("\n🧪 Testing database models...")
    try:
        from app.models import User
        print("✅ User model imports!")
        
        from app.models import Restaurant
        print("✅ Restaurant model imports!")
        
        from app.models import Order
        print("✅ Order model imports!")
        
        return True
    except Exception as e:
        print(f"❌ Model import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_server_test():
    """Start the server to see if it runs"""
    print("\n🚀 Testing server startup...")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    try:
        # This will start the server
        from app import create_app
        app = create_app()
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("MEGA-PIZZA Application Test Suite")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Failed at imports. Check your __init__.py")
        sys.exit(1)
    
    # Test 2: App creation
    app = test_app_creation()
    if not app:
        print("\n❌ Failed to create app")
        sys.exit(1)
    
    # Test 3: Models
    if not test_models():
        print("\n⚠️  Model imports had issues")
    
    # Test 4: Routes
    test_routes(app)
    
    # Test 5: Optional - Start server
    print("\n" + "=" * 50)
    choice = input("Do you want to start the server for manual testing? (y/n): ")
    if choice.lower() == 'y':
        run_server_test()
    else:
        print("\n✅ All basic tests passed!")
        print("You can now run: python run.py")
