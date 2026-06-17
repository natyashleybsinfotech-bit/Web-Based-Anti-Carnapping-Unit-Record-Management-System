# Supabase Real-time Sync Service
# Enables bi-directional real-time synchronization between local MySQL and Supabase PostgreSQL

import os
import json
import logging
import asyncio
from datetime import datetime
from threading import Thread, Lock, Event, local
from functools import wraps
from flask import current_app
import re
import supabase._sync.client

# Monkeypatch to bypass Supabase python SDK's strict JWT validation for newer publishable keys
_original_re_match = re.match
def _mock_re_match(pattern, string, flags=0):
    if isinstance(string, str) and string.startswith('sb_'):
        return True
    return _original_re_match(pattern, string, flags)

supabase._sync.client.re.match = _mock_re_match

try:
    import supabase._async.client
    supabase._async.client.re.match = _mock_re_match
except ImportError:
    pass

from supabase import create_client, Client
import time

logger = logging.getLogger(__name__)


class SupabaseRealtimeSync:
    """
    Manages real-time synchronization between local database and Supabase.
    Handles WebSocket connections, event listeners, and conflict resolution.
    """
    
    _instance = None
    _lock = Lock()
    
    # List of all tables that need syncing
    TABLES = ['users', 'complainants', 'cases', 'receipts', 'activity_logs', 'hotspot']
    
    def __new__(cls):
        """Singleton pattern to ensure only one sync instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._local_storage = local()
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.sync_enabled = os.getenv('SUPABASE_SYNC_ENABLED', 'False') == 'True'
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured")
            self.client = None
            self.async_client = None
            self._initialized = True
            return
        
        try:
            # Sync client for standard operations
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            # Async client for real-time listeners
            self.async_client = None  # AsyncClient removed in supabase v2
            self.listeners = {}
            self.sync_queue = []
            self.last_sync_times = {}
            self.sync_threads = {}
            self.stop_event = Event()
            self._async_loop = None
            self._listener_thread = None
            self._initialized = True
            logger.info("Supabase Realtime Sync initialized successfully (Sync + Async)")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            self.client = None
            self.async_client = None
            self._initialized = True
    
    def is_ready(self):
        """Check if Supabase is properly configured"""
        return self.client is not None and self.sync_enabled
    
    # ==================== REAL-TIME LISTENERS ====================
    
    def subscribe_to_table_changes(self, table_name: str, callback):
        """
        Subscribe to real-time changes on a specific table via RealtimeChannel.
        
        Args:
            table_name: Name of the table to listen to
            callback: Function to call when changes occur
        
        Returns:
            Subscription object
        """
        if not self.is_ready():
            logger.warning(f"Cannot subscribe to {table_name}: Supabase not ready")
            return None
        
        try:
            # Create channel for real-time updates
            channel = self.client.realtime.channel(f"{table_name}_changes")
            
            # Subscribe to postgres_changes
            channel.on(
                "postgres_changes",
                {"event": "*", "schema": "public", "table": table_name},
                callback
            ).subscribe()
            
            self.listeners[table_name] = channel
            logger.info(f"Subscribed to real-time changes on {table_name}")
            return channel
        except Exception as e:
            logger.error(f"Failed to subscribe to {table_name}: {e}")
            return None
    
    def unsubscribe_from_table(self, table_name: str):
        """Unsubscribe from a table's real-time changes"""
        if table_name in self.listeners:
            try:
                channel = self.listeners[table_name]
                self.client.realtime.unsubscribe(channel)
                del self.listeners[table_name]
                logger.info(f"Unsubscribed from {table_name}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {table_name}: {e}")
    
    def setup_all_listeners(self, local_db_connection):
        """
        Set up real-time listeners for all tables.
        
        Args:
            local_db_connection: MySQL connection object from Flask
        """
        if not self.is_ready():
            logger.warning("Cannot setup listeners: Supabase not ready")
            return
        
        for table_name in self.TABLES:
            def make_callback(table):
                def callback(payload):
                    """Handle incoming changes from Supabase"""
                    try:
                        event_type = payload.get('eventType')
                        record = payload.get('new') or payload.get('old')
                        
                        if event_type == 'INSERT':
                            self._sync_from_cloud_to_local('INSERT', table, record, local_db_connection)
                        elif event_type == 'UPDATE':
                            self._sync_from_cloud_to_local('UPDATE', table, record, local_db_connection)
                        elif event_type == 'DELETE':
                            self._sync_from_cloud_to_local('DELETE', table, payload.get('old'), local_db_connection)
                        
                        logger.info(f"Synced {event_type} from Supabase: {table}")
                    except Exception as e:
                        logger.error(f"Error syncing {table} from cloud: {e}")
                
                return callback
            
            self.subscribe_to_table_changes(table_name, make_callback(table_name))
    
    def _sync_from_cloud_to_local(self, event_type: str, table_name: str, record: dict, connection):
        """
        Sync changes from Supabase to local MySQL database.
        
        Args:
            event_type: INSERT, UPDATE, or DELETE
            table_name: Name of the table
            record: The record data
            connection: MySQL connection
        """
        if not record:
            return
        
        try:
            cur = connection.cursor()
            # Prevent the local write from triggering a sync back to the cloud
            self._local_storage.is_syncing = True
            
            if event_type == 'INSERT':
                # Use REPLACE INTO for MySQL to handle potential collisions gracefully
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['%s'] * len(record.values()))
                values = list(record.values())
                query = f"REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
                cur.execute(query, values)
                
            elif event_type == 'UPDATE':
                record_id = record.get('id')
                if record_id:
                    set_clause = ', '.join([f"{k}=%s" for k in record.keys() if k != 'id'])
                    values = [v for k, v in record.items() if k != 'id'] + [record_id]
                    query = f"UPDATE {table_name} SET {set_clause} WHERE id=%s"
                    cur.execute(query, values)
                    
            elif event_type == 'DELETE':
                record_id = record.get('id')
                if record_id:
                    cur.execute(f"DELETE FROM {table_name} WHERE id=%s", (record_id,))
            
            connection.commit()
            cur.close()
            self._local_storage.is_syncing = False
            logger.info(f"Synced {event_type} to local DB: {table_name} ID: {record.get('id')}")
        except Exception as e:
            self._local_storage.is_syncing = False
            logger.error(f"Failed to sync {event_type} to local DB: {e}")
    
    # ==================== SYNC OPERATIONS ====================
    
    def sync_record_to_supabase(self, table_name: str, record_data: dict, operation: str = 'insert'):
        """
        Sync a single record to Supabase (local to cloud).
        
        Args:
            table_name: Name of the table
            record_data: Record data dictionary (should be a copy to avoid mutation)
            operation: 'insert', 'update', or 'delete'
        
        Returns:
            Response data or None if failed
        """
        if not self.is_ready():
            logger.warning(f"Sync disabled for {table_name}")
            return None
        
        try:
            # Make a copy to avoid mutating the original
            record_copy = record_data.copy()
            
            if operation == 'insert':
                # Use upsert to handle cases where the record already exists (e.g. after database restore)
                response = self.client.table(table_name).upsert(record_copy).execute()
            elif operation == 'update':
                record_id = record_copy.pop('id', None)
                if not record_id:
                    logger.error(f"Cannot update {table_name}: no id provided")
                    return None
                response = self.client.table(table_name).update(record_copy).eq('id', record_id).execute()
            elif operation == 'delete':
                record_id = record_copy.get('id')
                if not record_id:
                    logger.error(f"Cannot delete {table_name}: no id provided")
                    return None
                response = self.client.table(table_name).delete().eq('id', record_id).execute()
            else:
                raise ValueError(f"Invalid operation: {operation}")
            
            logger.info(f"Successfully synced {operation} to Supabase: {table_name}")
            self.last_sync_times[table_name] = datetime.now().isoformat()
            return response
        except Exception as e:
            logger.error(f"Failed to sync {operation} to Supabase ({table_name}): {e}")
            # Queue for retry
            self.sync_queue.append({
                'table': table_name,
                'data': record_data.copy(),
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            })
            return None
    
    def pull_from_supabase(self, table_name: str, filters: dict = None):
        """
        Pull data from Supabase (cloud to local, read-only check).
        
        Args:
            table_name: Name of the table
            filters: Dictionary of filters to apply
        
        Returns:
            List of records or None if failed
        """
        if not self.is_ready():
            logger.warning(f"Cannot pull from {table_name}: Supabase not ready")
            return None
        
        try:
            query = self.client.table(table_name).select('*')
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            logger.info(f"Successfully pulled {len(response.data)} records from {table_name}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to pull from Supabase ({table_name}): {e}")
            return None
    
    def batch_sync_to_supabase(self, table_name: str, records: list, operation: str = 'insert'):
        """
        Sync multiple records to Supabase in a batch.
        
        Args:
            table_name: Name of the table
            records: List of record dictionaries
            operation: 'insert' or 'update'
        
        Returns:
            Dictionary with sync status
        """
        if not self.is_ready():
            return {"status": "error", "message": "Supabase not ready"}
        
        if not records:
            return {"status": "success", "synced": 0, "failed": 0}
        
        synced = 0
        failed = 0
        
        try:
            if operation == 'insert':
                # Batch upsert (up to 1000 at a time to respect API limits)
                # ignoreDuplicates=True skips records that already exist (avoids startup 409/23505 errors)
                batch_size = 1000
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    response = self.client.table(table_name).upsert(
                        batch, ignore_duplicates=True
                    ).execute()
                    synced += len(batch)  # count attempted, not returned (upsert may return 0 on ignore)
                    
            elif operation == 'update':
                for record in records:
                    result = self.sync_record_to_supabase(table_name, record.copy(), 'update')
                    if result:
                        synced += 1
                    else:
                        failed += 1
            
            logger.info(f"Batch sync completed: {synced} synced, {failed} failed for {table_name}")
            return {
                "status": "success",
                "synced": synced,
                "failed": failed,
                "table": table_name,
                "operation": operation,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Batch sync failed for {table_name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "synced": synced,
                "failed": failed
            }
    
    def retry_failed_syncs(self):
        """Retry syncing records that failed previously"""
        if not self.is_ready():
            return {"status": "error", "message": "Supabase not ready"}
        
        if not self.sync_queue:
            return {"status": "success", "retried": 0}
        
        retried = 0
        still_failed = []
        
        for item in self.sync_queue:
            result = self.sync_record_to_supabase(
                item['table'],
                item['data'].copy(),
                item['operation']
            )
            if result:
                retried += 1
            else:
                still_failed.append(item)
        
        self.sync_queue = still_failed
        logger.info(f"Retry sync: {retried} succeeded, {len(still_failed)} still failing")
        return {
            "status": "success",
            "retried": retried,
            "failed": len(still_failed)
        }
    
    # ==================== UTILITY METHODS ====================
    
    def get_sync_status(self):
        """Get current synchronization status"""
        return {
            "is_ready": self.is_ready(),
            "active_subscriptions": len(self.listeners),
            "pending_syncs": len(self.sync_queue),
            "last_sync_times": self.last_sync_times,
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_sync_queue(self):
        """Clear the failed sync queue"""
        count = len(self.sync_queue)
        self.sync_queue = []
        logger.info(f"Cleared {count} items from sync queue")
        return count


# ==================== DECORATOR FOR AUTO-SYNC ====================

def sync_to_supabase(table_name: str, operation: str = 'insert'):
    """
    Decorator to automatically sync database operations to Supabase.
    
    Usage:
        @sync_to_supabase('users', 'insert')
        def create_user(user_data):
            # Insert to local DB
            # Function returns the created record or dict with 'id' and other fields
            return record
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the original function (local DB operation)
            result = func(*args, **kwargs)
            
            # Check if this operation was triggered by a cloud sync
            sync_instance = SupabaseRealtimeSync()
            if getattr(sync_instance._local_storage, 'is_syncing', False):
                return result

            # Sync to Supabase if result contains record data
            if result and isinstance(result, dict) and 'id' in result:
                sync_instance.sync_record_to_supabase(table_name, result.copy(), operation)
            
            return result
        return wrapper
    return decorator


# ==================== INITIALIZATION ====================

def init_supabase_realtime():
    """Initialize Supabase real-time sync service"""
    sync = SupabaseRealtimeSync()
    if not sync.is_ready():
        logger.warning("Supabase Realtime Sync not initialized - credentials missing or disabled")
        return None
    logger.info("Supabase Realtime Sync initialized")
    return sync


# Create global instance
supabase_sync = init_supabase_realtime()
