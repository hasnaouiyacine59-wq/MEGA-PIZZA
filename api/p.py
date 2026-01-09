# test_order.py
import requests
import json
import time
import sys
import os

# API Base URL
BASE_URL = "http://localhost:5000/api"

def print_response(response, label):
    """Helper to print API responses"""
    print(f"\n{'='*60}")
    print(f"📤 {label}")
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
    except:
        print("Response:", response.text)
    return data if response.status_code == 200 else None

def register_customer():
    """Register a test customer"""
    print("\n👤 Registering test customer...")
    
    customer_data = {
        "username": "test_customer_" + str(int(time.time())),
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "full_name": "Test Customer",
        "phone": "1234567890",
        "address": "123 Test Street, Test City"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=customer_data)
    return print_response(response, "Customer Registration")

def login_customer(username, password):
    """Login and get JWT token"""
    print("\n🔐 Logging in customer...")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    data = print_response(response, "Customer Login")
    
    if data and data.get("success"):
        return data["data"]["access_token"]
    return None

def get_restaurants(token):
    """Get available restaurants"""
    print("\n🍕 Getting restaurants...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/restaurants", headers=headers)
    data = print_response(response, "Get Restaurants")
    
    if data and data.get("success") and data.get("data"):
        return data["data"]
    return []

def get_menu_items(token, restaurant_id):
    """Get menu items for a restaurant"""
    print(f"\n📋 Getting menu for restaurant {restaurant_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/restaurants/{restaurant_id}/menu", headers=headers)
    data = print_response(response, f"Menu for Restaurant {restaurant_id}")
    
    if data and data.get("success") and data.get("data"):
        return data["data"]
    return []

def create_order(token, restaurant_id, items):
    """Create a new order"""
    print("\n🛒 Creating order...")
    
    order_data = {
        "restaurant_id": restaurant_id,
        "items": items,
        "delivery_address": "123 Test Street, Test City",
        "delivery_instructions": "Ring the bell twice",
        "payment_method": "cash"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/orders", headers=headers, json=order_data)
    return print_response(response, "Create Order")

def get_user_orders(token):
    """Get user's order history"""
    print("\n📜 Getting order history...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/orders/my-orders", headers=headers)
    return print_response(response, "My Orders")

def test_complete_order_flow():
    """Test the complete order flow"""
    print("="*60)
    print("🚀 MEGA-PIZZA API ORDER TEST")
    print("="*60)
    
    # Step 1: Register a customer
    reg_result = register_customer()
    if not reg_result or not reg_result.get("success"):
        print("❌ Failed to register customer")
        return False
    
    customer = reg_result["data"]["user"]
    username = customer["username"]
    password = "TestPass123!"
    
    # Step 2: Login
    token = login_customer(username, password)
    if not token:
        print("❌ Failed to login")
        return False
    
    # Step 3: Get restaurants
    restaurants = get_restaurants(token)
    if not restaurants:
        print("❌ No restaurants found. Creating a test restaurant...")
        
        # If no restaurants, you might need to create one via admin first
        # For now, let's check if we can create a test order without restaurant
        print("⚠️  Skipping restaurant selection, using default ID 1")
        restaurant_id = 1
    else:
        restaurant_id = restaurants[0]["id"]
        print(f"✅ Selected restaurant: {restaurants[0]['name']} (ID: {restaurant_id})")
    
    # Step 4: Get menu items (skip if restaurant doesn't exist)
    try:
        menu_items = get_menu_items(token, restaurant_id)
        if menu_items:
            # Create order with actual menu items
            items = []
            for item in menu_items[:2]:  # Take first 2 items
                items.append({
                    "menu_item_id": item["id"],
                    "quantity": 1,
                    "special_instructions": f"Extra {item['name']} please"
                })
        else:
            # Create order with mock items
            print("⚠️  No menu items found, using mock data")
            items = [
                {
                    "menu_item_id": 1,
                    "quantity": 2,
                    "special_instructions": "Extra cheese please"
                },
                {
                    "menu_item_id": 2,
                    "quantity": 1,
                    "special_instructions": "No onions"
                }
            ]
    except:
        # If restaurant doesn't exist, use mock items
        print("⚠️  Restaurant endpoint error, using mock data")
        items = [
            {
                "menu_item_id": 1,
                "quantity": 2,
                "special_instructions": "Extra cheese please"
            }
        ]
    
    # Step 5: Create order
    order_result = create_order(token, restaurant_id, items)
    if not order_result or not order_result.get("success"):
        print("❌ Failed to create order")
        return False
    
    # Step 6: Get order history
    orders_result = get_user_orders(token)
    
    print("\n" + "="*60)
    print("✅ ORDER FLOW TEST COMPLETE!")
    print("="*60)
    
    return True

def quick_test_with_mock_data():
    """Quick test with mock data (no registration needed)"""
    print("="*60)
    print("⚡ QUICK ORDER TEST WITH MOCK DATA")
    print("="*60)
    
    # First, check if API is running
    try:
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"✅ API Health: {health_response.status_code}")
    except:
        print("❌ API is not running. Start server with: python run.py")
        return False
    
    # Try to create an order directly (this might fail if auth is required)
    order_data = {
        "restaurant_id": 1,
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 1,
                "special_instructions": "Test order from script"
            }
        ],
        "delivery_address": "123 Test Street",
        "payment_method": "cash"
    }
    
    print("\n🛒 Trying direct order creation...")
    response = requests.post(f"{BASE_URL}/orders", json=order_data)
    
    if response.status_code == 401:
        print("⚠️  Authentication required. Please run full test flow.")
        return False
    
    data = print_response(response, "Direct Order Creation")
    
    if data and data.get("success"):
        print("\n✅ Order created successfully!")
        print(f"Order ID: {data.get('data', {}).get('id', 'N/A')}")
        return True
    else:
        print("\n❌ Order creation failed")
        return False

def test_api_endpoints_directly():
    """Test API endpoints directly without authentication"""
    print("="*60)
    print("🔍 TESTING API ENDPOINTS")
    print("="*60)
    
    endpoints = [
        ("/", "Home page"),
        ("/health", "Health check"),
        ("/api", "API base"),
        ("/api/restaurants", "Restaurants list"),
        ("/api/menu", "Menu items"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=3)
            print(f"\n📡 {description}:")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Data keys: {list(data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"\n❌ {description}: Error - {e}")

if __name__ == "__main__":
    print("MEGA-PIZZA Order Testing Script")
    print("Choose test mode:")
    print("1. Complete order flow (register, login, order)")
    print("2. Quick test with mock data")
    print("3. Test API endpoints only")
    print("4. All tests")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    # Make sure server is running
    print("\n🔍 Checking if server is running...")
    try:
        requests.get("http://localhost:5000/health", timeout=2)
        print("✅ Server is running!")
    except:
        print("⚠️  Server is not running. Please start it with:")
        print("   python run.py")
        print("\nWould you like to start the server now? (y/n)")
        start_choice = input("> ").lower()
        if start_choice == 'y':
            print("Starting server in background...")
            import subprocess
            subprocess.Popen(["python", "run.py"])
            time.sleep(3)  # Wait for server to start
        else:
            print("Please start the server manually and try again.")
            sys.exit(1)
    
    if choice == "1":
        test_complete_order_flow()
    elif choice == "2":
        quick_test_with_mock_data()
    elif choice == "3":
        test_api_endpoints_directly()
    elif choice == "4":
        test_api_endpoints_directly()
        time.sleep(1)
        quick_test_with_mock_data()
        time.sleep(1)
        test_complete_order_flow()
    else:
        print("Invalid choice. Running complete order flow...")
        test_complete_order_flow()
    
    print("\n" + "="*60)
    print("🎯 Testing complete!")
    print("="*60)
