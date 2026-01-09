# test_order_fixed.py
import requests
import json

def create_order_with_correct_schema():
    """Create an order that matches the exact database schema"""
    print("🎯 Creating Order with Correct Schema")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Use actual data from your database
    # Customer ID must be string like 'CUST-001'
    # Restaurant ID must be string like '1' (not integer 1)
    
    order_data = {
        "customer_id": "CUST-001",  # String, not integer
        "restaurant_id": "1",       # String, not integer  
        "total": 35.50,
        "items": [
            {
                "item_id": "ITEM-001",  # String like your menu_items table
                "name": "Pepperoni Pizza",
                "quantity": 1,
                "price": 18.99
            },
            {
                "item_id": "ITEM-002",
                "name": "Garlic Bread",
                "quantity": 2,
                "price": 5.99
            },
            {
                "item_id": "ITEM-003", 
                "name": "Coke",
                "quantity": 2,
                "price": 2.99
            }
        ],
        "special_instructions": "Please ring the bell"
    }
    
    print("📦 Order Data:")
    print(json.dumps(order_data, indent=2))
    
    try:
        response = requests.post(
            f"{base_url}/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Order processed!")
            
            # Check if saved to database
            db_info = data.get('data', {}).get('database', {})
            if db_info.get('saved'):
                print("🎉 SUCCESS: Order saved to database!")
                print(f"   Order ID: {data['data']['order_id']}")
                
                # Show database details
                print(f"\n📋 Database Details:")
                details = db_info.get('details', {})
                for key, value in details.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️  Order NOT saved to database")
                print(f"   Reason: {db_info.get('message')}")
                
                # Show error details if available
                if 'details' in db_info:
                    print(f"\n🔍 Debug Details:")
                    details = db_info['details']
                    for key, value in details.items():
                        if key == 'error_details':
                            print(f"   Error traceback:\n{value[:500]}...")
                        else:
                            print(f"   {key}: {value}")
            
            print(f"\n📄 Full Response:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data, indent=2)) > 1000 else json.dumps(data, indent=2))
            
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def verify_database_state():
    """Check what's currently in the database"""
    print("\n" + "="*50)
    print("🔍 Verifying Database State")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Check current orders count
    try:
        response = requests.get(f"{base_url}/test/api/database-stats")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"📊 Current Database Stats:")
            print(f"   Total orders: {stats.get('orders', 'N/A')}")
            print(f"   Active orders: {stats.get('active_orders', 'N/A')}")
            print(f"   Customers: {stats.get('customers', 'N/A')}")
            print(f"   Restaurants: {stats.get('restaurants', 'N/A')}")
            
            # Show last few orders
            print(f"\n📋 Recent Orders:")
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host='localhost',
                    database='mega_pizza_db',
                    user='mega_pizza_admin',
                    password='SecurePass123!',
                    port=5432
                )
                cur = conn.cursor()
                cur.execute("""
                    SELECT order_id, customer_id, restaurant_id, order_status, total_amount, created_at
                    FROM orders 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent_orders = cur.fetchall()
                
                for i, order in enumerate(recent_orders, 1):
                    print(f"   {i}. {order[0]} - Customer: {order[1]}, Restaurant: {order[2]}")
                    print(f"      Status: {order[3]}, Total: ${order[4]}, Created: {order[5]}")
                
                cur.close()
                conn.close()
            except Exception as db_err:
                print(f"   Could not fetch recent orders: {db_err}")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def interactive_order_creator():
    """Interactive order creation with correct schema"""
    print("\n" + "="*50)
    print("🛒 Interactive Order Creator")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Get available customers
    print("\n📋 Available Customers:")
    try:
        response = requests.get(f"{base_url}/test/api/get-customers")
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            for i, cust in enumerate(customers, 1):
                print(f"   {i}. ID: {cust.get('customer_id')}, Name: {cust.get('name')}")
        
        customer_id = input("\nEnter Customer ID (e.g., CUST-001): ").strip()
        if not customer_id:
            customer_id = "CUST-001"
    except:
        customer_id = "CUST-001"
    
    # Get available restaurants  
    print("\n🍕 Available Restaurants:")
    try:
        response = requests.get(f"{base_url}/api/restaurants")
        if response.status_code == 200:
            data = response.json()
            restaurants = data.get('data', [])
            for i, rest in enumerate(restaurants, 1):
                print(f"   {i}. ID: {rest.get('id')}, Name: {rest.get('name')}")
        
        restaurant_id = input("\nEnter Restaurant ID (e.g., 1): ").strip()
        if not restaurant_id:
            restaurant_id = "1"
    except:
        restaurant_id = "1"
    
    # Get menu items for the restaurant
    print(f"\n📝 Creating order for Restaurant {restaurant_id}...")
    items = []
    item_count = 1
    
    # Try to get actual menu items
    try:
        response = requests.get(f"{base_url}/test/api/get-menu-items?restaurant_id={restaurant_id}")
        if response.status_code == 200:
            data = response.json()
            menu_items = data.get('items', [])
            
            print(f"Found {len(menu_items)} menu items:")
            for i, item in enumerate(menu_items[:10], 1):  # Show first 10
                print(f"   {i}. {item.get('name')} - ${item.get('price')} (ID: {item.get('item_id')})")
            
            print("\nEnter item IDs (type 'done' when finished):")
            while True:
                item_id = input(f"  Item {item_count} ID: ").strip()
                if item_id.lower() == 'done':
                    break
                
                # Find the item
                found_item = None
                for item in menu_items:
                    if str(item.get('item_id')) == item_id:
                        found_item = item
                        break
                
                if found_item:
                    quantity = input(f"  Quantity for {found_item.get('name')} (default: 1): ").strip() or "1"
                    items.append({
                        "item_id": found_item.get('item_id'),
                        "name": found_item.get('name'),
                        "quantity": int(quantity),
                        "price": float(found_item.get('price', 9.99))
                    })
                    item_count += 1
                else:
                    print(f"  ❌ Item ID {item_id} not found")
                    
                if item_count > 10:  # Limit
                    print("  Maximum 10 items reached.")
                    break
    except:
        print("Could not fetch menu items. Using manual entry.")
    
    # If no items from menu, ask for manual entry
    if not items:
        print("\nEnter items manually (type 'done' when finished):")
        while True:
            print(f"\nItem {item_count}:")
            name = input("  Item name: ").strip()
            if name.lower() == 'done':
                break
            
            item_id = input("  Item ID (default: AUTO): ").strip() or f"ITEM-{item_count:03d}"
            quantity = input("  Quantity (default: 1): ").strip() or "1"
            price = input("  Price (default: 9.99): ").strip() or "9.99"
            
            items.append({
                "item_id": item_id,
                "name": name,
                "quantity": int(quantity),
                "price": float(price)
            })
            
            item_count += 1
            if item_count > 10:
                print("Maximum 10 items reached.")
                break
    
    if not items:
        items = [{"item_id": "ITEM-001", "name": "Test Pizza", "quantity": 1, "price": 12.99}]
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in items)
    
    # Create order
    order_data = {
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "total": total,
        "items": items,
        "special_instructions": "Order from interactive creator"
    }
    
    print(f"\n📦 Order Summary:")
    print(f"Customer: {customer_id}")
    print(f"Restaurant: {restaurant_id}")
    print(f"Items: {len(items)}")
    print(f"Total: ${total:.2f}")
    
    confirm = input("\nCreate this order? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Order cancelled.")
        return
    
    create_order_with_data(order_data)

def create_order_with_data(order_data):
    """Helper to create order with given data"""
    base_url = "http://localhost:5000"
    
    try:
        response = requests.post(
            f"{base_url}/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            db_info = data.get('data', {}).get('database', {})
            
            if db_info.get('saved'):
                print("🎉 SUCCESS: Order saved to database!")
                print(f"Order ID: {data['data']['order_id']}")
                
                # Quick verification
                verify_database_state()
            else:
                print("⚠️  Order NOT saved to database")
                print(f"Reason: {db_info.get('message')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("MEGA-PIZZA Order Creation Tool")
    print("="*50)
    
    # Check server
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        if response.status_code != 200:
            print("❌ Server not responding")
            exit(1)
    except:
        print("❌ Server not running")
        exit(1)
    
    print("\nChoose option:")
    print("1. Create test order with fixed schema")
    print("2. Interactive order creation")
    print("3. Verify database state")
    print("4. All of the above")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        create_order_with_correct_schema()
    elif choice == "2":
        interactive_order_creator()
    elif choice == "3":
        verify_database_state()
    elif choice == "4":
        create_order_with_correct_schema()
        verify_database_state()
        interactive_order_creator()
    else:
        print("Invalid choice. Creating test order...")
        create_order_with_correct_schema()
    
    print("\n" + "="*50)
    print("✅ Done!")
    print("="*50)
