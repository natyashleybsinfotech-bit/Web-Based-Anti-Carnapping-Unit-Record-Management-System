#!/usr/bin/env python3
"""
Schema Inspection Tool - Compare Local MySQL vs Supabase PostgreSQL
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 80)
print(" SCHEMA COMPARISON: Local MySQL vs Supabase PostgreSQL")
print("=" * 80 + "\n")

from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

client = create_client(supabase_url, supabase_key)

# Tables to inspect
tables = ['users', 'cases', 'activity_logs', 'report_exports']

print("LOCAL MySQL SCHEMA (from schema.sql):")
print("-" * 80)

local_schema = {
    'users': ['id', 'full_name', 'username', 'password_hash', 'role', 'email', 'is_active', 'force_password_change', 'created_at'],
    'cases': ['id', 'reference_no', 'complainant_name', 'complainant_email', 'complainant_contact', 'incident_date', 'incident_location', 'barangay_number', 'vehicle_details', 'narrative', 'status', 'assigned_officer_id', 'created_by', 'created_at', 'updated_at'],
    'activity_logs': ['id', 'user_id', 'action', 'description', 'created_at'],
    'report_exports': ['id', 'case_id', 'pdf_path', 'qr_path', 'emailed_to', 'created_at']
}

for table, columns in local_schema.items():
    print(f"\n{table}:")
    for col in columns:
        print(f"  • {col}")

print("\n\nSUPABASE PostgreSQL SCHEMA (Current):")
print("-" * 80)

supabase_schema = {}

for table in tables:
    try:
        # Get one record to see what columns exist
        response = client.table(table).select('*').limit(1).execute()
        
        if response.data:
            columns = list(response.data[0].keys())
            supabase_schema[table] = columns
            print(f"\n{table}:")
            for col in columns:
                print(f"  • {col}")
        else:
            print(f"\n{table}: [empty table]")
    except Exception as e:
        print(f"\n{table}: ERROR - {str(e)[:80]}")

# Compare schemas
print("\n\nSCHEMA DIFFERENCES:")
print("-" * 80)

all_differences = False

for table in tables:
    local_cols = set(local_schema.get(table, []))
    supabase_cols = set(supabase_schema.get(table, []))
    
    missing_in_supabase = local_cols - supabase_cols
    extra_in_supabase = supabase_cols - local_cols
    
    if missing_in_supabase or extra_in_supabase:
        all_differences = True
        print(f"\n{table}:")
        if missing_in_supabase:
            print(f"  ❌ Missing in Supabase: {', '.join(sorted(missing_in_supabase))}")
        if extra_in_supabase:
            print(f"  ⚠️  Extra in Supabase: {', '.join(sorted(extra_in_supabase))}")

if not all_differences:
    print("\n✅ All schemas match!")

print("\n" + "=" * 80)
print(" RECOMMENDATIONS")
print("=" * 80)

print("""
To sync schemas between Local MySQL and Supabase:

Option A: Modify Supabase schema to match Local
- Go to https://app.supabase.com → SQL Editor
- Run ALTER TABLE commands to add/remove columns

Option B: Modify Local schema to match Supabase  
- Update schema.sql and run migrations
- Ensure new columns don't break existing code

Option C: Create a mapping layer
- In the sync service, map between different column names
- Handle schema differences in sync functions

Which approach do you prefer?
""")

print("=" * 80 + "\n")
