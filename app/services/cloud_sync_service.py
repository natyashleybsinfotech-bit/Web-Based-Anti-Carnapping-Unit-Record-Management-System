# Supabase Real-Time Cloud Sync Service
# Comprehensive bi-directional sync between local MySQL and Supabase PostgreSQL

from datetime import datetime
from flask import current_app
from app.services.supabase_realtime_sync import supabase_sync
from app import mysql


def sync_all_tables_to_cloud(operation="push"):
    """
    Comprehensive cloud synchronization for all 6 database entities.
    Syncs: users, complainants, cases, receipts, activity_logs, hotspot

    Args:
        operation: 'push' (local to cloud) or 'pull' (cloud to local)

    Returns:
        Dictionary with detailed sync status
    """
    try:
        if not supabase_sync or not supabase_sync.is_ready():
            return {
                "status": "error",
                "message": "Supabase not configured",
                "timestamp": datetime.now().isoformat(),
            }

        sync_results = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "tables_synced": {},
            "total_records": 0,
            "errors": [],
        }

        if operation == "push":
            # Push all local data to Supabase

            # 1. SYNC USERS TABLE
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT id, full_name, username, password_hash, role, email, is_active, force_password_change, created_at
                    FROM users
                """)
                users = cur.fetchall()
                cur.close()

                if users:
                    user_records = [
                        {
                            "id": row[0],
                            "full_name": row[1],
                            "username": row[2],
                            "password_hash": row[3],
                            "role": row[4],
                            "email": row[5] if row[5] else None,
                            "is_active": bool(row[6]),
                            "force_password_change": bool(row[7]),
                            "created_at": (
                                row[8].isoformat()
                                if row[8]
                                else datetime.now().isoformat()
                            ),
                        }
                        for row in users
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "users", user_records, "insert"
                    )
                    sync_results["tables_synced"]["users"] = result.get("synced", 0)
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["users"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing users: {e}")
                sync_results["errors"].append(f"Users sync failed: {str(e)}")

            # 2. SYNC CASES TABLE
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT id, reference_no, complainant_name, complainant_email, complainant_contact,
                           incident_date, incident_location, barangay_number, vehicle_details, narrative,
                           status, assigned_officer_id, created_by, created_at, updated_at, Complainant_ID
                    FROM cases
                """)
                cases = cur.fetchall()
                cur.close()

                if cases:
                    case_records = [
                        {
                            "id": row[0],
                            "reference_no": row[1],
                            "complainant_name": row[2],
                            "complainant_email": row[3],
                            "complainant_contact": row[4] if row[4] else None,
                            "incident_date": str(row[5]) if row[5] else None,
                            "incident_location": row[6],
                            "barangay_number": row[7],
                            "vehicle_details": row[8] if row[8] else None,
                            "narrative": row[9],
                            "status": row[10],
                            "assigned_officer_id": row[11],
                            "created_by": row[12],
                            "created_at": (
                                row[13].isoformat()
                                if row[13]
                                else datetime.now().isoformat()
                            ),
                            "updated_at": (
                                row[14].isoformat()
                                if row[14]
                                else datetime.now().isoformat()
                            ),
                            "Complainant_ID": row[15],
                        }
                        for row in cases
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "cases", case_records, "insert"
                    )
                    sync_results["tables_synced"]["cases"] = result.get("synced", 0)
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["cases"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing cases: {e}")
                sync_results["errors"].append(f"Cases sync failed: {str(e)}")

            # 3. SYNC ACTIVITY_LOGS TABLE
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT id, user_id, action, description, created_at
                    FROM activity_logs
                """)
                logs = cur.fetchall()
                cur.close()

                if logs:
                    log_records = [
                        {
                            "id": row[0],
                            "user_id": row[1],
                            "action": row[2],
                            "description": row[3] if row[3] else None,
                            "created_at": (
                                row[4].isoformat()
                                if row[4]
                                else datetime.now().isoformat()
                            ),
                        }
                        for row in logs
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "activity_logs", log_records, "insert"
                    )
                    sync_results["tables_synced"]["activity_logs"] = result.get(
                        "synced", 0
                    )
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["activity_logs"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing activity logs: {e}")
                sync_results["errors"].append(f"Activity logs sync failed: {str(e)}")

            # 4. SYNC RECEIPTS TABLE (formerly report_exports)
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Receipt_ID, Receipt_Code, Date_Issued, email_sent, Case_ID, pdf_path, qr_path
                    FROM receipts
                """)
                receipts = cur.fetchall()
                cur.close()

                if receipts:
                    receipt_records = [
                        {
                            "Receipt_ID": row[0],
                            "Receipt_Code": row[1] if row[1] else None,
                            "Date_Issued": (
                                row[2].isoformat()
                                if row[2]
                                else datetime.now().isoformat()
                            ),
                            "email_sent": row[3] if row[3] else None,
                            "Case_ID": row[4],
                            "pdf_path": row[5] if row[5] else None,
                            "qr_path": row[6] if row[6] else None,
                        }
                        for row in receipts
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "receipts", receipt_records, "insert"
                    )
                    sync_results["tables_synced"]["receipts"] = result.get("synced", 0)
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["receipts"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing receipts: {e}")
                sync_results["errors"].append(f"Receipts sync failed: {str(e)}")

            # 5. SYNC COMPLAINANTS TABLE
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Complainant_ID, First_Name, Last_Name, Contact_Number, Address
                    FROM complainants
                """)
                complainants = cur.fetchall()
                cur.close()

                if complainants:
                    comp_records = [
                        {
                            "Complainant_ID": row[0],
                            "First_Name": row[1],
                            "Last_Name": row[2],
                            "Contact_Number": row[3] if row[3] else None,
                            "Address": row[4] if row[4] else None,
                        }
                        for row in complainants
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "complainants", comp_records, "insert"
                    )
                    sync_results["tables_synced"]["complainants"] = result.get(
                        "synced", 0
                    )
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["complainants"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing complainants: {e}")
                sync_results["errors"].append(f"Complainants sync failed: {str(e)}")

            # 6. SYNC HOTSPOT TABLE
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT Hotspot_ID, barangay_name, district_name, period_type, risk_level, total_cases, resolution_rate
                    FROM hotspot
                """)
                hotspots = cur.fetchall()
                cur.close()

                if hotspots:
                    hotspot_records = [
                        {
                            "Hotspot_ID": row[0],
                            "barangay_name": row[1],
                            "district_name": row[2],
                            "period_type": row[3],
                            "risk_level": row[4],
                            "total_cases": row[5],
                            "resolution_rate": row[6],
                        }
                        for row in hotspots
                    ]
                    result = supabase_sync.batch_sync_to_supabase(
                        "hotspot", hotspot_records, "insert"
                    )
                    sync_results["tables_synced"]["hotspot"] = result.get("synced", 0)
                    sync_results["total_records"] += result.get("synced", 0)
                else:
                    sync_results["tables_synced"]["hotspot"] = 0
            except Exception as e:
                current_app.logger.error(f"Error syncing hotspot: {e}")
                sync_results["errors"].append(f"Hotspot sync failed: {str(e)}")

        elif operation == "pull":
            # Pull data from Supabase to local (cloud to local)
            try:
                # 1. PULL USERS
                users = supabase_sync.pull_from_supabase("users")
                if users:
                    sync_results["tables_synced"]["users"] = len(users)
                    sync_results["total_records"] += len(users)
                else:
                    sync_results["tables_synced"]["users"] = 0

                # 2. PULL CASES
                cases = supabase_sync.pull_from_supabase("cases")
                if cases:
                    sync_results["tables_synced"]["cases"] = len(cases)
                    sync_results["total_records"] += len(cases)
                else:
                    sync_results["tables_synced"]["cases"] = 0

                # 3. PULL ACTIVITY_LOGS
                activity_logs = supabase_sync.pull_from_supabase("activity_logs")
                if activity_logs:
                    sync_results["tables_synced"]["activity_logs"] = len(activity_logs)
                    sync_results["total_records"] += len(activity_logs)
                else:
                    sync_results["tables_synced"]["activity_logs"] = 0

                # 4. PULL RECEIPTS (formerly report_exports)
                receipts = supabase_sync.pull_from_supabase("receipts")
                if receipts:
                    sync_results["tables_synced"]["receipts"] = len(receipts)
                    sync_results["total_records"] += len(receipts)
                else:
                    sync_results["tables_synced"]["receipts"] = 0

                # 5. PULL COMPLAINANTS
                complainants = supabase_sync.pull_from_supabase("complainants")
                if complainants:
                    sync_results["tables_synced"]["complainants"] = len(complainants)
                    sync_results["total_records"] += len(complainants)
                else:
                    sync_results["tables_synced"]["complainants"] = 0

                # 6. PULL HOTSPOT
                hotspot = supabase_sync.pull_from_supabase("hotspot")
                if hotspot:
                    sync_results["tables_synced"]["hotspot"] = len(hotspot)
                    sync_results["total_records"] += len(hotspot)
                else:
                    sync_results["tables_synced"]["hotspot"] = 0
            except Exception as e:
                current_app.logger.error(f"Error pulling data from Supabase: {e}")
                sync_results["errors"].append(f"Pull operation failed: {str(e)}")

        # Update status based on errors
        if sync_results["errors"]:
            if sync_results["total_records"] > 0:
                sync_results["status"] = "partial_success"
            else:
                sync_results["status"] = "error"

        current_app.logger.info(f"Sync completed: {sync_results}")
        return sync_results

    except Exception as e:
        current_app.logger.error(f"Sync error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def sync_with_cloud_database(data, table, operation="push"):
    """
    Wrapper function for syncing individual records to cloud.

    Args:
        data: Dictionary with record data
        table: Table name
        operation: 'push' or 'pull'

    Returns:
        Sync result dictionary
    """
    if not supabase_sync or not supabase_sync.is_ready():
        return {"status": "error", "message": "Supabase not configured"}

    try:
        if operation == "push":
            # Sync single record to Supabase
            if "id" in data:
                # This is an update
                result = supabase_sync.sync_record_to_supabase(
                    table, data.copy(), "update"
                )
            else:
                # This is an insert
                result = supabase_sync.sync_record_to_supabase(
                    table, data.copy(), "insert"
                )

            return {
                "status": "success" if result else "error",
                "table": table,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "info",
                "message": "Pull operation handled by real-time listeners",
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def get_sync_status():
    """Get current sync status"""
    if not supabase_sync:
        return {"status": "error", "message": "Supabase not configured"}
    return supabase_sync.get_sync_status()


def retry_failed_syncs():
    """Retry all failed sync operations"""
    if not supabase_sync or not supabase_sync.is_ready():
        return {"status": "error", "message": "Supabase not configured"}
    return supabase_sync.retry_failed_syncs()
