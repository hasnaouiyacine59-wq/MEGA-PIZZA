# quick_test.py
import requests

def quick_test():
    """Quick test of the API"""
    print("Quick API Test\n")
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/api/v1/health", "Health check"),
        ("GET", "/api/v1/docs", "API docs"),
        ("GET", "/api/v1/restaurants", "Restaurants list"),
    ]
    
    for method, endpoint, description in endpoints:
        url = f"http://localhost:8000{endpoint}"
        print(f"Testing: {description}")
        print(f"URL: {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5, json={})
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success\n")
            else:
                print(f"❌ Failed - Response: {response.text[:100]}...\n")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect - Is the API running?\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    quick_test()
