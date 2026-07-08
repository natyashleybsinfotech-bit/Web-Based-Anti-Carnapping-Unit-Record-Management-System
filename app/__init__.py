import os
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask import Flask
from flask_mysqldb import MySQL
from flask_mail import Mail
from dotenv import load_dotenv

mysql = MySQL()
mail = Mail()

# Set Philippines timezone globally (UTC+8)
PH_TIMEZONE = ZoneInfo("Asia/Manila")


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
    app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
    app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
    app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "carnapping_db")
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
    app.config["BASE_URL"] = os.getenv("BASE_URL", "http://127.0.0.1:5000")
    app.config["TIMEZONE"] = "Asia/Manila"  # Philippines timezone (UTC+8)

    # Supabase (kept for reference / fallback)
    app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")
    app.config["SUPABASE_ANON_KEY"] = os.getenv("SUPABASE_ANON_KEY", "")
    app.config["SUPABASE_SERVICE_KEY"] = os.getenv("SUPABASE_SERVICE_KEY", "")
    app.config["SUPABASE_SYNC_ENABLED"] = (
        os.getenv("SUPABASE_SYNC_ENABLED", "False") == "True"
    )

    # Firebase Firestore (primary cloud DB)
    app.config["FIREBASE_CREDENTIALS_PATH"] = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"
    )
    app.config["FIREBASE_SYNC_ENABLED"] = (
        os.getenv("FIREBASE_SYNC_ENABLED", "False") == "True"
    )

    mysql.init_app(app)
    mail.init_app(app)

    # Set MySQL timezone to Philippines on each request
    @app.before_request
    def set_mysql_timezone():
        """Ensure MySQL session uses Philippines timezone (UTC+8)"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SET time_zone='+08:00'")
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            app.logger.debug(f"MySQL timezone note: {e}")

    from .routes import bp

    app.register_blueprint(bp)

    # Initialize Firebase Firestore sync
    with app.app_context():
        try:
            from .services.firebase_sync import (
                init_firebase,
                is_ready as firebase_ready,
            )

            ok = init_firebase()
            if ok:
                app.logger.info("✓ Firebase Firestore sync initialized")
            else:
                app.logger.info(
                    "ℹ Firebase sync not active (disabled or credentials missing)"
                )
        except Exception as e:
            app.logger.warning(f"Firebase init warning: {e}")

    return app
