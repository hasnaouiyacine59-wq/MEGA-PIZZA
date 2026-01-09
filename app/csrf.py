# app/csrf.py
from functools import wraps
from flask import request, session, jsonify

def csrf_protect():
    """CSRF protection decorator factory"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # Try to get token from headers or form
                token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                
                # For JSON requests, check the JSON data
                if not token and request.is_json:
                    data = request.get_json(silent=True)
                    if data:
                        token = data.get('csrf_token')
                
                session_token = session.get('_csrf_token')
                
                if not token or not session_token or token != session_token:
                    if request.is_json or request.content_type == 'application/json':
                        return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 403
                    return 'Invalid CSRF token', 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
