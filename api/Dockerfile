# REST API Service
FROM python:3.11-slim

WORKDIR /api

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy API-specific requirements
COPY requirements-api.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-api.txt

# Copy API application
COPY . .

# Create wsgi.py if it doesn't exist
RUN echo 'from app import create_api_app\n\napp = create_api_app()\n\nif __name__ == "__main__":\n    app.run(host="0.0.0.0", port=8000, debug=False)' > wsgi.py

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /api
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run API with gunicorn using wsgi.py
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "wsgi:app"]