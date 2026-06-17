#!/usr/bin/env python3
"""
Migration: Add force_password_change column to users table
This allows tracking which users need to change their password on first login
"""
import os
from dotenv import load_dotenv
import MySQLdb

load_dotenv()

# Database connection
conn = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    autocommit=True,
    database=os.getenv("MYSQL_DB", "carnapping_db")
)

try:
    cursor = conn.cursor()
    
    print("🔄 Running Migration: Add force_password_change column...")
    
    # Check if column exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME='users' AND COLUMN_NAME='force_password_change'
    """)
    
    if cursor.fetchone():
        print("✓ Column 'force_password_change' already exists")
    else:
        # Add the column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN force_password_change TINYINT DEFAULT 0 
            AFTER is_active
        """)
        print("✓ Added column 'force_password_change' to users table")
    
    conn.commit()
    cursor.close()
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
finally:
    conn.close()
