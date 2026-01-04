# create_fix_metadata.py
from app import db, create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check what columns actually exist
    result = db.session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'order_status_history'
        ORDER BY ordinal_position;
    """))
    
    print("Actual database columns:")
    for row in result:
        print(f"  {row.column_name}: {row.data_type}")
    
    # Drop and recreate the table if needed
    print("\nIf 'notes' column exists, we need to remove it...")
    
    # Option 1: Drop column if it exists
    try:
        db.session.execute(text("ALTER TABLE order_status_history DROP COLUMN IF EXISTS notes;"))
        db.session.commit()
        print("✅ Dropped 'notes' column if it existed")
    except Exception as e:
        print(f"❌ Error dropping column: {e}")
        db.session.rollback()
