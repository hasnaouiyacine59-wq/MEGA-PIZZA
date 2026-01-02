# test_app.py
from flask import Flask, render_template_string
import psycopg2

app = Flask(__name__)

def test_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!'
        )
        conn.close()
        return True
    except Exception as e:
        return str(e)

@app.route('/')
def index():
    db_status = test_db_connection()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mega Pizza Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-5">
        <h1>Mega Pizza Test Page</h1>
        <div class="alert alert-info">
            <h4>Database Connection Test:</h4>
            <p><strong>Status:</strong> %s</p>
            <p><strong>Database:</strong> mega_pizza_db</p>
            <p><strong>User:</strong> mega_pizza_admin</p>
        </div>
        <a href="/login" class="btn btn-primary">Go to Login</a>
    </body>
    </html>
    """ % ("✅ Connected" if db_status is True else f"❌ Error: {db_status}")
    
    return render_template_string(html)

@app.route('/login')
def login():
    return """
    <h1>Login Page</h1>
    <form>
        <input type="text" placeholder="Username" class="form-control mb-2">
        <input type="password" placeholder="Password" class="form-control mb-2">
        <button class="btn btn-primary">Login</button>
    </form>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
