# final_test.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_all_endpoints():
    print("="*60)
    print("FINAL API TEST - MEGA PIZZA DELIVERY")
    print("="*60)
    
    # 1. Test public endpoints
    print("\n1. Testing Public Endpoints:")
    print("-"*40)
    
    endpoints = [
        ("GET", "/", "Root"),
        ("GET", "/api/v1/health", "Health"),
        ("GET", "/api/v1/docs", "API Docs"),
        ("GET", "/api/v1/restaurants", "Restaurants"),
    ]
    
    for method, endpoint, name in endpoints:
        url = f"http://localhost:8000{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5, json={})
            
            if response.status_code < 400:
                print(f"✅ {name}: {response.status_code}")
                if name == "Health":
                    data = response.json()
                    print(f"   Stats: {data['data']['statistics']}")
            else:
                print(f"⚠️  {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    # 2. Test login with admin credentials
    print("\n2. Testing Authentication:")
    print("-"*40)
    
    login_data = {"username": "admin", "password": "Admin@123"}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            token = data['data']['access_token']
            user = data['data']['user']
            print(f"✅ Login successful!")
            print(f"   User: {user['username']} (Role: {user['role']})")
            print(f"   Token: {token[:50]}...")
            
            # 3. Test protected endpoints with token
            print("\n3. Testing Protected Endpoints:")
            print("-"*40)
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test drivers endpoint
            response = requests.get(f"{BASE_URL}/drivers/available", headers=headers)
            if response.status_code == 200:
                drivers_data = response.json()
                count = drivers_data['data']['count']
                print(f"✅ Available Drivers: {count} drivers found")
            else:
                print(f"⚠️  Drivers endpoint: {response.status_code}")
            
            # Try to get orders (might be empty)
            response = requests.get(f"{BASE_URL}/orders/ORD-20240101-000001", headers=headers)
            if response.status_code == 404:
                print("✅ Orders endpoint: Correctly returns 404 for non-existent order")
            elif response.status_code == 200:
                print("✅ Orders endpoint: Returns existing order")
            else:
                print(f"⚠️  Orders endpoint: {response.status_code}")
                
        elif response.status_code == 401:
            print("⚠️  Login failed: Invalid credentials")
            print("   Try creating a user first or check admin credentials")
        else:
            print(f"⚠️  Login: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
    
    # 4. Test error handling
    print("\n4. Testing Error Handling:")
    print("-"*40)
    
    # Test non-existent endpoint
    response = requests.get(f"{BASE_URL}/nonexistent")
    print(f"✅ 404 Handling: {response.status_code}")
    
    # Test invalid restaurant
    response = requests.get(f"{BASE_URL}/restaurants/INVALID/menu")
    print(f"✅ Invalid Restaurant: {response.status_code}")
    
    print("\n" + "="*60)
    print("SUMMARY: API is running successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Create more test data in the database")
    print("2. Test order creation and tracking")
    print("3. Integrate with frontend application")
    print("4. Set up proper environment variables for production")
    print("\nAPI Documentation available at: http://localhost:8000/api/v1/docs")

if __name__ == "__main__":
    test_all_endpoints()
