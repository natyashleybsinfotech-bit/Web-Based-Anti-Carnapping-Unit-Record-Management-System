#!/usr/bin/env python3
"""
Initialize the database schema
"""
import os
from dotenv import load_dotenv
import MySQLdb
from MySQLdb import cursors

load_dotenv()

# Database connection
conn = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    autocommit=True
)

try:
    # Read schema file
    with open("schema.sql", "r") as f:
        schema = f.read()
    
    # Execute schema
    cursor = conn.cursor()
    
    # Split and execute individual statements
    statements = schema.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
                print(f"✓ Executed: {statement[:60]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    conn.commit()
    cursor.close()
    print("\n✅ Database schema initialized successfully!")
    
except Exception as e:
    print(f"❌ Error initializing database: {e}")
finally:
    conn.close()
