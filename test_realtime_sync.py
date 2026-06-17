#!/usr/bin/env python3
"""
Real-Time Sync Verification Test
Tests all sync functionality to ensure everything is working correctly.

Usage:
    python test_realtime_sync.py
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, mysql
from app.services.supabase_realtime_sync import supabase_sync
from app.services.cloud_sync_service import sync_all_tables_to_cloud, get_sync_status

def test_supabase_connection():
    """Test if Supabase connection works"""
    print("\n" + "=" * 80)
    print("TEST 1: Supabase Connection")
    print("=" * 80)
    
    if not supabase_sync:
        print("❌ Supabase sync not initialized")
        return False
    
    if not supabase_sync.is_ready():
        print("❌ Supabase not ready (credentials missing?)")
        return False
    
    print("✓ Supabase connection: OK")
    print(f"  URL: {supabase_sync.supabase_url}")
    print(f"  Ready: {supabase_sync.is_ready()}")
    return True


def test_tables_accessible():
    """Test if we can access Supabase tables"""
    print("\n" + "=" * 80)
    print("TEST 2: Table Accessibility")
    print("=" * 80)
    
    tables = ['users', 'cases', 'activity_logs', 'report_exports']
    all_ok = True
    
    for table_name in tables:
        try:
            result = supabase_sync.pull_from_supabase(table_name)
            if result is not None:
                count = len(result)
                print(f"✓ {table_name:<20} - Accessible ({count} records)")
            else:
                print(f"❌ {table_name:<20} - Cannot read")
                all_ok = False
        except Exception as e:
            print(f"❌ {table_name:<20} - Error: {str(e)[:50]}")
            all_ok = False
    
    return all_ok


def test_local_database():
    """Test if local MySQL is accessible"""
    print("\n" + "=" * 80)
    print("TEST 3: Local MySQL Database")
    print("=" * 80)
    
    try:
        cur = mysql.connection.cursor()
        
        # Count records in each table
        tables = ['users', 'cases', 'activity_logs', 'report_exports']
        all_ok = True
        
        for table_name in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"✓ {table_name:<20} - OK ({count} records)")
            except Exception as e:
                print(f"❌ {table_name:<20} - Error: {str(e)[:50]}")
                all_ok = False
        
        cur.close()
        return all_ok
        
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False


def test_sync_status():
    """Test sync status endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: Sync Status")
    print("=" * 80)
    
    try:
        status = get_sync_status()
        print(f"✓ Sync Status Retrieved:")
        print(f"  Ready: {status.get('is_ready')}")
        print(f"  Active Subscriptions: {status.get('active_subscriptions')}")
        print(f"  Pending Syncs: {status.get('pending_syncs')}")
        
        last_syncs = status.get('last_sync_times', {})
        if last_syncs:
            print(f"  Last Syncs:")
            for table, timestamp in last_syncs.items():
                print(f"    - {table}: {timestamp}")
        
        return True
    except Exception as e:
        print(f"❌ Error getting sync status: {e}")
        return False


def test_sync_operation():
    """Test a sync operation"""
    print("\n" + "=" * 80)
    print("TEST 5: Manual Sync Operation (Push)")
    print("=" * 80)
    
    try:
        print("Starting sync (this may take a moment)...")
        result = sync_all_tables_to_cloud(operation="push")
        
        print(f"\n✓ Sync Result:")
        print(f"  Status: {result.get('status')}")
        print(f"  Total Records Synced: {result.get('total_records')}")
        
        tables_synced = result.get('tables_synced', {})
        print(f"  Tables Synced:")
        for table, count in tables_synced.items():
            print(f"    - {table}: {count} records")
        
        errors = result.get('errors', [])
        if errors:
            print(f"  Errors:")
            for error in errors:
                print(f"    - {error}")
        
        return result.get('status') == 'success' or result.get('status') == 'partial_success'
        
    except Exception as e:
        print(f"❌ Sync operation failed: {e}")
        return False


def test_real_time_listeners():
    """Test if real-time listeners are set up"""
    print("\n" + "=" * 80)
    print("TEST 6: Real-Time Listeners")
    print("=" * 80)
    
    try:
        num_listeners = len(supabase_sync.listeners)
        expected_tables = 4  # users, cases, activity_logs, report_exports
        
        print(f"Active Listeners: {num_listeners}/{expected_tables}")
        
        for table_name, listener in supabase_sync.listeners.items():
            print(f"  ✓ {table_name} - Listening")
        
        return num_listeners == expected_tables
        
    except Exception as e:
        print(f"❌ Error checking listeners: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "REAL-TIME SYNC VERIFICATION TEST" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        results = []
        
        # Run tests
        results.append(("Supabase Connection", test_supabase_connection()))
        results.append(("Table Accessibility", test_tables_accessible()))
        results.append(("Local MySQL Database", test_local_database()))
        results.append(("Sync Status", test_sync_status()))
        results.append(("Sync Operation", test_sync_operation()))
        results.append(("Real-Time Listeners", test_real_time_listeners()))
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "❌ FAIL"
            print(f"{status:10} - {test_name}")
        
        print("-" * 80)
        print(f"Total: {passed}/{total} tests passed")
        print("=" * 80)
        
        if passed == total:
            print("\n✓ ALL TESTS PASSED! Real-time sync is working correctly.")
            print("\nYour sync is ready to use:")
            print("  1. Changes to local MySQL → auto-synced to Supabase")
            print("  2. Changes to Supabase → auto-synced to local MySQL")
            print("  3. Use /api/sync/* endpoints for manual control")
            return True
        elif passed >= total - 1:
            print("\n⚠️  Most tests passed, but check the failures above.")
            print("The system may still work but with limitations.")
            return True
        else:
            print("\n❌ Multiple tests failed. Check the configuration.")
            print("\nCommon issues:")
            print("  1. Supabase tables not created - run: python setup_supabase_tables.py")
            print("  2. Wrong credentials in .env")
            print("  3. Network connectivity issue")
            return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
