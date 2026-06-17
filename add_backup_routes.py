# Script to add backup routes to routes.py
with open('app/routes.py', 'r') as f:
    content = f.read()

# Find the location where we should insert the backup routes
insert_marker = '@bp.route("/reports")'
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("ERROR: Could not find reports route")
    exit(1)

# Define the backup routes code
backup_routes_code = '''
# =========================
# Database Backup & Recovery (FR8)
# =========================
@bp.route("/database/backup", methods=["POST"])
@login_required
@role_required("admin")
def backup_database():
    """Create database backup"""
    try:
        from pathlib import Path
        from datetime import datetime
        import os
        
        # Create backup directory
        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sql"
        backup_path = backup_dir / backup_filename
        
        # MySQL dump command
        db_name = current_app.config.get('MYSQL_DB', 'carnapping_db')
        db_user = current_app.config.get('MYSQL_USER', 'root')
        db_password = current_app.config.get('MYSQL_PASSWORD', '')
        db_host = current_app.config.get('MYSQL_HOST', 'localhost')
        
        # Build mysqldump command
        dump_cmd = f"mysqldump -h {db_host} -u {db_user}"
        if db_password:
            dump_cmd += f" -p{db_password}"
        dump_cmd += f" {db_name} > \\"{backup_path}\\""
        
        # Execute backup
        result = os.system(dump_cmd)
        
        if result == 0:
            log_activity(session.get("user_id"), "Database Backup", f"Created backup: {backup_filename}")
            flash(f"Database backup created successfully: {backup_filename}")
        else:
            flash("Error creating database backup. Check if mysqldump is installed.")
        
        return redirect(url_for("main.manage_backups"))
    
    except Exception as e:
        print("BACKUP ERROR:", e)
        flash(f"Error creating backup: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/backups")
@login_required
@role_required("admin")
def manage_backups():
    """List all database backups"""
    backups = []
    
    try:
        from pathlib import Path
        import os
        from datetime import datetime
        
        backup_dir = Path(current_app.root_path) / "static" / "backups"
        
        if backup_dir.exists():
            for backup_file in sorted(backup_dir.glob("*.sql"), reverse=True):
                file_size = backup_file.stat().st_size / (1024 * 1024)  # Convert to MB
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                backups.append({
                    "name": backup_file.name,
                    "size_mb": f"{file_size:.2f}",
                    "created_at": file_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": file_time.timestamp()
                })
    
    except Exception as e:
        print("MANAGE BACKUPS ERROR:", e)
        flash(f"Error loading backups: {e}")
    
    return render_template("manage_backups.html", backups=backups)


@bp.route("/database/restore/<backup_name>", methods=["POST"])
@login_required
@role_required("admin")
def restore_database(backup_name):
    """Restore database from backup"""
    try:
        from pathlib import Path
        import os
        
        # Validate backup name (prevent directory traversal)
        if ".." in backup_name or "/" in backup_name:
            flash("Invalid backup file.")
            return redirect(url_for("main.manage_backups"))
        
        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_path = backup_dir / backup_name
        
        if not backup_path.exists():
            flash("Backup file not found.")
            return redirect(url_for("main.manage_backups"))
        
        # MySQL restore command
        db_name = current_app.config.get('MYSQL_DB', 'carnapping_db')
        db_user = current_app.config.get('MYSQL_USER', 'root')
        db_password = current_app.config.get('MYSQL_PASSWORD', '')
        db_host = current_app.config.get('MYSQL_HOST', 'localhost')
        
        # Build mysql command
        restore_cmd = f"mysql -h {db_host} -u {db_user}"
        if db_password:
            restore_cmd += f" -p{db_password}"
        restore_cmd += f" {db_name} < \\"{backup_path}\\""
        
        # Execute restore
        result = os.system(restore_cmd)
        
        if result == 0:
            log_activity(session.get("user_id"), "Database Restore", f"Restored from: {backup_name}")
            flash(f"Database restored successfully from {backup_name}")
        else:
            flash("Error restoring database.")
        
        return redirect(url_for("main.manage_backups"))
    
    except Exception as e:
        print("RESTORE ERROR:", e)
        flash(f"Error restoring database: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/delete-backup/<backup_name>", methods=["POST"])
@login_required
@role_required("admin")
def delete_backup(backup_name):
    """Delete a backup file"""
    try:
        from pathlib import Path
        
        # Validate backup name (prevent directory traversal)
        if ".." in backup_name or "/" in backup_name:
            flash("Invalid backup file.")
            return redirect(url_for("main.manage_backups"))
        
        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_path = backup_dir / backup_name
        
        if not backup_path.exists():
            flash("Backup file not found.")
            return redirect(url_for("main.manage_backups"))
        
        # Delete backup
        backup_path.unlink()
        
        log_activity(session.get("user_id"), "Backup Deleted", f"Deleted backup: {backup_name}")
        flash(f"Backup '{backup_name}' deleted successfully.")
        return redirect(url_for("main.manage_backups"))
    
    except Exception as e:
        print("DELETE BACKUP ERROR:", e)
        flash(f"Error deleting backup: {e}")
        return redirect(url_for("main.manage_backups"))


'''

# Find and replace the Reports section header to insert backup routes before it
old_section = '@bp.route("/reports")'
new_section = backup_routes_code + '\n# =========================\n# Reports\n# =========================\n@bp.route("/reports")'

new_content = content.replace(old_section, new_section)

# Write back to the file
with open('app/routes.py', 'w') as f:
    f.write(new_content)

print("✓ Backup routes added successfully")
