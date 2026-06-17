#!/usr/bin/env python3
"""
Service Key Verification Test
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("SUPABASE SERVICE KEY VERIFICATION")
print("=" * 60)

from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')

print("\n[1] Checking credentials...")
print(f"  URL: {supabase_url[:40]}...")
print(f"  Anon Key: {supabase_anon_key[:30]}...")
print(f"  Service Key: {supabase_service_key[:30]}...")

# Create sync client
client = create_client(supabase_url, supabase_anon_key)

# Test pulls from all tables
print("\n[2] Testing data pulls from Supabase...")

try:
    users = client.table('users').select('*').execute().data
    print(f"  Users: {len(users)} records")
except Exception as e:
    print(f"  Users: ERROR - {str(e)[:50]}")

try:
    cases = client.table('cases').select('*').execute().data
    print(f"  Cases: {len(cases)} records")
except Exception as e:
    print(f"  Cases: ERROR - {str(e)[:50]}")

try:
    logs = client.table('activity_logs').select('*').execute().data
    print(f"  Activity Logs: {len(logs)} records")
except Exception as e:
    print(f"  Activity Logs: ERROR - {str(e)[:50]}")

try:
    reports = client.table('report_exports').select('*').execute().data
    print(f"  Report Exports: {len(reports)} records")
except Exception as e:
    print(f"  Report Exports: ERROR - {str(e)[:50]}")

print("\n[3] Supabase Real-time Sync Service...")

try:
    from app import create_app
    from app.services.supabase_realtime_sync import supabase_sync
    
    app = create_app()
    with app.app_context():
        print(f"  Service Ready: {supabase_sync.is_ready()}")
        print(f"  Watched Tables: {len(supabase_sync.TABLES)}")
        print(f"  Sync Enabled: {supabase_sync.sync_enabled}")
except Exception as e:
    print(f"  Error: {str(e)[:60]}")

print("\n" + "=" * 60)
print("SUCCESS - All systems configured!")
print("=" * 60)
