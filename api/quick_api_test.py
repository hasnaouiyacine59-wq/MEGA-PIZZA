# quick_api_test.py
import requests
import json

def test_api_structure():
    """Test the exact API structure"""
    print("🔍 Testing MEGA-PIZZA API Structure")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Test API v1 endpoints
    print("\n📋 API v1 Endpoints:")
    
    endpoints = [
        "/api/v1/",
        "/api/v1/docs",
        "/api/v1/health",
        "/api/v1/restaurants",
        "/api/v1/auth/login",
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"\n🔗 {endpoint}")
            if endpoint == "/api/v1/auth/login":
                # Test POST for login
                response = requests.post(url, json={"username": "test", "password": "test"}, timeout=3)
            else:
                response = requests.get(url, timeout=3)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "success" in data:
                        print(f"   Success: {data['success']}")
                    if "message" in data:
                        print(f"   Message: {data['message']}")
                    if endpoint == "/api/v1/restaurants" and "data" in data and "restaurants" in data["data"]:
                        print(f"   Restaurants count: {len(data['data']['restaurants'])}")
                        for i, r in enumerate(data['data']['restaurants'][:3]):  # Show first 3
                            print(f"   - {i+1}. {r.get('name', 'Unknown')} (ID: {r.get('restaurant_id', 'N/A')})")
                except:
                    print(f"   Response: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*50)
    print("📝 Order Creation Test")
    print("="*50)
    
    # Try to get restaurants first
    restaurants_url = base_url + "/api/v1/restaurants"
    response = requests.get(restaurants_url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data", {}).get("restaurants"):
            restaurants = data["data"]["restaurants"]
            if restaurants:
                restaurant = restaurants[0]
                print(f"\n🍕 Found restaurant: {restaurant['name']}")
                print(f"   ID: {restaurant['restaurant_id']}")
                
                # Try to create an order
                order_url = base_url + "/api/v1/orders"
                order_data = {
                    "customer_id": 1,  # Try customer ID 1
                    "restaurant_id": restaurant["restaurant_id"],
                    "items": [
                        {
                            "item_id": 1,
                            "quantity": 1
                        }
                    ],
                    "delivery_type": "delivery",
                    "payment_method": "cash",
                    "special_instructions": "Test from quick script"
                }
                
                print(f"\n🛒 Attempting to create order...")
                print(f"   Order data: {json.dumps(order_data, indent=2)}")
                
                response = requests.post(order_url, json=order_data)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            else:
                print("❌ No restaurants found. Add restaurants first.")
        else:
            print("❌ Could not get restaurants list.")
    else:
        print("❌ Failed to access restaurants endpoint.")

if __name__ == "__main__":
    test_api_structure()
