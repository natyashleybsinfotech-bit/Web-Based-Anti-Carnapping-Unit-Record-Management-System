#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script: Align database to 6-entity schema from paper.

Changes:
  1. Create 'complainants' table
  2. Populate complainants from existing cases data
  3. Add Complainant_ID FK + extra columns to cases
  4. Create 'receipts' table (renamed from report_exports)
  5. Create 'hotspot' table

Run once: python migrate_to_paper_schema.py
"""

import os
import sys

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
import MySQLdb

load_dotenv()

conn = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    db=os.getenv("MYSQL_DB", "carnapping_db"),
    autocommit=False,
)
cur = conn.cursor()


def run(sql, desc=""):
    try:
        cur.execute(sql)
        print(f"  [OK] {desc or sql[:70]}")
    except MySQLdb.OperationalError as e:
        code = e.args[0]
        if code in (1060, 1061, 1050, 1091, 1025):
            print(f"  [SKIP] Already done: {desc or sql[:70]}")
        else:
            print(f"  [ERR] [{code}]: {e.args[1]}")
            print(f"    SQL: {sql[:120]}")
    except Exception as e:
        print(f"  [ERR] UNEXPECTED: {e}")


print("\n--- STEP 1: Create 'complainants' table ---")
run(
    """
CREATE TABLE IF NOT EXISTS complainants (
    Complainant_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(100) NOT NULL,
    Last_Name VARCHAR(100) NOT NULL,
    Contact_Number VARCHAR(30),
    Address VARCHAR(255)
)
""",
    "Create complainants table",
)

print("\n--- STEP 2: Populate complainants from existing cases ---")
try:
    cur.execute("SELECT COUNT(*) FROM complainants")
    existing_count = cur.fetchone()[0]

    cur.execute(
        "SELECT id, complainant_name, complainant_email, complainant_contact FROM cases"
    )
    case_rows = cur.fetchall()

    if existing_count == 0 and case_rows:
        for case_id, full_name, email, contact in case_rows:
            parts = (full_name or "Unknown").strip().split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            cur.execute(
                "INSERT INTO complainants (First_Name, Last_Name, Contact_Number, Address) VALUES (%s, %s, %s, %s)",
                (first, last, contact, None),
            )
        print(f"  [OK] Inserted {len(case_rows)} complainant records")
    else:
        print(f"  [SKIP] complainants already has {existing_count} records")
except Exception as e:
    print(f"  [ERR] {e}")

print("\n--- STEP 3: Add Complainant_ID FK + extra columns to cases ---")
run(
    "ALTER TABLE cases ADD COLUMN Complainant_ID INT NULL",
    "Add Complainant_ID column to cases",
)
run(
    "ALTER TABLE cases ADD COLUMN Case_Title VARCHAR(255)",
    "Add Case_Title column to cases",
)
run(
    "ALTER TABLE cases ADD COLUMN Priority ENUM('Low','Normal','High') DEFAULT 'Normal'",
    "Add Priority column to cases",
)

try:
    cur.execute("SELECT id FROM cases ORDER BY id ASC")
    case_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT Complainant_ID FROM complainants ORDER BY Complainant_ID ASC")
    comp_ids = [r[0] for r in cur.fetchall()]

    for case_id, comp_id in zip(case_ids, comp_ids):
        cur.execute(
            "UPDATE cases SET Complainant_ID=%s WHERE id=%s", (comp_id, case_id)
        )
    print(f"  [OK] Mapped {len(case_ids)} cases to complainants")
except Exception as e:
    print(f"  [ERR] {e}")

run(
    "ALTER TABLE cases ADD CONSTRAINT fk_case_complainant FOREIGN KEY (Complainant_ID) REFERENCES complainants(Complainant_ID) ON DELETE RESTRICT",
    "Add FK: cases.Complainant_ID -> complainants",
)

print("\n--- STEP 4: Create 'receipts' table ---")
run(
    """
CREATE TABLE IF NOT EXISTS receipts (
    Receipt_ID INT AUTO_INCREMENT PRIMARY KEY,
    Receipt_Code VARCHAR(50),
    Date_Issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent VARCHAR(150),
    Case_ID INT NOT NULL,
    pdf_path VARCHAR(255),
    qr_path VARCHAR(255),
    FOREIGN KEY (Case_ID) REFERENCES cases(id) ON DELETE CASCADE
)
""",
    "Create receipts table",
)

try:
    cur.execute("SELECT COUNT(*) FROM receipts")
    r_count = cur.fetchone()[0]
    if r_count == 0:
        cur.execute("""
            INSERT INTO receipts (Receipt_Code, Date_Issued, email_sent, Case_ID, pdf_path, qr_path)
            SELECT NULL, created_at, emailed_to, case_id, pdf_path, qr_path
            FROM report_exports
        """)
        print(
            f"  [OK] Migrated data from report_exports -> receipts ({cur.rowcount} rows)"
        )
    else:
        print(f"  [SKIP] receipts already has {r_count} records")
except MySQLdb.ProgrammingError as e:
    if "report_exports" in str(e):
        print("  [SKIP] report_exports table not found, nothing to migrate")
    else:
        print(f"  [ERR] {e}")
except Exception as e:
    print(f"  [ERR] {e}")

print("\n--- STEP 5: Create 'hotspot' table ---")
run(
    """
CREATE TABLE IF NOT EXISTS hotspot (
    Hotspot_ID INT AUTO_INCREMENT PRIMARY KEY,
    barangay_name VARCHAR(100) NOT NULL,
    period_type ENUM('weekly','monthly') DEFAULT 'monthly',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_cases INT DEFAULT 0,
    last_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
""",
    "Create hotspot table",
)

print("\n--- STEP 6: Commit all changes ---")
try:
    conn.commit()
    print("  [OK] All changes committed successfully!")
except Exception as e:
    conn.rollback()
    print(f"  [ERR] Commit failed, rolled back: {e}")
finally:
    cur.close()
    conn.close()

print("\nMigration complete! Database now has 6 entities:")
print("   1. users           (Users)")
print("   2. complainants    (Complainants)  <- NEW")
print("   3. cases           (Cases)")
print("   4. receipts        (Receipts)      <- renamed from report_exports")
print("   5. activity_logs   (Activity_Logs)")
print("   6. hotspot         (Hotspot)       <- NEW")
