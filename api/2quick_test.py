# Test 1: Check if Python can import your app
python -c "from app import create_app; print('Import successful!')"

# Test 2: Create and test a minimal app
python -c "
from app import create_app
app = create_app()
print('App created:', app)

# Test health endpoint
with app.test_client() as client:
    response = client.get('/health')
    print('Health check:', response.status_code, response.get_json())
"

# Test 3: Check for circular imports
python -c "
import sys
sys.setrecursionlimit(10000)
from app import create_app
app = create_app()
print('✅ No circular import errors!')
"
