# /home/odyx/Desktop/09-01-2026-mega/MEGA-PIZZA/app/templates/test/test_order_quick.py

import requests
import sys

def quick_test():
    """Quick test of order API endpoints"""
    BASE_URL = "http://localhost:8000/api/v1"
    
    print("🧪 Quick Order API Test")
    print("="*50)
    
    # 1. Test health
    print("\n1. Testing Health Check:")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ API Healthy")
            print(f"   📊 Stats: {data['data']['statistics']}")
        else:
            print(f"   ❌ API Unhealthy")
    except:
        print("   ❌ Cannot connect to API")
    
    # 2. Test restaurants
    print("\n2. Testing Restaurants:")
    try:
        resp = requests.get(f"{BASE_URL}/restaurants", timeout=3)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            count = data['data']['count']
            print(f"   ✅ Found {count} restaurants")
            if count > 0:
                restaurant = data['data']['restaurants'][0]
                print(f"   🏪 First: {restaurant['name']} ({restaurant['restaurant_id']})")
        else:
            print(f"   ❌ Failed to get restaurants")
    except:
        print("   ❌ Error getting restaurants")
    
    # 3. Test login
    print("\n3. Testing Authentication:")
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "Admin@123"},
            timeout=3
        )
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            token = data['data']['access_token'][:30] + "..."
            print(f"   ✅ Login successful")
            print(f"   🔑 Token: {token}")
            
            # 4. Test protected endpoint
            print("\n4. Testing Protected Endpoint (Drivers):")
            headers = {"Authorization": f"Bearer {data['data']['access_token']}"}
            resp = requests.get(f"{BASE_URL}/drivers/available", headers=headers, timeout=3)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                drivers_data = resp.json()
                print(f"   ✅ Found {drivers_data['data']['count']} available drivers")
            else:
                print(f"   ⚠️  Drivers endpoint: {resp.status_code}")
        else:
            print(f"   ❌ Login failed")
    except:
        print("   ❌ Authentication test failed")
    
    print("\n" + "="*50)
    print("Quick test completed!")

if __name__ == "__main__":
    quick_test()
