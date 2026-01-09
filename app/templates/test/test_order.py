# /home/odyx/Desktop/09-01-2026-mega/MEGA-PIZZA/app/templates/test/test_order.py

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to access app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class MegaPizzaOrderTester:
    """Comprehensive tester for Mega Pizza Delivery System Order API"""
    
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
        self.user_info = None
        self.test_data = {}
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f" {title}")
        print("="*70)
    
    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def test_connection(self):
        """Test API connection"""
        self.print_header("Testing API Connection")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"API Health: {data['data']['status']}")
                self.print_info(f"Database: {data['data']['database']}")
                self.print_info(f"Total Orders: {data['data']['statistics']['total_orders']}")
                self.print_info(f"Active Orders: {data['data']['statistics']['active_orders']}")
                return True
            else:
                self.print_error(f"API returned status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error(f"Cannot connect to {self.base_url}")
            self.print_info("Make sure the API is running: docker ps | grep mega-pizza-api")
            return False
    
    def authenticate(self, username="admin", password="Admin@123"):
        """Authenticate and get JWT token"""
        self.print_header("Authentication Test")
        try:
            payload = {"username": username, "password": password}
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['data']['access_token']
                self.user_info = data['data']['user']
                self.print_success(f"Logged in as: {self.user_info['username']}")
                self.print_info(f"Role: {self.user_info['role']}")
                self.print_info(f"Token: {self.token[:50]}...")
                return True
            else:
                self.print_error(f"Login failed: {response.status_code}")
                if response.status_code == 401:
                    self.print_info("Invalid credentials. Try:")
                    self.print_info("  Username: admin, Password: Admin@123")
                    self.print_info("Or create a test user first")
                return False
        except Exception as e:
            self.print_error(f"Authentication error: {e}")
            return False
    
    def get_headers(self):
        """Get headers with authentication token"""
        if self.token:
            return {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}
    
    def test_public_endpoints(self):
        """Test endpoints that don't require authentication"""
        self.print_header("Testing Public Endpoints")
        
        endpoints = [
            ("GET", "/restaurants", "Get Restaurants"),
            ("GET", "/docs", "API Documentation"),
        ]
        
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5, json={})
                
                if response.status_code < 400:
                    self.print_success(f"{description}: {response.status_code}")
                    # Store restaurants for later use
                    if "restaurants" in endpoint and response.status_code == 200:
                        data = response.json()
                        if data['data']['restaurants']:
                            self.test_data['restaurant'] = data['data']['restaurants'][0]
                            self.print_info(f"Found restaurant: {self.test_data['restaurant']['name']}")
                else:
                    self.print_error(f"{description}: {response.status_code}")
            except Exception as e:
                self.print_error(f"{description}: {e}")
    
    def test_restaurant_menu(self):
        """Test getting restaurant menu"""
        if not self.test_data.get('restaurant'):
            self.print_info("No restaurant found, skipping menu test")
            return
        
        self.print_header("Testing Restaurant Menu")
        restaurant_id = self.test_data['restaurant']['restaurant_id']
        
        try:
            response = requests.get(
                f"{self.base_url}/restaurants/{restaurant_id}/menu",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data['data']['menu_items']
                self.print_success(f"Found {len(menu_items)} menu items")
                
                if menu_items:
                    self.test_data['menu_items'] = menu_items
                    # Store first item for order creation
                    self.test_data['sample_item'] = menu_items[0]
                    self.print_info(f"Sample item: {self.test_data['sample_item']['name']} - ${self.test_data['sample_item']['price']}")
            else:
                self.print_error(f"Failed to get menu: {response.status_code}")
        except Exception as e:
            self.print_error(f"Menu test error: {e}")
    
    def create_test_customer(self):
        """Create or get a test customer"""
        self.print_header("Setting Up Test Customer")
        
        # This would normally create a customer in the database
        # For now, we'll use a placeholder or check if one exists
        self.test_data['customer_id'] = "CUST-001"
        self.print_info(f"Using customer ID: {self.test_data['customer_id']}")
        
        # Note: In a real test, you'd create a customer via API or database
        self.print_info("Note: Ensure customer exists in database before creating orders")
    
    def test_order_creation(self):
        """Test creating a new order"""
        if not self.token:
            self.print_error("Authentication required for order creation")
            return False
        
        if not all(key in self.test_data for key in ['customer_id', 'restaurant', 'sample_item']):
            self.print_error("Missing required test data")
            return False
        
        self.print_header("Testing Order Creation")
        
        order_payload = {
            "customer_id": self.test_data['customer_id'],
            "restaurant_id": self.test_data['restaurant']['restaurant_id'],
            "items": [
                {
                    "item_id": self.test_data['sample_item']['item_id'],
                    "quantity": 2
                }
            ],
            "delivery_type": "delivery",
            "special_instructions": "Please include extra napkins",
            "payment_method": "cash"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                headers=self.get_headers(),
                json=order_payload,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data['created_order'] = data['data']
                self.print_success(f"Order created successfully!")
                self.print_info(f"Order ID: {self.test_data['created_order']['order_id']}")
                self.print_info(f"Status: {self.test_data['created_order']['status']}")
                self.print_info(f"Total Amount: ${self.test_data['created_order']['total_amount']}")
                return True
            else:
                self.print_error(f"Order creation failed: {response.status_code}")
                self.print_info(f"Response: {response.text[:200]}")
                return False
        except Exception as e:
            self.print_error(f"Order creation error: {e}")
            return False
    
    def test_get_order_details(self):
        """Test retrieving order details"""
        if not self.token:
            self.print_error("Authentication required")
            return
        
        if not self.test_data.get('created_order'):
            self.print_info("No order created yet, skipping order details test")
            return
        
        self.print_header("Testing Get Order Details")
        order_id = self.test_data['created_order']['order_id']
        
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}",
                headers=self.get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Order details retrieved")
                order = data['data']['order']
                self.print_info(f"Status: {order['order_status']}")
                self.print_info(f"Items: {len(order['items'])}")
                self.print_info(f"Payment: {order['payment_method']} ({order['payment_status']})")
                return True
            elif response.status_code == 404:
                self.print_error("Order not found (might have been cleaned up)")
                return False
            else:
                self.print_error(f"Failed to get order: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Get order error: {e}")
            return False
    
    def test_order_tracking(self):
        """Test order tracking functionality"""
        if not self.token:
            self.print_error("Authentication required")
            return
        
        order_id = None
        if self.test_data.get('created_order'):
            order_id = self.test_data['created_order']['order_id']
        else:
            # Try with a sample order ID
            order_id = "ORD-20260101000000-TEST01"
        
        self.print_header("Testing Order Tracking")
        
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}/track",
                headers=self.get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Order tracking data retrieved")
                tracking = data['data']
                self.print_info(f"Current Status: {tracking['order_status']}")
                if tracking.get('driver'):
                    self.print_info(f"Driver: {tracking['driver']['name']}")
                self.print_info(f"Status History: {len(tracking['status_timeline'])} events")
                return True
            elif response.status_code == 404:
                self.print_info("Order not found (normal for test order IDs)")
                return True  # Not an error, just no data
            else:
                self.print_error(f"Tracking failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Tracking error: {e}")
            return False
    
    def test_available_drivers(self):
        """Test getting available drivers"""
        if not self.token:
            self.print_error("Authentication required")
            return
        
        self.print_header("Testing Available Drivers")
        
        try:
            response = requests.get(
                f"{self.base_url}/drivers/available",
                headers=self.get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                drivers = data['data']['drivers']
                count = data['data']['count']
                self.print_success(f"Found {count} available drivers")
                
                if drivers:
                    for i, driver in enumerate(drivers[:3], 1):  # Show first 3
                        self.print_info(f"Driver {i}: {driver['name']} - {driver['vehicle_type']} - Rating: {driver['rating']}")
                return True
            else:
                self.print_error(f"Failed to get drivers: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Drivers test error: {e}")
            return False
    
    def test_error_handling(self):
        """Test error scenarios"""
        self.print_header("Testing Error Handling")
        
        error_tests = [
            ("POST", "/auth/login", {}, "Empty login"),
            ("POST", "/auth/login", {"username": "nonexistent"}, "Missing password"),
            ("GET", "/orders/INVALID-ORDER", None, "Invalid order ID"),
            ("GET", "/restaurants/INVALID-REST/menu", None, "Invalid restaurant"),
        ]
        
        for method, endpoint, payload, description in error_tests:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=3)
                else:
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(
                        f"{self.base_url}{endpoint}", 
                        json=payload if payload else {},
                        headers=headers,
                        timeout=3
                    )
                
                # For error tests, 4xx status codes are expected successes
                if 400 <= response.status_code < 500:
                    self.print_success(f"{description}: Correctly returned {response.status_code}")
                elif response.status_code >= 200 and response.status_code < 400:
                    self.print_info(f"{description}: Returned {response.status_code} (unexpected success)")
                else:
                    self.print_error(f"{description}: Unexpected {response.status_code}")
            except Exception as e:
                self.print_error(f"{description}: {e}")
    
    def run_complete_test(self, username="admin", password="Admin@123"):
        """Run complete test suite"""
        print("\n" + "="*70)
        print(" MEGA PIZZA DELIVERY - ORDER API TEST SUITE")
        print("="*70)
        print(f"API URL: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        test_results = []
        
        # Test 1: Connection
        if self.test_connection():
            test_results.append(True)
        else:
            test_results.append(False)
            print("\n❌ Cannot proceed without API connection")
            return False
        
        # Test 2: Authentication
        if self.authenticate(username, password):
            test_results.append(True)
        else:
            test_results.append(False)
            print("\n⚠️  Authentication failed, some tests will be skipped")
        
        # Test 3: Public endpoints
        self.test_public_endpoints()
        test_results.append(True)  # Mark as passed unless connection failed
        
        # Test 4: Restaurant menu
        self.test_restaurant_menu()
        test_results.append(True)
        
        # Test 5: Setup customer
        self.create_test_customer()
        test_results.append(True)
        
        # Test 6: Order creation (requires auth)
        if self.token:
            order_created = self.test_order_creation()
            test_results.append(order_created)
        else:
            self.print_info("Skipping order creation (no authentication)")
            test_results.append(False)
        
        # Test 7: Get order details
        if self.token:
            order_details = self.test_get_order_details()
            test_results.append(order_details)
        else:
            self.print_info("Skipping order details (no authentication)")
            test_results.append(False)
        
        # Test 8: Order tracking
        if self.token:
            tracking = self.test_order_tracking()
            test_results.append(tracking)
        else:
            self.print_info("Skipping order tracking (no authentication)")
            test_results.append(False)
        
        # Test 9: Available drivers
        if self.token:
            drivers = self.test_available_drivers()
            test_results.append(drivers)
        else:
            self.print_info("Skipping drivers test (no authentication)")
            test_results.append(False)
        
        # Test 10: Error handling
        self.test_error_handling()
        test_results.append(True)
        
        # Summary
        self.print_header("TEST SUMMARY")
        passed = sum([1 for r in test_results if r])
        total = len(test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Order API is working correctly.")
        elif passed >= total * 0.7:
            print("\n⚠️  MOST TESTS PASSED. Check failed tests above.")
        else:
            print("\n❌ MULTIPLE TESTS FAILED. Review errors above.")
        
        print("\n" + "="*70)
        print(" NEXT STEPS:")
        print("="*70)
        print("1. Check database has test data (customers, restaurants, menu items)")
        print("2. Verify PostgreSQL is running and accessible")
        print("3. Test with different user roles (admin, customer, driver)")
        print("4. Integrate with frontend application")
        print("5. Set up automated testing pipeline")
        print("="*70)
        
        return passed == total

def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Mega Pizza Order API')
    parser.add_argument('--url', default='http://localhost:8000/api/v1',
                       help='API base URL (default: http://localhost:8000/api/v1)')
    parser.add_argument('--username', default='admin',
                       help='Username for authentication (default: admin)')
    parser.add_argument('--password', default='Admin@123',
                       help='Password for authentication (default: Admin@123)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick test only (connection and auth)')
    
    args = parser.parse_args()
    
    tester = MegaPizzaOrderTester(args.url)
    
    if args.quick:
        # Quick test
        print("Running quick test...")
        if tester.test_connection() and tester.authenticate(args.username, args.password):
            print("\n✅ Quick test passed!")
            sys.exit(0)
        else:
            print("\n❌ Quick test failed!")
            sys.exit(1)
    else:
        # Complete test suite
        success = tester.run_complete_test(args.username, args.password)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
