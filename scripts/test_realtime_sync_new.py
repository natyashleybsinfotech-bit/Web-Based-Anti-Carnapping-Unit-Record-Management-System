#!/usr/bin/env python3
"""
Test script for Supabase Real-time Sync
Tests connection, credentials, and real-time listeners
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("SUPABASE REAL-TIME SYNC TEST")
print("=" * 70)

# Test 1: Environment Variables
print("\n[TEST 1] Environment Variables")
print("-" * 70)

supabase_url = os.getenv("SUPABASE_URL")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
sync_enabled = os.getenv("SUPABASE_SYNC_ENABLED", "False") == "True"

print(
    f"✓ SUPABASE_URL: {supabase_url[:50]}..."
    if supabase_url
    else "✗ SUPABASE_URL: NOT SET"
)
print(
    f"✓ SUPABASE_ANON_KEY: {supabase_anon_key[:30]}..."
    if supabase_anon_key
    else "✗ SUPABASE_ANON_KEY: NOT SET"
)
print(
    f"✓ SUPABASE_SERVICE_KEY: {'SET' if supabase_service_key and supabase_service_key != 'your_service_key_here' else 'NOT SET OR PLACEHOLDER'}"
)
print(f"✓ SUPABASE_SYNC_ENABLED: {sync_enabled}")

if not all([supabase_url, supabase_anon_key]):
    print("\n❌ ERROR: Missing required Supabase credentials!")
    sys.exit(1)

# Test 2: Supabase Connection
print("\n[TEST 2] Supabase Connection")
print("-" * 70)

try:
    from supabase import create_client

    supabase = create_client(supabase_url, supabase_anon_key)
    print("✓ Supabase client created successfully")
except Exception as e:
    print(f"✗ Failed to create Supabase client: {e}")
    sys.exit(1)

# Test 3: Check if tables exist
print("\n[TEST 3] Checking Supabase Tables")
print("-" * 70)

tables_to_check = ["users", "cases", "activity_logs", "report_exports"]

for table in tables_to_check:
    try:
        response = supabase.table(table).select("count", count="exact").execute()
        count = (
            response.count if hasattr(response, "count") else len(response.data or [])
        )
        print(f"✓ {table:20} - {count} records")
    except Exception as e:
        print(f"✗ {table:20} - Error: {str(e)[:50]}")

# Test 4: Real-time Subscription Test
print("\n[TEST 4] Real-time Listener Setup")
print("-" * 70)

try:
    from app.services.supabase_realtime_sync import supabase_sync

    if supabase_sync.is_ready():
        print("✓ Supabase Realtime Sync is ready")

        # Try to subscribe to a table
        def test_callback(payload):
            print(f"  🔔 Received event: {payload}")

        channel = supabase_sync.subscribe_to_table_changes("users", test_callback)
        if channel:
            print("✓ Successfully subscribed to 'users' table")
            time.sleep(1)
            supabase_sync.unsubscribe_from_table("users")
            print("✓ Unsubscribed from 'users' table")
        else:
            print("✗ Failed to subscribe to 'users' table")
    else:
        print("✗ Supabase Realtime Sync not ready")

except Exception as e:
    print(f"✗ Error testing real-time listeners: {e}")
    import traceback

    traceback.print_exc()

# Test 5: Test Data Sync Simulation
print("\n[TEST 5] Cloud Sync Service Check")
print("-" * 70)

try:
    from app.services.cloud_sync_service import sync_all_tables_to_cloud

    print("✓ Cloud sync service loaded successfully")
    print("  (Note: Full sync test requires active database connections)")
except Exception as e:
    print(f"✗ Failed to load cloud sync service: {e}")

# Final Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
To enable real-time sync:

1. ✅ Ensure SUPABASE_SERVICE_KEY is set in .env
   - Get it from: https://app.supabase.com → Project Settings → API

2. ✅ Set SUPABASE_SYNC_ENABLED=True in .env

3. ✅ Ensure tables exist in Supabase matching your schema

4. ✅ Start the Flask app - listeners will initialize automatically

5. ✅ Make changes to any watched table to test real-time sync

Watched tables: users, cases, activity_logs, report_exports
""")
print("=" * 70)
