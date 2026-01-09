# debug_database.py
import requests
import json

def test_database_connection():
    """Test if we can connect to the database"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing Database Connection")
    print("="*50)
    
    # Test 1: Check your existing test endpoint
    print("\n1. Testing database stats...")
    try:
        response = requests.get(f"{base_url}/test/api/database-stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Database stats:")
            for key, value in data.get('stats', {}).items():
                print(f"     {key}: {value}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Try to create an order with more debugging
    print("\n2. Creating order with debug info...")
    try:
        order_data = {
            "customer_id": "test_customer_001",
            "restaurant_id": 1,
            "items": [{"name": "Debug Pizza", "quantity": 1}],
            "debug": True
        }
        
        response = requests.post(
            f"{base_url}/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Order created!")
            print(f"   Order ID: {data.get('data', {}).get('order_id')}")
            print(f"   Database message: {data.get('data', {}).get('database', {}).get('message')}")
            
            # Print full response for debugging
            print(f"\n   Full response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def create_order_with_real_save():
    """Create an order that will actually save to database"""
    print("\n" + "="*50)
    print("💾 Creating Order with Real Database Save")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # First, check what customers exist
    print("\n📋 Checking existing customers...")
    try:
        response = requests.get(f"{base_url}/test/api/get-customers")
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            print(f"   Found {len(customers)} customers")
            if customers:
                for i, cust in enumerate(customers[:5]):  # Show first 5
                    print(f"   {i+1}. ID: {cust.get('customer_id')}, Name: {cust.get('name')}")
                customer_id = customers[0].get('customer_id')
            else:
                print("   No customers found. Using default.")
                customer_id = "test_customer_001"
        else:
            print("   Could not fetch customers")
            customer_id = "test_customer_001"
    except:
        customer_id = "test_customer_001"
    
    # Check restaurants
    print("\n🍕 Checking existing restaurants...")
    try:
        response = requests.get(f"{base_url}/api/restaurants")
        if response.status_code == 200:
            data = response.json()
            restaurants = data.get('data', [])
            print(f"   Found {len(restaurants)} restaurants")
            if restaurants:
                for i, rest in enumerate(restaurants):
                    print(f"   {i+1}. ID: {rest.get('id')}, Name: {rest.get('name')}")
                restaurant_id = restaurants[0].get('id')
            else:
                print("   No restaurants found. Using default.")
                restaurant_id = 1
        else:
            print("   Could not fetch restaurants")
            restaurant_id = 1
    except:
        restaurant_id = 1
    
    # Create order
    print(f"\n🛒 Creating order with:")
    print(f"   Customer ID: {customer_id}")
    print(f"   Restaurant ID: {restaurant_id}")
    
    order_data = {
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "items": [
            {"item_id": 1, "name": "Pepperoni Pizza", "quantity": 1, "price": 12.99},
            {"item_id": 2, "name": "Coke", "quantity": 2, "price": 2.99}
        ],
        "total": 18.97,
        "save_to_db": True,
        "special_instructions": "Please save this to database!"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Order created!")
            
            # Check database status
            db_info = data.get('data', {}).get('database', {})
            if db_info.get('saved'):
                print("🎉 SUCCESS: Order saved to database!")
                print(f"   Order ID: {data['data']['order_id']}")
                print(f"   Order Number: {data['data']['order_number']}")
                
                # Verify it's in the database
                print("\n🔍 Verifying in database...")
                order_id = data['data']['order_id']
                verify_response = requests.get(f"{base_url}/test/api/database-stats")
                if verify_response.status_code == 200:
                    stats = verify_response.json().get('stats', {})
                    print(f"   Total orders in DB: {stats.get('orders', 'N/A')}")
                    print(f"   Active orders: {stats.get('active_orders', 'N/A')}")
            else:
                print("⚠️  Order created but NOT saved to database")
                print(f"   Reason: {db_info.get('message', 'Unknown error')}")
            
            print(f"\n📋 Order details:")
            print(json.dumps(data['data'], indent=2))
            
        else:
            print(f"❌ Failed to create order: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def direct_database_insert():
    """Try to insert directly into database using your existing test endpoint"""
    print("\n" + "="*50)
    print("⚡ Direct Database Insert Test")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    print("\nUsing your existing Android simulator endpoint...")
    
    # Use the data format that your simulator expects
    simulator_data = {
        "customer_id": "test_customer_001",
        "restaurant_id": "1",
        "address_id": 1,
        "delivery_type": "delivery",
        "items": [
            {
                "item_id": 1,
                "quantity": 1,
                "price": 12.99,
                "name": "Test Pizza"
            }
        ],
        "special_instructions": "Direct database test",
        "payment_method": "cash"
    }
    
    try:
        response = requests.post(
            f"{base_url}/test/api/simulate-android-order",
            json=simulator_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Order created via simulator!")
                print(f"Order ID: {data.get('order_id')}")
                print(f"Status: {data.get('status')}")
                print(f"Total: ${data.get('total', 0)}")
            else:
                print(f"❌ Simulator failed: {data.get('message')}")
        else:
            print(f"❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("MEGA-PIZZA Database Debug Tool")
    print("="*50)
    
    # Check server
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            exit(1)
    except:
        print("❌ Server not running")
        exit(1)
    
    print("\nChoose debug option:")
    print("1. Test database connection")
    print("2. Create order with real save attempt")
    print("3. Use Android simulator endpoint (direct DB)")
    print("4. All tests")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_database_connection()
    elif choice == "2":
        create_order_with_real_save()
    elif choice == "3":
        direct_database_insert()
    elif choice == "4":
        test_database_connection()
        create_order_with_real_save()
        direct_database_insert()
    else:
        print("Invalid choice. Running all tests...")
        test_database_connection()
        create_order_with_real_save()
        direct_database_insert()
    
    print("\n" + "="*50)
    print("🔧 Next steps:")
    print("1. Check your database schema - make sure 'orders' table exists")
    print("2. Check table structure with: \\d orders (in psql)")
    print("3. Verify primary key and column names match your code")
    print("4. Check if you have a 'restaurants' table with restaurant_id=1")
    print("="*50)
