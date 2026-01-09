# test_api_orders.py
import requests
import json
import time
import sys

# API Base URL - Note: Your API uses /api/v1 prefix
BASE_URL = "http://localhost:5000/api/v1"

def print_response(response, label):
    """Helper to print API responses"""
    print(f"\n{'='*60}")
    print(f"📤 {label}")
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text[:200]}")
    else:
        try:
            data = response.json()
            print("Response:", json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data, indent=2)) > 500 else json.dumps(data, indent=2))
            return data
        except:
            print("Response:", response.text[:200])
    return None

def test_api_endpoints():
    """Test all available API endpoints"""
    print("🔍 Testing API Endpoints...")
    
    endpoints = [
        ("/", "API Home"),
        ("/docs", "API Documentation"),
        ("/health", "Health Check"),
        ("/restaurants", "Get Restaurants"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"\n✅ {description}: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Data keys: {list(data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"\n❌ {description}: Error - {e}")

def create_test_order_with_existing_user():
    """Create a test order using an existing test user"""
    print("\n" + "="*60)
    print("🚀 Creating Test Order")
    print("="*60)
    
    # Step 1: First, let's see what restaurants are available
    print("\n🍕 Getting restaurants...")
    response = requests.get(f"{BASE_URL}/restaurants")
    data = print_response(response, "Get Restaurants")
    
    if not data or not data.get('success'):
        print("❌ Failed to get restaurants")
        return False
    
    restaurants = data.get('data', {}).get('restaurants', [])
    if not restaurants:
        print("❌ No restaurants available. Please add restaurants first.")
        return False
    
    restaurant = restaurants[0]
    restaurant_id = restaurant['restaurant_id']
    print(f"✅ Selected restaurant: {restaurant['name']} (ID: {restaurant_id})")
    
    # Step 2: Get restaurant menu
    print(f"\n📋 Getting menu for restaurant {restaurant_id}...")
    response = requests.get(f"{BASE_URL}/restaurants/{restaurant_id}/menu")
    menu_data = print_response(response, f"Restaurant {restaurant_id} Menu")
    
    if not menu_data or not menu_data.get('success'):
        print("⚠️  Could not get menu. Creating order with mock data...")
        menu_items = []
    else:
        menu_items = menu_data.get('data', {}).get('menu_items', [])
    
    # Step 3: Prepare order data
    # For testing, we need to use an existing customer_id
    # Check if there's a test customer in your database
    
    # Try to login first to get a token
    print("\n🔐 Trying to login with test credentials...")
    login_data = {
        "username": "test",  # Try common test username
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    login_result = print_response(response, "Login")
    
    if not login_result or not login_result.get('success'):
        print("⚠️  Login failed. Creating order without authentication might not work.")
        token = None
        customer_id = 1  # Try default customer ID
    else:
        token = login_result.get('data', {}).get('access_token')
        # Extract user/customer info from login response
        user_data = login_result.get('data', {}).get('user', {})
        customer_id = user_data.get('user_id')  # Adjust based on your API response
    
    # Step 4: Prepare order items
    if menu_items:
        # Use actual menu items
        items = []
        for item in menu_items[:2]:  # Take first 2 items
            items.append({
                "item_id": item['item_id'],
                "quantity": 1
            })
    else:
        # Use mock items
        print("⚠️  Using mock menu items")
        items = [
            {
                "item_id": 1,
                "quantity": 2
            },
            {
                "item_id": 2,
                "quantity": 1
            }
        ]
    
    # Step 5: Create order
    order_data = {
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "items": items,
        "delivery_type": "delivery",
        "payment_method": "cash",
        "special_instructions": "Test order from API script"
    }
    
    print(f"\n🛒 Creating order for customer {customer_id}...")
    print(f"Order data: {json.dumps(order_data, indent=2)}")
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.post(f"{BASE_URL}/orders", 
                           json=order_data, 
                           headers=headers)
    
    order_result = print_response(response, "Create Order")
    
    if order_result and order_result.get('success'):
        order_id = order_result.get('data', {}).get('order_id')
        print(f"\n✅ Order created successfully!")
        print(f"Order ID: {order_id}")
        
        # Step 6: Get order details
        if token and order_id:
            print(f"\n📋 Getting order details...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=headers)
            order_details = print_response(response, "Order Details")
        
        return True
    else:
        print("\n❌ Failed to create order")
        return False

def create_direct_test_order():
    """Try to create a test order directly without auth"""
    print("\n" + "="*60)
    print("⚡ Direct Order Test (No Auth)")
    print("="*60)
    
    # First get restaurants
    response = requests.get(f"{BASE_URL}/restaurants")
    restaurants_data = response.json() if response.status_code == 200 else None
    
    if not restaurants_data or not restaurants_data.get('success'):
        print("❌ Could not get restaurants")
        return False
    
    restaurants = restaurants_data.get('data', {}).get('restaurants', [])
    if not restaurants:
        print("❌ No restaurants found")
        return False
    
    restaurant = restaurants[0]
    restaurant_id = restaurant['restaurant_id']
    
    # Create order with mock data
    order_data = {
        "customer_id": 1,  # Try customer ID 1
        "restaurant_id": restaurant_id,
        "items": [
            {
                "item_id": 1,
                "quantity": 1
            }
        ],
        "delivery_type": "delivery",
        "payment_method": "cash",
        "special_instructions": "Direct test order"
    }
    
    print(f"\n🛒 Creating direct order...")
    print(f"Data: {json.dumps(order_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/orders", json=order_data)
    
    if response.status_code == 201 or response.status_code == 200:
        result = response.json()
        print(f"\n✅ Order created! Response: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"\n❌ Failed to create order: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def setup_test_data():
    """Setup test data if needed"""
    print("\n" + "="*60)
    print("🔧 Setup Test Data")
    print("="*60)
    
    # Try to create a test user via admin interface or directly in DB
    print("To create test orders, you need:")
    print("1. At least one restaurant in the database")
    print("2. At least one menu item for that restaurant")
    print("3. At least one customer/user account")
    
    # Check current status
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health_data = response.json()
        print(f"\n📊 Current System Status:")
        print(f"   Total Orders: {health_data.get('data', {}).get('statistics', {}).get('total_orders', 0)}")
        print(f"   Active Orders: {health_data.get('data', {}).get('statistics', {}).get('active_orders', 0)}")
        print(f"   Available Drivers: {health_data.get('data', {}).get('statistics', {}).get('available_drivers', 0)}")

def main():
    print("="*60)
    print("MEGA-PIZZA API ORDER TESTER")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        print("✅ Server is running!")
    except:
        print("❌ Server is not running. Please start it with:")
        print("   cd /home/odyx/Desktop/09-01-2026-mega/MEGA-PIZZA")
        print("   python run.py")
        print("\nOr if you're running the API separately:")
        print("   cd /home/odyx/Desktop/09-01-2026-mega/MEGA-PIZZA/api")
        print("   python run.py")
        return
    
    print("\nChoose test option:")
    print("1. Test API endpoints only")
    print("2. Try to create order with existing user")
    print("3. Try direct order creation (no auth)")
    print("4. Setup guidance")
    print("5. Full test sequence")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        test_api_endpoints()
    elif choice == "2":
        create_test_order_with_existing_user()
    elif choice == "3":
        create_direct_test_order()
    elif choice == "4":
        setup_test_data()
    elif choice == "5":
        test_api_endpoints()
        time.sleep(1)
        create_test_order_with_existing_user()
        time.sleep(1)
        create_direct_test_order()
    else:
        print("Invalid choice. Running full test...")
        test_api_endpoints()
        create_test_order_with_existing_user()
    
    print("\n" + "="*60)
    print("🎯 Testing Complete!")
    print("="*60)
    
    print("\n📝 Next steps:")
    print("1. If orders fail due to authentication:")
    print("   - Create a test user in your admin panel")
    print("   - Or modify the create_order endpoint to accept orders without auth for testing")
    print("")
    print("2. If orders fail due to missing data:")
    print("   - Make sure you have at least one restaurant")
    print("   - Add menu items to that restaurant")
    print("   - Ensure you have customer accounts")

if __name__ == "__main__":
    main()
