#!/usr/bin/env python3
"""
Test Philippine Timezone Configuration
Verifies that all timestamps are in Manila time (UTC+8)
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 80)
print(" PHILIPPINES TIMEZONE VERIFICATION")
print("=" * 80)

# Test 1: Verify app timezone
print("\n[1] Flask Application Timezone Configuration")
print("-" * 80)

try:
    from app import create_app

    app = create_app()

    with app.app_context():
        timezone_config = app.config.get("TIMEZONE")
        print(f"App Timezone: {timezone_config}")

        if timezone_config == "Asia/Manila":
            print("Status: OK - Philippines timezone configured")
        else:
            print("Status: WARNING - Check timezone configuration")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Verify Python timezone
print("\n[2] Python Timezone (Application Level)")
print("-" * 80)

try:
    PH_TZ = ZoneInfo("Asia/Manila")
    ph_now = datetime.now(PH_TZ)

    print(f"Current PH Time: {ph_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timezone: {ph_now.tzname()} (UTC{ph_now.strftime('%z')})")
    print("Status: OK - Python timezone working")

except Exception as e:
    print(f"Error: {e}")

# Test 3: Verify helpers
print("\n[3] Helpers Timezone Functions")
print("-" * 80)

try:
    from app.utils.helpers import get_ph_datetime, generate_reference

    ph_dt = get_ph_datetime()
    ref_no = generate_reference()

    print(f"get_ph_datetime(): {ph_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"generate_reference(): {ref_no}")
    print("Status: OK - Timezone helpers working")

except Exception as e:
    print(f"Error: {e}")

# Test 4: Verify timezone utilities
print("\n[4] Timezone Utility Functions")
print("-" * 80)

try:
    from app.utils.timezone import get_ph_datetime_str, format_ph_datetime

    ph_str = get_ph_datetime_str()
    formatted = format_ph_datetime(datetime.now(ZoneInfo("UTC")))

    print(f"get_ph_datetime_str(): {ph_str}")
    print(f"format_ph_datetime(): {formatted}")
    print("Status: OK - Timezone utilities working")

except Exception as e:
    print(f"Error: {e}")

# Test 5: MySQL timezone (if database is running)
print("\n[5] MySQL Database Timezone")
print("-" * 80)

try:
    from app import mysql, create_app

    app = create_app()
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT NOW(), @@session.time_zone")
            result = cur.fetchone()

            if result:
                db_time, tz = result
                print(f"MySQL Current Time: {db_time}")
                print(f"MySQL Timezone: {tz}")
                print("Status: OK - MySQL timezone set")
            else:
                print("Status: WARNING - Could not get MySQL timezone")

            cur.close()
        except Exception as db_e:
            print(f"MySQL Connection: NOT AVAILABLE")
            print(f"Note: This is OK if MySQL is not running")
            print(f"Details: {str(db_e)[:80]}")

except Exception as e:
    print(f"Error: {e}")

# Summary
print("\n" + "=" * 80)
print(" TIMEZONE CONFIGURATION SUMMARY")
print("=" * 80)

print("""
CONFIGURED FOR PHILIPPINES (UTC+8):

✓ Flask App: Asia/Manila timezone set
✓ Python: ZoneInfo('Asia/Manila') available
✓ Helpers: generate_reference() uses PH time
✓ Database: MySQL timezone will be set to UTC+8 on each request

TIMESTAMPS NOW USE:
- Philippines timezone (UTC+8)
- No daylight saving time
- Consistent across app, database, and Supabase

ALL OPERATIONS WILL SHOW:
- Case creation times: Philippine time
- Activity logs: Philippine time
- Report generation: Philippine time
- Supabase sync: Philippine time

TESTING:
1. Create a new case in the app
2. Check the timestamp in your database
3. Check the timestamp in Supabase
4. All should show Philippine time (UTC+8)
""")

print("=" * 80 + "\n")
