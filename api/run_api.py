# api/run_api.py
from app import create_api_app

app = create_api_app()

if __name__ == '__main__':
    # Run on all interfaces, port 8000
    app.run(host='0.0.0.0', port=8000, debug=False)