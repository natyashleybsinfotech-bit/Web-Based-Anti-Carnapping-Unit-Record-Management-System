# Python script to add cloud sync routes
with open("app/routes.py", "r") as f:
    content = f.read()

# Find the location where we should insert the cloud sync routes
# Insert before the Activity Log section
insert_marker = (
    "# =========================\n# Activity Log\n# ========================="
)
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("ERROR: Could not find Activity Log section")
    exit(1)

# Define the cloud sync routes code
cloud_sync_routes_code = '''# =========================
# Cloud Synchronization (FR9)
# =========================
@bp.route("/cloud-sync/manual", methods=["POST"])
@login_required
@role_required("admin")
def manual_cloud_sync():
    """Manually trigger cloud synchronization"""
    try:
        from .services.cloud_sync_service import sync_all_tables_to_cloud
        
        result = sync_all_tables_to_cloud(operation="push")
        
        # Log the sync action
        log_activity(session.get("user_id"), "Cloud Sync", f"Manual cloud sync: {result['status']}")
        
        if result["status"] == "success" or result["status"] == "partial_success":
            total = result.get("total_records", 0)
            tables = len(result.get("tables_synced", {}))
            flash(f"Cloud sync completed: {total} records from {tables} tables synced successfully.")
        else:
            flash(f"Cloud sync failed: {result.get('message', 'Unknown error')}")
        
        return redirect(url_for("main.cloud_sync_status"))
    
    except Exception as e:
        print("CLOUD SYNC ERROR:", e)
        flash(f"Error syncing to cloud: {e}")
        return redirect(url_for("main.cloud_sync_status"))


@bp.route("/cloud-sync/status")
@login_required
@role_required("admin")
def cloud_sync_status():
    """Display cloud synchronization status and history"""
    sync_history = []
    cloud_status = {}
    
    try:
        # Get cloud configuration status
        cloud_status = {
            "configured": bool(current_app.config.get('CLOUDFLARE_ACCOUNT_ID')),
            "account_id": current_app.config.get('CLOUDFLARE_ACCOUNT_ID', '')[:8] + '...' if current_app.config.get('CLOUDFLARE_ACCOUNT_ID') else 'Not configured',
            "database_id": current_app.config.get('CLOUDFLARE_DATABASE_ID', '')[:8] + '...' if current_app.config.get('CLOUDFLARE_DATABASE_ID') else 'Not configured'
        }
        
        # Get recent sync activity from activity logs
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.created_at, u.username, a.action, a.description
            FROM activity_logs a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.action = 'Cloud Sync'
            ORDER BY a.created_at DESC
            LIMIT 20
        """)
        sync_history = cur.fetchall()
        cur.close()
    
    except Exception as e:
        print("CLOUD SYNC STATUS ERROR:", e)
        flash(f"Error loading sync status: {e}")
    
    return render_template("cloud_sync_status.html", sync_history=sync_history, cloud_status=cloud_status)


# =========================
# Activity Log
# ========================='''

# Insert the cloud sync routes before the Activity Log section
new_content = (
    content[:insert_pos]
    + cloud_sync_routes_code
    + "\n"
    + content[insert_pos + len(insert_marker) :]
)

# Write back to the file
with open("app/routes.py", "w") as f:
    f.write(new_content)

print("✓ Cloud sync routes added successfully")
