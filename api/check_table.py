# check_db_tables.py
import psycopg2

def check_database_structure():
    """Check what tables and columns exist"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='mega_pizza_db',
            user='mega_pizza_admin',
            password='SecurePass123!',
            port=5432
        )
        cur = conn.cursor()
        
        print("📊 Database Structure Check")
        print("="*50)
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get columns for this table
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cur.fetchall()
            print(f"  Columns ({len(columns)}):")
            for col in columns:
                print(f"    - {col[0]}: {col[1]} ({'nullable' if col[2] == 'YES' else 'not null'})")
            
            # Get row count
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"  Row count: {count}")
            except:
                print("  Could not get row count")
        
        # Check specific tables we need
        print("\n" + "="*50)
        print("🔍 Checking critical tables for orders:")
        
        required_tables = ['customers', 'restaurants', 'orders', 'order_items']
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]
            print(f"  {table}: {'✅ EXISTS' if exists else '❌ MISSING'}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_structure()
