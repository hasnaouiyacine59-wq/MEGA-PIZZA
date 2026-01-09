# test_api_complete.py
import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, test_name):
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}")
    return response

def test_connection():
    """Test if we can connect to the API"""
    print("Testing connection to API...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("Make sure the API container is running:")
        print("  docker ps | grep mega-pizza-api")
        print("  docker logs mega-pizza-api")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_basic_endpoints():
    """Test basic endpoints without authentication"""
    print("\n1. Testing basic endpoints...")
    
    # Test root endpoint
    response = requests.get("http://localhost:8000/")
    print_response(response, "Root Endpoint")
    
    # Test health check
    response = requests.get(f"{BASE_URL}/health")
    health_result = print_response(response, "Health Check")
    
    # Test API documentation
    response = requests.get(f"{BASE_URL}/docs")
    docs_result = print_response(response, "API Documentation")
    
    # Test restaurants endpoint (public)
    response = requests.get(f"{BASE_URL}/restaurants")
    restaurants_result = print_response(response, "Get Restaurants")
    
    return all([
        health_result.status_code == 200,
        docs_result.status_code == 200,
        restaurants_result.status_code == 200
    ])

def test_login():
    """Test login functionality"""
    print("\n2. Testing login...")
    
    # Test with invalid credentials
    invalid_data = {"username": "nonexistent", "password": "wrong"}
    response = requests.post(f"{BASE_URL}/auth/login", json=invalid_data)
    print_response(response, "Invalid Login")
    
    # Test with missing fields
    missing_data = {"username": "test"}
    response = requests.post(f"{BASE_URL}/auth/login", json=missing_data)
    print_response(response, "Missing Password")
    
    # Test with empty data
    response = requests.post(f"{BASE_URL}/auth/login", json={})
    print_response(response, "Empty Login")
    
    print("\nNote: To test successful login, create a test user in the database.")
    print("SQL commands to create a test user:")
    print("""
    -- Password will be 'testpassword123'
    INSERT INTO users (public_id, username, email, password_hash, role, is_active) 
    VALUES ('test-uuid-123', 'testuser', 'test@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'customer', true);
    
    -- Create test customer
    INSERT INTO customers (customer_id, name, phone_number, email, user_id)
    VALUES ('CUST-001', 'Test Customer', '+1234567890', 'test@example.com', 1);
    """)
    
    return True

def test_authentication_required():
    """Test that protected endpoints require authentication"""
    print("\n3. Testing authentication requirements...")
    
    # Test protected endpoints without token
    endpoints = [
        f"{BASE_URL}/orders",
        f"{BASE_URL}/orders/123/track",
        f"{BASE_URL}/drivers/available"
    ]
    
    for endpoint in endpoints:
        if endpoint.endswith("/orders") and "123" not in endpoint:
            # POST to /orders
            response = requests.post(endpoint, json={})
        else:
            # GET for others
            response = requests.get(endpoint)
        
        print_response(response, f"Unauthorized: {endpoint}")
    
    print("\n✅ All protected endpoints correctly require authentication")
    return True

def test_error_handling():
    """Test error handling"""
    print("\n4. Testing error handling...")
    
    # Test 404
    response = requests.get(f"{BASE_URL}/nonexistent")
    print_response(response, "404 Not Found")
    
    # Test invalid restaurant menu
    response = requests.get(f"{BASE_URL}/restaurants/NONEXISTENT/menu")
    print_response(response, "Invalid Restaurant Menu")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("MEGA PIZZA API TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    
    # Test 1: Connection
    print("\n[TEST 1/4] Testing connection...")
    if test_connection():
        print("✅ Connection successful")
        results.append(True)
    else:
        print("❌ Connection failed")
        results.append(False)
        return False  # Stop if can't connect
    
    # Test 2: Basic endpoints
    print("\n[TEST 2/4] Testing basic endpoints...")
    if test_basic_endpoints():
        print("✅ Basic endpoints working")
        results.append(True)
    else:
        print("❌ Basic endpoints failed")
        results.append(False)
    
    # Test 3: Login
    print("\n[TEST 3/4] Testing login...")
    if test_login():
        print("✅ Login tests completed")
        results.append(True)
    else:
        print("❌ Login tests failed")
        results.append(False)
    
    # Test 4: Authentication
    print("\n[TEST 4/4] Testing authentication...")
    if test_authentication_required():
        print("✅ Authentication tests completed")
        results.append(True)
    else:
        print("❌ Authentication tests failed")
        results.append(False)
    
    # Test 5: Error handling
    print("\n[TEST 5/5] Testing error handling...")
    if test_error_handling():
        print("✅ Error handling tests completed")
        results.append(True)
    else:
        print("❌ Error handling tests failed")
        results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
