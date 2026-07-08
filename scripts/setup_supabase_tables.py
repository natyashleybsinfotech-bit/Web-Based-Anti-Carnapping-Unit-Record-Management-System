#!/usr/bin/env python3
"""
Supabase Table Setup Script
Creates all necessary PostgreSQL tables in Supabase to match the MySQL schema.

IMPORTANT: You must first enable the Realtime feature in Supabase for these tables!

Usage:
    python setup_supabase_tables.py
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    sys.exit(1)


def create_supabase_tables():
    """Create all required tables in Supabase PostgreSQL"""

    try:
        # Create client - using service key for admin operations if available
        client: Client = create_client(
            SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
        )

        print("🔄 Connecting to Supabase...")

        # Test connection
        result = client.table("users").select("id", count="exact").limit(1).execute()
        print("✓ Connected to Supabase!")
        print("✓ Tables appear to exist already")
        print(
            "\nNote: If tables don't exist, use Supabase Dashboard SQL Editor to run:"
        )
        print(get_sql_schema())
        return True

    except Exception as e:
        if "does not exist" in str(e) or "no relation" in str(e).lower():
            print("\n⚠️  Tables don't exist yet. Creating SQL schema...\n")
            print("=" * 80)
            print("COPY AND PASTE THE FOLLOWING SQL INTO SUPABASE SQL EDITOR:")
            print("=" * 80)
            print(get_sql_schema())
            print("=" * 80)
            print("\n1. Go to: https://app.supabase.com/project/<your-project>/sql")
            print("2. Click 'New Query'")
            print("3. Paste the SQL above")
            print("4. Click 'Run'")
            print("5. Then run this script again to verify")
            return False
        else:
            print(f"❌ Connection error: {e}")
            return False


def get_sql_schema():
    """Returns the SQL schema for Supabase PostgreSQL"""
    return """
-- Disable RLS temporarily for setup (enable it after)
ALTER PUBLICATION supabase_realtime DROP ALL;

-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'officer',
    email VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    force_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create cases table
CREATE TABLE IF NOT EXISTS public.cases (
    id INTEGER PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE NOT NULL,
    complainant_name VARCHAR(100) NOT NULL,
    complainant_email VARCHAR(150) NOT NULL,
    complainant_contact VARCHAR(30),
    incident_date DATE NOT NULL,
    incident_location VARCHAR(255) NOT NULL,
    barangay_number INTEGER,
    vehicle_details VARCHAR(255),
    narrative TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    assigned_officer_id INTEGER,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_officer_id) REFERENCES public.users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create activity_logs table
CREATE TABLE IF NOT EXISTS public.activity_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create report_exports table
CREATE TABLE IF NOT EXISTS public.report_exports (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    pdf_path VARCHAR(255),
    qr_path VARCHAR(255),
    emailed_to VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES public.cases(id) ON DELETE CASCADE
);

-- Enable real-time for all tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.users;
ALTER PUBLICATION supabase_realtime ADD TABLE public.cases;
ALTER PUBLICATION supabase_realtime ADD TABLE public.activity_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.report_exports;

-- Ensure full row data is sent for updates and deletes
ALTER TABLE public.users REPLICA IDENTITY FULL;
ALTER TABLE public.cases REPLICA IDENTITY FULL;
ALTER TABLE public.activity_logs REPLICA IDENTITY FULL;
ALTER TABLE public.report_exports REPLICA IDENTITY FULL;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);
CREATE INDEX IF NOT EXISTS idx_cases_reference_no ON public.cases(reference_no);
CREATE INDEX IF NOT EXISTS idx_cases_assigned_officer ON public.cases(assigned_officer_id);
CREATE INDEX IF NOT EXISTS idx_cases_created_by ON public.cases(created_by);
CREATE INDEX IF NOT EXISTS idx_cases_status ON public.cases(status);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_case_id ON public.report_exports(case_id);

-- Optional: Enable Row Level Security (RLS) - configure policies as needed
-- ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.report_exports ENABLE ROW LEVEL SECURITY;

-- Trigger function to update the updated_at column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to cases table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at') THEN
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON public.cases
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- All tables created and real-time enabled!
"""


def verify_tables():
    """Verify that all tables exist and are properly configured"""
    try:
        client: Client = create_client(
            SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
        )

        tables = ["users", "cases", "activity_logs", "report_exports"]
        print("\n🔍 Verifying tables...")

        for table_name in tables:
            try:
                result = (
                    client.table(table_name)
                    .select("id", count="exact")
                    .limit(1)
                    .execute()
                )
                count = result.count
                print(f"  ✓ {table_name:<20} - OK (record count: {count})")
            except Exception as e:
                print(f"  ❌ {table_name:<20} - MISSING")
                return False

        print("\n✓ All tables verified successfully!")
        return True

    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


def main():
    print("=" * 80)
    print("SUPABASE TABLE SETUP")
    print("=" * 80)
    print(f"\nSUPABASE_URL: {SUPABASE_URL}")
    print(f"Using: {'Service Key' if SUPABASE_SERVICE_KEY else 'Anon Key'}")

    if not create_supabase_tables():
        print(
            "\n⚠️  Please create the tables using the SQL above, then run this script again."
        )
        sys.exit(1)

    # Verify tables
    if not verify_tables():
        print("\n⚠️  Tables are not configured correctly.")
        print("Please review the SQL schema and try again.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("✓ SETUP COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run your Flask app: python run.py")
    print("2. The app will automatically sync your local MySQL data to Supabase")
    print("3. Check the logs to verify real-time sync is working")
    print("\nTo monitor syncing:")
    print("  - Go to: http://127.0.0.1:5000/api/sync/status")
    print("  - Monitor logs for sync events")


if __name__ == "__main__":
    main()
