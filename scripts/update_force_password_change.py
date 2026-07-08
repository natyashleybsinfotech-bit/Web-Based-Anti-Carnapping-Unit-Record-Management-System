#!/usr/bin/env python3
"""
Update existing users to require password change on first login
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
    database=os.getenv("MYSQL_DB", "carnapping_db"),
)

try:
    cursor = conn.cursor()

    print("🔄 Updating users to require password change on first login...\n")

    # Get all officers with force_password_change = 0
    cursor.execute("""
        SELECT id, username, role 
        FROM users 
        WHERE role = 'officer' AND force_password_change = 0
    """)

    users = cursor.fetchall()

    if not users:
        print(
            "✓ All officers already have force_password_change enabled or no officers found"
        )
    else:
        print(
            f"Found {len(users)} officers that need to change password on first login:\n"
        )

        for user_id, username, role in users:
            cursor.execute(
                """
                UPDATE users 
                SET force_password_change = 1 
                WHERE id = %s
            """,
                (user_id,),
            )
            print(
                f"  ✓ {username} (ID: {user_id}) - will require password change on next login"
            )

        conn.commit()
        print(f"\n✅ Updated {len(users)} users successfully!")

    cursor.close()

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
