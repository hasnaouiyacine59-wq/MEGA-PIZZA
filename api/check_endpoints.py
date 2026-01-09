# check_endpoints.py
import requests

BASE_URL = "http://localhost:5000"

def check_all_routes():
    """Check what routes are actually available"""
    print("🔍 Checking available routes...")
    
    endpoints = [
        "/",
        "/health",
        "/api",
        "/auth/login",
        "/auth/register",
        "/admin/dashboard",
        "/test/dashboard",
        "/api/restaurants",
        "/api/orders",
        "/api/auth/register",
        "/api/auth/login"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=2)
            print(f"✓ {endpoint}: {response.status_code}")
        except:
            print(f"✗ {endpoint}: Connection failed")

if __name__ == "__main__":
    check_all_routes()
