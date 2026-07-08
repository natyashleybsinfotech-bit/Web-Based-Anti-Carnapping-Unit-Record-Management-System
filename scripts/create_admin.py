import mysql.connector
import bcrypt
import os

# Database connection details (matches your .env)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "carnapping_db"


def create_default_admin():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        cursor = conn.cursor()

        # Admin details
        username = "admin"
        password = "password123"
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            print("❌ Admin user already exists!")
        else:
            # Insert admin user
            query = """
            INSERT INTO users (full_name, email, role, password_hash, username, is_active, force_password_change)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                "System Admin",
                "admin@mpd.gov.ph",
                "admin",
                hashed_password,
                username,
                1,
                0,
            )

            cursor.execute(query, values)
            conn.commit()
            print("✅ Default admin created successfully!")
            print(f"👉 Username: {username}")
            print(f"👉 Password: {password}")

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    create_default_admin()
