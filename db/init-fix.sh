#!/bin/bash
echo "🔧 Fixing Mega Pizza Database Initialization"

# Stop container if running
docker stop mega_pizza-db-cnt 2>/dev/null || true
docker rm mega_pizza-db-cnt 2>/dev/null || true

# Remove old volume
docker volume rm mega_pizza_db_data 2>/dev/null || true

# Build fresh image
echo "Building image..."
docker build --no-cache -t mega_pizza-db-img .

# Run container
echo "Starting container..."
docker run -d \
  --name mega_pizza-db-cnt \
  -e POSTGRES_DB=mega_pizza_db \
  -e POSTGRES_USER=mega_pizza_admin \
  -e POSTGRES_PASSWORD=SecurePass123! \
  -e TZ=Africa/Algiers \
  -p 5432:5432 \
  -v mega_pizza_db_data:/var/lib/postgresql/data \
  mega_pizza-db-img

# Wait and check
echo "Waiting for initialization..."
sleep 15

echo "Checking initialization..."
docker logs mega_pizza-db-cnt --tail 30 | grep -i "init\|executing\|done"

echo "Testing database..."
if docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "\dt" | grep -q "restaurants"; then
    echo "✅ SUCCESS: Tables created!"
    echo "Tables found:"
    docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "\dt"
else
    echo "❌ FAILED: No tables created."
    echo "Last 50 lines of logs:"
    docker logs mega_pizza-db-cnt --tail 50
fi
