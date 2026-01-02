#!/bin/bash
echo "📊 MEGA PIZZA DATABASE SUMMARY"
echo "=============================="

echo -e "\n1. DATABASE INFO:"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT 
    current_database() as database,
    current_user as current_user,
    version() as postgres_version,
    (SELECT setting FROM pg_settings WHERE name = 'TimeZone') as timezone,
    (SELECT setting FROM pg_settings WHERE name = 'server_encoding') as encoding;
"

echo -e "\n2. TABLES (Total count and size):"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT 
    COUNT(*) as table_count,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname || '.' || tablename))) as total_size
FROM pg_tables 
WHERE schemaname = 'public';
"

echo -e "\n3. TABLES LIST:"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT 
    tablename as table_name,
    pg_size_pretty(pg_total_relation_size('public.' || tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
"

echo -e "\n4. USERS/ROLES:"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT rolname as username, rolsuper as is_superuser, rolcanlogin as can_login
FROM pg_roles 
WHERE rolname NOT LIKE 'pg_%'
ORDER BY rolname;
"

echo -e "\n5. EXTENSIONS:"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT extname as extension, extversion as version
FROM pg_extension
ORDER BY extname;
"

echo -e "\n6. SAMPLE DATA CHECK:"
docker exec mega_pizza-db-cnt psql -U mega_pizza_admin -d mega_pizza_db -c "
SELECT 
    'restaurants' as table_name, 
    (SELECT COUNT(*) FROM restaurants) as row_count
UNION ALL
SELECT 
    'users' as table_name, 
    (SELECT COUNT(*) FROM users) as row_count
UNION ALL
SELECT 
    'customers' as table_name, 
    (SELECT COUNT(*) FROM customers) as row_count
ORDER BY table_name;
"
