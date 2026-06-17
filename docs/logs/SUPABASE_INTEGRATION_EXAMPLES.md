# Example: Integrating Supabase Real-Time Sync with Flask Routes
# This file shows how to modify your routes to use Supabase with real-time sync

"""
INTEGRATION EXAMPLES FOR SUPABASE REALTIME SYNC

Add these imports to your routes.py:
    from app.services.supabase_realtime_sync import supabase_sync, sync_to_supabase

And use the examples below in your route handlers.
"""

# ==================== EXAMPLE 1: CREATE CASE WITH AUTO-SYNC ====================

def create_case_example(complainant_name, complainant_email, incident_date, narrative):
    """Example: Create case with automatic Supabase sync"""
    from app import mysql
    
    try:
        # 1. Generate reference number
        ref_no = generate_reference()
        
        # 2. Insert into local MySQL
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO cases 
            (reference_no, complainant_name, complainant_email, incident_date, narrative, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ref_no, complainant_name, complainant_email, incident_date, narrative, session['user_id']))
        mysql.connection.commit()
        case_id = cur.lastrowid
        cur.close()
        
        # 3. Prepare data for Supabase sync
        case_data = {
            'id': case_id,
            'reference_no': ref_no,
            'complainant_name': complainant_name,
            'complainant_email': complainant_email,
            'incident_date': str(incident_date),
            'narrative': narrative,
            'created_by': session['user_id'],
            'status': 'Pending'
        }
        
        # 4. Sync to Supabase (non-blocking)
        if supabase_sync.is_ready():
            supabase_sync.sync_record_to_supabase('cases', case_data, 'insert')
        
        return {'status': 'success', 'case_id': case_id, 'reference_no': ref_no}
    
    except Exception as e:
        print(f"Error creating case: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== EXAMPLE 2: UPDATE CASE STATUS ====================

def update_case_status_example(case_id, new_status):
    """Example: Update case with Supabase sync"""
    from app import mysql
    
    try:
        # 1. Update local database
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE cases SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_status, case_id)
        )
        mysql.connection.commit()
        cur.close()
        
        # 2. Sync update to Supabase
        if supabase_sync.is_ready():
            supabase_sync.sync_record_to_supabase(
                'cases',
                {'id': case_id, 'status': new_status},
                'update'
            )
        
        # 3. Log activity
        log_activity(session['user_id'], 'UPDATE_CASE_STATUS', f'Case {case_id} status changed to {new_status}')
        
        return {'status': 'success', 'message': f'Case status updated to {new_status}'}
    
    except Exception as e:
        print(f"Error updating case: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== EXAMPLE 3: BATCH SYNC ACTIVITY LOGS ====================

def sync_activity_logs_example():
    """Example: Batch sync pending activity logs to Supabase"""
    from app import mysql
    
    try:
        # 1. Get recent activity logs from local database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, user_id, action, description, created_at
            FROM activity_logs
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        logs = cur.fetchall()
        cur.close()
        
        if not logs:
            return {'status': 'success', 'synced': 0}
        
        # 2. Batch sync to Supabase
        if supabase_sync.is_ready():
            result = supabase_sync.batch_sync_to_supabase('activity_logs', logs, 'insert')
            return result
        
        return {'status': 'success', 'synced': len(logs)}
    
    except Exception as e:
        print(f"Error syncing activity logs: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== EXAMPLE 4: SUBSCRIBE TO REAL-TIME CHANGES ====================

def setup_realtime_subscriptions_example():
    """
    Example: Setup real-time subscriptions
    Call this once during app initialization
    """
    if not supabase_sync.is_ready():
        print("Supabase not ready for subscriptions")
        return
    
    # Define callback for case changes
    def on_case_change(payload):
        """Handle real-time changes to cases"""
        event_type = payload.get('eventType')
        new_record = payload.get('new')
        
        print(f"Case event: {event_type}")
        print(f"Data: {new_record}")
        
        # You could:
        # - Update a cache
        # - Notify connected WebSocket clients
        # - Log to monitoring system
        # - Update local database if change came from elsewhere
    
    def on_user_change(payload):
        """Handle real-time changes to users"""
        event_type = payload.get('eventType')
        new_record = payload.get('new')
        
        print(f"User event: {event_type}")
        print(f"Data: {new_record}")
    
    # Subscribe to tables
    supabase_sync.subscribe_to_table('cases', on_case_change)
    supabase_sync.subscribe_to_table('users', on_user_change)
    print("Real-time subscriptions initialized")


# ==================== EXAMPLE 5: PULL DATA FROM SUPABASE ====================

def pull_cases_from_supabase_example(status='Pending'):
    """Example: Pull specific data from Supabase"""
    if not supabase_sync.is_ready():
        return {'status': 'error', 'message': 'Supabase not available'}
    
    try:
        # Pull pending cases from Supabase
        cases = supabase_sync.pull_from_supabase('cases', {'status': status})
        
        if cases:
            print(f"Retrieved {len(cases)} {status} cases from Supabase")
            return {'status': 'success', 'cases': cases}
        else:
            return {'status': 'success', 'cases': []}
    
    except Exception as e:
        print(f"Error pulling from Supabase: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== EXAMPLE 6: HEALTH CHECK ENDPOINT ====================

def sync_health_check_example():
    """Example: Health check endpoint for monitoring"""
    from flask import jsonify
    
    status = supabase_sync.get_sync_status()
    
    return jsonify({
        'sync_status': 'healthy' if status['is_ready'] else 'unavailable',
        'active_subscriptions': status['active_subscriptions'],
        'pending_syncs': status['pending_syncs'],
        'last_sync_times': status['last_sync_times'],
        'timestamp': status['timestamp']
    })


# ==================== EXAMPLE 7: RETRY FAILED SYNCS ====================

def retry_failed_syncs_example():
    """Example: Retry previously failed sync operations"""
    if not supabase_sync.is_ready():
        return {'status': 'error', 'message': 'Supabase not available'}
    
    try:
        result = supabase_sync.retry_failed_syncs()
        print(f"Retried {result['retried']} sync operations, {result['failed']} still failing")
        return result
    
    except Exception as e:
        print(f"Error retrying syncs: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== EXAMPLE 8: DECORATOR USAGE ====================

# Apply decorator to automatically sync operations
# @sync_to_supabase('users', 'insert')
# def create_user(username, email, role):
#     cur = mysql.connection.cursor()
#     cur.execute(
#         "INSERT INTO users (username, email, role) VALUES (%s, %s, %s)",
#         (username, email, role)
#     )
#     mysql.connection.commit()
#     user_id = cur.lastrowid
#     cur.close()
#     
#     # Return dict with user data (will be auto-synced to Supabase)
#     return {
#         'id': user_id,
#         'username': username,
#         'email': email,
#         'role': role
#     }


# ==================== INTEGRATION CHECKLIST ====================

"""
To integrate Supabase real-time sync into your Flask app:

✓ STEP 1: Install dependencies
  pip install -r requirements.txt

✓ STEP 2: Set environment variables (.env)
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_ANON_KEY=your-key
  SUPABASE_SERVICE_KEY=your-service-key
  SUPABASE_SYNC_ENABLED=True

✓ STEP 3: Create tables in Supabase
  Run the SQL from SUPABASE_SETUP.md

✓ STEP 4: Migrate existing data
  python migrate_to_supabase.py

✓ STEP 5: Initialize sync in your Flask app
  from app.services.supabase_realtime_sync import init_supabase_realtime
  supabase_sync = init_supabase_realtime()

✓ STEP 6: Update your routes with the examples above

✓ STEP 7: Add real-time frontend updates
  See SUPABASE_SETUP.md for frontend JavaScript examples

✓ STEP 8: Test and deploy
  - Test local changes sync to Supabase
  - Test Supabase changes reflect locally
  - Monitor sync health with health check endpoint
"""
