#!/usr/bin/env python3
"""
Test Cloud Sync with Cloudflare D1
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
database_id = os.getenv("CLOUDFLARE_DATABASE_ID", "")
api_token = os.getenv("CLOUDFLARE_API_TOKEN", "")

print("=" * 60)
print("CLOUDFLARE D1 SYNC TEST")
print("=" * 60)

print("\n✓ Configuration Loaded:")
print(f"  Account ID: {account_id[:20]}...")
print(f"  Database ID: {database_id}")
print(f"  API Token: {api_token[:20]}...")

if not all([account_id, database_id, api_token]):
    print("\n❌ ERROR: Missing Cloudflare credentials!")
    exit(1)

# Test API call
d1_api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"

headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

print(f"\n📡 Testing API Endpoint:")
print(f"  URL: {d1_api_url}")

# Test 1: Check if database connection works
print("\n[TEST 1] Checking database connection...")
try:
    test_sql = "SELECT COUNT(*) as count FROM cases;"

    response = requests.post(
        d1_api_url, json={"sql": test_sql}, headers=headers, timeout=10
    )

    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {response.text[:200]}")

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Database connection successful!")
        print(f"  Result: {result}")
    else:
        print(f"  ❌ Failed with status {response.status_code}")
        if response.status_code == 401:
            print("     Error: Invalid API token")
        elif response.status_code == 404:
            print("     Error: Invalid Account ID or Database ID")

except requests.exceptions.RequestException as e:
    print(f"  ❌ Network error: {e}")
    exit(1)

# Test 2: Try to insert a test record
print("\n[TEST 2] Inserting test case record...")
try:
    test_case_sql = """
    INSERT INTO cases (reference_no, complainant_name, complainant_email, incident_location, status, created_at) 
    VALUES ('TEST-' || datetime('now'), 'Test Complainant', 'test@email.com', 'Test Location', 'Pending', datetime('now'));
    """

    response = requests.post(
        d1_api_url, json={"sql": test_case_sql}, headers=headers, timeout=10
    )

    print(f"  Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Test record inserted successfully!")
        print(f"  Result: {result}")
    else:
        print(f"  ❌ Failed to insert: {response.text[:200]}")

except requests.exceptions.RequestException as e:
    print(f"  ❌ Network error: {e}")

# Test 3: Retrieve records
print("\n[TEST 3] Retrieving records from cloud...")
try:
    retrieve_sql = "SELECT reference_no, complainant_name, status FROM cases ORDER BY created_at DESC LIMIT 5;"

    response = requests.post(
        d1_api_url, json={"sql": retrieve_sql}, headers=headers, timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Retrieved records successfully!")
        records = result.get("result", [])
        if records:
            print(f"  Found {len(records)} records:")
            for record in records:
                print(f"    - {record}")
        else:
            print("  No records found in cloud database")
    else:
        print(f"  ❌ Failed to retrieve: {response.text[:200]}")

except requests.exceptions.RequestException as e:
    print(f"  ❌ Network error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
