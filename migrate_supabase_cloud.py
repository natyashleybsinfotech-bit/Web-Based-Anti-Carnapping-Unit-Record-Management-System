#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Cloud Migration Script
Adds the 3 missing tables (complainants, receipts, hotspot) to the Supabase
cloud database to match the 6-entity paper schema, then pushes all local data.

Run: python migrate_supabase_cloud.py
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SERVICE_KEY:
    print("[ERR] SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

# ── Headers for Supabase REST / RPC calls ──────────────────────────────────
HEADERS = {
    "apikey":        SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal"
}


def run_sql(sql: str, label: str = ""):
    """Execute arbitrary SQL via the Supabase REST /sql endpoint (service key)."""
    url = f"{SUPABASE_URL}/rest/v1/sql"
    resp = requests.post(url, headers=HEADERS, json={"query": sql}, timeout=30)
    if resp.status_code in (200, 201, 204):
        print(f"  [OK] {label}")
        return True
    else:
        # Try the pg-meta endpoint (older Supabase projects)
        url2 = f"{SUPABASE_URL}/pg/query"
        resp2 = requests.post(url2, headers=HEADERS, json={"query": sql}, timeout=30)
        if resp2.status_code in (200, 201, 204):
            print(f"  [OK] {label}")
            return True
        print(f"  [ERR] {label}")
        print(f"        HTTP {resp.status_code}: {resp.text[:200]}")
        return False


def table_exists(table_name: str) -> bool:
    """Check if a table exists by doing a HEAD request against it."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=0"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    return resp.status_code == 200


def push_local_data():
    """Push local MySQL data to the new Supabase tables."""
    import MySQLdb
    conn = MySQLdb.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        db=os.getenv("MYSQL_DB", "carnapping_db"),
    )
    cur = conn.cursor()

    # Helper: upsert records via Supabase REST
    def upsert(table, records, on_conflict=""):
        if not records:
            return 0
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {**HEADERS, "Prefer": f"resolution=merge-duplicates,return=minimal"}
        resp = requests.post(url, headers=headers, json=records, timeout=30)
        if resp.status_code in (200, 201, 204):
            return len(records)
        else:
            print(f"    [WARN] Upsert to {table} failed: {resp.status_code} {resp.text[:150]}")
            return 0

    total = 0

    # 1. Push complainants
    print("\n  Pushing complainants...")
    cur.execute("SELECT Complainant_ID, First_Name, Last_Name, Contact_Number, Address FROM complainants")
    rows = cur.fetchall()
    records = [
        {"Complainant_ID": r[0], "First_Name": r[1], "Last_Name": r[2],
         "Contact_Number": r[3], "Address": r[4]}
        for r in rows
    ]
    n = upsert("complainants", records)
    print(f"    [OK] {n} complainant records pushed")
    total += n

    # 2. Update cases with Complainant_ID + new columns
    print("\n  Pushing updated cases (Complainant_ID, Case_Title, Priority)...")
    cur.execute("""
        SELECT id, Complainant_ID, Case_Title, Priority
        FROM cases
        WHERE Complainant_ID IS NOT NULL
    """)
    rows = cur.fetchall()
    # Patch each case individually (PATCH by id)
    ok = 0
    for r in rows:
        case_id, comp_id, title, priority = r
        url = f"{SUPABASE_URL}/rest/v1/cases?id=eq.{case_id}"
        patch_headers = {**HEADERS, "Prefer": "return=minimal"}
        body = {"Complainant_ID": comp_id}
        if title:
            body["Case_Title"] = title
        if priority:
            body["Priority"] = priority
        resp = requests.patch(url, headers=patch_headers, json=body, timeout=10)
        if resp.status_code in (200, 201, 204):
            ok += 1
        # silently skip missing cases on cloud (they may not exist yet)
    print(f"    [OK] {ok} cases updated with Complainant_ID")

    # 3. Push receipts
    print("\n  Pushing receipts...")
    cur.execute("""
        SELECT Receipt_ID, Receipt_Code, Date_Issued, email_sent, Case_ID, pdf_path, qr_path
        FROM receipts
    """)
    rows = cur.fetchall()
    from datetime import datetime
    records = [
        {
            "Receipt_ID":   r[0],
            "Receipt_Code": r[1],
            "Date_Issued":  r[2].isoformat() if r[2] else datetime.now().isoformat(),
            "email_sent":   r[3],
            "Case_ID":      r[4],
            "pdf_path":     r[5],
            "qr_path":      r[6]
        }
        for r in rows
    ]
    n = upsert("receipts", records)
    print(f"    [OK] {n} receipt records pushed")
    total += n

    # 4. Push hotspot (likely empty, but push anyway)
    print("\n  Pushing hotspot records...")
    cur.execute("SELECT Hotspot_ID, barangay_name, period_type, period_start, period_end, total_cases, last_generated FROM hotspot")
    rows = cur.fetchall()
    records = [
        {
            "Hotspot_ID":     r[0],
            "barangay_name":  r[1],
            "period_type":    r[2],
            "period_start":   str(r[3]) if r[3] else None,
            "period_end":     str(r[4]) if r[4] else None,
            "total_cases":    r[5],
            "last_generated": r[6].isoformat() if r[6] else None
        }
        for r in rows
    ]
    n = upsert("hotspot", records)
    print(f"    [OK] {n} hotspot records pushed")
    total += n

    cur.close()
    conn.close()
    return total


# ──────────────────────────────────────────────────────────────────────────────
# SQL statements to create the 3 missing tables + alter existing ones
# ──────────────────────────────────────────────────────────────────────────────

NEW_TABLES_SQL = """
-- ============================================================
-- TABLE: complainants
-- ============================================================
CREATE TABLE IF NOT EXISTS public.complainants (
    "Complainant_ID" SERIAL PRIMARY KEY,
    "First_Name"     VARCHAR(100) NOT NULL,
    "Last_Name"      VARCHAR(100) NOT NULL,
    "Contact_Number" VARCHAR(30),
    "Address"        VARCHAR(255)
);

-- ============================================================
-- TABLE: receipts  (replaces report_exports)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.receipts (
    "Receipt_ID"   SERIAL PRIMARY KEY,
    "Receipt_Code" VARCHAR(50),
    "Date_Issued"  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "email_sent"   VARCHAR(150),
    "Case_ID"      INTEGER NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
    "pdf_path"     VARCHAR(255),
    "qr_path"      VARCHAR(255)
);

-- ============================================================
-- TABLE: hotspot
-- ============================================================
CREATE TABLE IF NOT EXISTS public.hotspot (
    "Hotspot_ID"    SERIAL PRIMARY KEY,
    "barangay_name" VARCHAR(100) NOT NULL,
    "period_type"   VARCHAR(10) DEFAULT 'monthly',
    "period_start"  DATE NOT NULL,
    "period_end"    DATE NOT NULL,
    "total_cases"   INTEGER DEFAULT 0,
    "last_generated" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Alter cases: add Complainant_ID FK + new columns
-- ============================================================
ALTER TABLE public.cases
    ADD COLUMN IF NOT EXISTS "Complainant_ID" INTEGER REFERENCES public.complainants("Complainant_ID") ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS "Case_Title"     VARCHAR(255),
    ADD COLUMN IF NOT EXISTS "Priority"       VARCHAR(10) DEFAULT 'Normal';

-- ============================================================
-- Enable Realtime for new tables
-- ============================================================
DO $$
BEGIN
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.complainants;
    EXCEPTION WHEN others THEN NULL;
    END;
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.receipts;
    EXCEPTION WHEN others THEN NULL;
    END;
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.hotspot;
    EXCEPTION WHEN others THEN NULL;
    END;
END $$;

-- REPLICA IDENTITY FULL for change tracking
ALTER TABLE public.complainants REPLICA IDENTITY FULL;
ALTER TABLE public.receipts     REPLICA IDENTITY FULL;
ALTER TABLE public.hotspot      REPLICA IDENTITY FULL;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_receipts_case_id       ON public.receipts("Case_ID");
CREATE INDEX IF NOT EXISTS idx_complainants_last_name  ON public.complainants("Last_Name");
CREATE INDEX IF NOT EXISTS idx_hotspot_barangay        ON public.hotspot("barangay_name");
"""


def main():
    print("=" * 60)
    print("  SUPABASE CLOUD MIGRATION  (6-Entity Paper Schema)")
    print("=" * 60)
    print(f"\n  Project: {SUPABASE_URL}")

    # ── Step 1: Check connection ──────────────────────────────
    print("\n[STEP 1] Checking Supabase connection...")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users?limit=0", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print(f"  [ERR] Cannot reach Supabase: {r.status_code} {r.text[:100]}")
        print("\n  The SQL needs to be run manually. Printing it now...")
        print_manual_sql()
        sys.exit(1)
    print("  [OK] Connected to Supabase")

    # ── Step 2: Run DDL via SQL endpoint ─────────────────────
    print("\n[STEP 2] Creating/altering tables via SQL...")
    success = run_sql(NEW_TABLES_SQL, "Create complainants, receipts, hotspot; alter cases")

    if not success:
        print("\n  [WARN] Could not execute SQL automatically.")
        print("  Please run the following SQL manually in the Supabase SQL Editor:")
        print_manual_sql()
        print("\n  After running the SQL, re-run this script with --push-only flag.")
        # Still try to push data if tables already exist
        if "--push-only" not in sys.argv:
            sys.exit(1)

    # ── Step 3: Push local data ───────────────────────────────
    print("\n[STEP 3] Pushing local MySQL data to new cloud tables...")
    try:
        total = push_local_data()
        print(f"\n  [OK] Pushed {total} records to Supabase")
    except Exception as e:
        print(f"\n  [ERR] Data push failed: {e}")

    # ── Step 4: Verify ────────────────────────────────────────
    print("\n[STEP 4] Verifying tables...")
    tables = {
        "users":         "User_ID / id",
        "complainants":  "Complainant_ID",
        "cases":         "id / Case_ID",
        "receipts":      "Receipt_ID",
        "activity_logs": "Log_ID / id",
        "hotspot":       "Hotspot_ID"
    }
    all_ok = True
    for tbl, pk_hint in tables.items():
        if table_exists(tbl):
            print(f"  [OK] {tbl:<20} exists  (PK: {pk_hint})")
        else:
            print(f"  [ERR] {tbl:<20} MISSING!")
            all_ok = False

    print()
    if all_ok:
        print("=" * 60)
        print("  SUCCESS! All 6 cloud tables are now in sync.")
        print("=" * 60)
    else:
        print("  Some tables are still missing. Run the manual SQL below.")
        print_manual_sql()


def print_manual_sql():
    print("\n" + "=" * 60)
    print("PASTE THIS INTO: https://app.supabase.com/project/_/sql/new")
    print("=" * 60)
    print(NEW_TABLES_SQL)
    print("=" * 60)


if __name__ == "__main__":
    main()
