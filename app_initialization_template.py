# app_initialization_template.py
# Template showing how to initialize Supabase sync in your Flask app

"""
Add this to your app/__init__.py or create_app() function
"""

from flask import Flask
from app.services.supabase_realtime_sync import init_supabase_realtime
import logging

def create_app(config=None):
    """
    Flask app factory with Supabase real-time sync initialization
    """
    app = Flask(__name__)
    
    # ... your existing Flask setup ...
    
    # ========== SUPABASE INITIALIZATION ==========
    
    # Initialize Supabase real-time sync
    supabase_sync = init_supabase_realtime()
    
    if supabase_sync and supabase_sync.is_ready():
        print("✓ Supabase Realtime Sync initialized")
        
        # Optional: Setup real-time subscriptions on startup
        # setup_realtime_listeners(supabase_sync)
    else:
        print("⚠ Supabase not configured - running in local-only mode")
    
    # Store reference in app config for easy access
    app.supabase_sync = supabase_sync
    
    # ========== OPTIONAL: PERIODIC RETRY TASK ==========
    
    # Option A: Using APScheduler (recommended)
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        
        def retry_syncs():
            """Periodically retry failed syncs"""
            if supabase_sync and supabase_sync.is_ready():
                result = supabase_sync.retry_failed_syncs()
                if result['failed'] > 0:
                    logging.warning(f"Still have {result['failed']} failed syncs")
        
        scheduler.add_job(
            retry_syncs,
            'interval',
            seconds=60,  # Retry every 60 seconds
            id='retry_syncs'
        )
        scheduler.start()
        print("✓ Sync retry scheduler started")
    
    except ImportError:
        print("⚠ APScheduler not installed - skipping auto-retry")
    
    # Option B: Using Flask before_request (simpler, less efficient)
    # Uncomment if you prefer this approach
    # 
    # import time
    # last_retry = {}
    # 
    # @app.before_request
    # def retry_failed_syncs():
    #     current_time = time.time()
    #     if current_time - last_retry.get('time', 0) > 60:  # Every 60 seconds
    #         if supabase_sync and supabase_sync.is_ready():
    #             supabase_sync.retry_failed_syncs()
    #         last_retry['time'] = current_time
    
    return app


def setup_realtime_listeners(supabase_sync):
    """
    Setup real-time listeners for all tables
    Call this after Flask app is initialized
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Callback for case changes
    def on_cases_change(payload):
        event_type = payload.get('eventType')
        new_record = payload.get('new')
        old_record = payload.get('old')
        
        logger.info(f"Case {event_type}: {new_record}")
        
        # Example: You could update a cache or notify connected users
        # if event_type == 'INSERT':
        #     cache.update_cases()
        # elif event_type == 'UPDATE':
        #     broadcast_to_users(f"Case {new_record['id']} updated")
    
    # Callback for user changes
    def on_users_change(payload):
        event_type = payload.get('eventType')
        new_record = payload.get('new')
        
        logger.info(f"User {event_type}: {new_record}")
    
    # Callback for activity logs
    def on_activity_logs_change(payload):
        event_type = payload.get('eventType')
        new_record = payload.get('new')
        
        logger.info(f"Activity {event_type}: {new_record}")
    
    # Subscribe to all tables
    supabase_sync.subscribe_to_table('cases', on_cases_change)
    supabase_sync.subscribe_to_table('users', on_users_change)
    supabase_sync.subscribe_to_table('activity_logs', on_activity_logs_change)
    
    logger.info("Real-time listeners subscribed to all tables")


# ========== EXAMPLE: UPDATE YOUR EXISTING __init__.py ==========

"""
Here's what to add to your app/__init__.py:

from flask_mysqldb import MySQL
from flask import Flask
from app.services.supabase_realtime_sync import init_supabase_realtime

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    
    # Initialize MySQL
    mysql.init_app(app)
    
    # Initialize Supabase
    supabase_sync = init_supabase_realtime()
    app.supabase_sync = supabase_sync
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app
"""


# ========== EXAMPLE: WRAPPER FUNCTIONS FOR COMMON OPERATIONS ==========

class DatabaseOperations:
    """
    Wrapper class for database operations with automatic Supabase sync
    Usage:
        db_ops = DatabaseOperations(app)
        db_ops.create_case(...)
        db_ops.update_case_status(...)
    """
    
    def __init__(self, app):
        self.app = app
        self.supabase_sync = app.supabase_sync
        self.mysql = app.config.get('mysql')
    
    def create_case(self, case_data):
        """Create a case with automatic Supabase sync"""
        from app import mysql
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO cases 
            (reference_no, complainant_name, complainant_email, incident_date, narrative, created_by)
            VALUES (%(reference_no)s, %(complainant_name)s, %(complainant_email)s, 
                    %(incident_date)s, %(narrative)s, %(created_by)s)
        """, case_data)
        mysql.connection.commit()
        case_data['id'] = cur.lastrowid
        cur.close()
        
        # Sync to Supabase
        if self.supabase_sync and self.supabase_sync.is_ready():
            self.supabase_sync.sync_record_to_supabase('cases', case_data, 'insert')
        
        return case_data
    
    def update_case(self, case_id, updates):
        """Update a case with automatic Supabase sync"""
        from app import mysql
        
        cur = mysql.connection.cursor()
        fields = ', '.join([f"{k}=%s" for k in updates.keys()])
        values = list(updates.values()) + [case_id]
        
        cur.execute(f"UPDATE cases SET {fields} WHERE id=%s", values)
        mysql.connection.commit()
        cur.close()
        
        # Sync to Supabase
        if self.supabase_sync and self.supabase_sync.is_ready():
            updates['id'] = case_id
            self.supabase_sync.sync_record_to_supabase('cases', updates, 'update')
        
        return True
    
    def get_cases_from_cloud(self, filters=None):
        """Get cases directly from Supabase cloud"""
        if not self.supabase_sync or not self.supabase_sync.is_ready():
            return None
        
        return self.supabase_sync.pull_from_supabase('cases', filters)
