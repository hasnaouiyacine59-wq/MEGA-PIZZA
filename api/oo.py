# test_order_api.py
import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5000"  # Note: port 5000, not 8000
    
    print("🚀 Testing MEGA-PIZZA API")
    print("="*50)
    
    # Test 1: API Home
    print("\n1. Testing API Home...")
    try:
        response = requests.get(f"{base_url}/api")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('service')}")
            print(f"   Endpoints: {', '.join(data.get('endpoints', {}).keys())}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Health check
    print("\n2. Testing API Health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success: {response.json().get('status')}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get restaurants
    print("\n3. Testing Restaurants...")
    try:
        response = requests.get(f"{base_url}/api/restaurants")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data.get('count', 0)} restaurants")
            if data.get('data'):
                for r in data['data'][:3]:  # Show first 3
                    print(f"     - {r.get('name')} (ID: {r.get('id')})")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Create order
    print("\n4. Creating Test Order...")
    try:
        order_data = {
            "customer_id": "test_customer_001",
            "restaurant_id": 1,
            "items": [
                {"item_id": 1, "name": "Pepperoni Pizza", "quantity": 1, "price": 12.99},
                {"item_id": 2, "name": "Garlic Bread", "quantity": 2, "price": 5.99}
            ],
            "total": 24.97,
            "special_instructions": "Extra cheese please!"
        }
        
        response = requests.post(
            f"{base_url}/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Order created successfully!")
            order_id = data.get('data', {}).get('order_id')
            print(f"   Order ID: {order_id}")
            print(f"   Database saved: {data.get('data', {}).get('database', {}).get('saved', False)}")
            
            # Test 5: Get the created order
            print("\n5. Getting Order Details...")
            if order_id:
                response = requests.get(f"{base_url}/api/orders/{order_id}")
                if response.status_code == 200:
                    order_data = response.json()
                    print(f"   ✅ Order status: {order_data.get('data', {}).get('status')}")
                    print(f"   Total: ${order_data.get('data', {}).get('total_amount')}")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def create_order_interactive():
    """Create an order interactively"""
    print("\n" + "="*50)
    print("🛒 Create a Test Order")
    print("="*50)
    
    customer_id = input("Customer ID (default: test_customer_001): ").strip() or "test_customer_001"
    restaurant_id = input("Restaurant ID (default: 1): ").strip() or "1"
    
    print("\nEnter items (type 'done' when finished):")
    items = []
    item_count = 1
    
    while True:
        print(f"\nItem {item_count}:")
        name = input("  Item name: ").strip()
        if name.lower() == 'done':
            break
        
        quantity = input("  Quantity (default: 1): ").strip() or "1"
        price = input("  Price (default: 9.99): ").strip() or "9.99"
        
        items.append({
            "item_id": item_count,
            "name": name,
            "quantity": int(quantity),
            "price": float(price)
        })
        
        item_count += 1
        if item_count > 5:  # Limit to 5 items
            print("Maximum 5 items reached.")
            break
    
    if not items:
        items = [{"item_id": 1, "name": "Test Pizza", "quantity": 1, "price": 12.99}]
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in items)
    
    order_data = {
        "customer_id": customer_id,
        "restaurant_id": int(restaurant_id),
        "items": items,
        "total": total,
        "special_instructions": "Test order from interactive script"
    }
    
    print(f"\n📦 Order Summary:")
    print(f"Customer: {customer_id}")
    print(f"Restaurant: {restaurant_id}")
    print(f"Items: {len(items)}")
    print(f"Total: ${total:.2f}")
    print(f"Data: {json.dumps(order_data, indent=2)}")
    
    confirm = input("\nCreate this order? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Order cancelled.")
        return
    
    try:
        response = requests.post(
            "http://localhost:5000/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print("\n✅ Order created successfully!")
            print(f"Order ID: {result['data']['order_id']}")
            print(f"Status: {result['data']['status']}")
            print(f"Database: {result['data']['database']['message']}")
            
            # Show the order
            order_id = result['data']['order_id']
            response = requests.get(f"http://localhost:5000/api/orders/{order_id}")
            if response.status_code == 200:
                order_details = response.json()
                print(f"\n📋 Order Details:")
                print(json.dumps(order_details['data'], indent=2))
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    print("MEGA-PIZZA API Order Testing")
    print("="*50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        if response.status_code == 200:
            print("✅ Server is running on port 5000")
        else:
            print("⚠️  Server response unexpected")
    except:
        print("❌ Server not running. Please start it with:")
        print("   python run.py")
        print("\nMake sure it's running on port 5000")
        return
    
    print("\nChoose option:")
    print("1. Run all API tests")
    print("2. Create interactive order")
    print("3. Test specific endpoint")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_api()
    elif choice == "2":
        create_order_interactive()
    elif choice == "3":
        endpoint = input("Enter endpoint (e.g., /api/health): ").strip()
        if endpoint:
            try:
                response = requests.get(f"http://localhost:5000{endpoint}")
                print(f"\nStatus: {response.status_code}")
                print(f"Response: {response.text[:500]}")
            except Exception as e:
                print(f"Error: {e}")
    else:
        print("Invalid choice. Running all tests...")
        test_api()
    
    print("\n" + "="*50)
    print("🎯 Testing Complete!")
    print("="*50)
    print("\nYou can also test in your browser:")
    print("  http://localhost:5000/api")
    print("  http://localhost:5000/api/health")
    print("  http://localhost:5000/api/restaurants")

if __name__ == "__main__":
    main()
