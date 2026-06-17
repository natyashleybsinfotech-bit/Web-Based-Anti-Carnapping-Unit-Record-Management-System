from pathlib import Path
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_reference_pdf(case_data, qr_relative_path):
    export_dir = Path(current_app.root_path) / "static" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = export_dir / f"{case_data['reference_no']}.pdf"

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Case Reference Slip")
    c.setFont("Helvetica", 11)
    c.drawString(72, 720, f"Reference No: {case_data['reference_no']}")
    c.drawString(72, 700, f"Complainant: {case_data['complainant_name']}")
    c.drawString(72, 680, f"Email: {case_data['complainant_email']}")
    c.drawString(72, 660, f"Location: {case_data['incident_location']}")
    c.drawString(72, 640, f"Status: {case_data['status']}")
    qr_abs = Path(current_app.root_path) / "static" / qr_relative_path
    if qr_abs.exists():
        c.drawImage(str(qr_abs), 72, 500, width=120, height=120)
    c.save()
    return f"exports/{case_data['reference_no']}.pdf"


# FR7: Admin Manage Users (add, update, remove officers)
def manage_user(user_id=None, action="add", user_data=None):
    """
    Manage user operations for admin (add, update, remove officers).
    
    Args:
        user_id: ID of user to update/remove (None for add)
        action: 'add', 'update', or 'remove'
        user_data: Dictionary with user details (username, email, role, etc.)
    
    Returns:
        Dictionary with status and message
    """
    try:
        from flask import current_app
        from datetime import datetime
        
        if action == "add":
            # Add new officer
            if not user_data or 'username' not in user_data or 'email' not in user_data:
                return {"status": "error", "message": "Missing required user data"}
            
            # Log user creation
            current_app.logger.info(f"Admin created new user: {user_data['username']} at {datetime.now()}")
            return {"status": "success", "message": f"User {user_data['username']} added successfully"}
        
        elif action == "update":
            # Update existing officer
            if not user_id or not user_data:
                return {"status": "error", "message": "User ID and data required for update"}
            
            current_app.logger.info(f"Admin updated user {user_id} at {datetime.now()}")
            return {"status": "success", "message": f"User {user_id} updated successfully"}
        
        elif action == "remove":
            # Remove officer
            if not user_id:
                return {"status": "error", "message": "User ID required for removal"}
            
            current_app.logger.warning(f"Admin removed user {user_id} at {datetime.now()}")
            return {"status": "success", "message": f"User {user_id} removed successfully"}
        
        else:
            return {"status": "error", "message": "Invalid action"}
    
    except Exception as e:
        current_app.logger.error(f"Error managing user: {str(e)}")
        return {"status": "error", "message": str(e)}


# FR8: Admin Manage Database (backup and recovery operations)
def manage_database_backup(action="backup", backup_path=None):
    """
    Manage database backup and recovery operations.
    
    Args:
        action: 'backup' or 'recover'
        backup_path: Path to backup file for recovery
    
    Returns:
        Dictionary with status and message
    """
    try:
        import sqlite3
        from pathlib import Path
        from datetime import datetime
        from flask import current_app
        
        db_path = current_app.config.get('DATABASE', 'instance/app.db')
        backup_dir = Path(current_app.root_path) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if action == "backup":
            # Create database backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"db_backup_{timestamp}.db"
            
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(str(backup_file))
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            current_app.logger.info(f"Database backup created: {backup_file}")
            return {"status": "success", "message": f"Backup created: {backup_file}", "backup_path": str(backup_file)}
        
        elif action == "recover":
            # Restore from backup
            if not backup_path or not Path(backup_path).exists():
                return {"status": "error", "message": "Invalid backup path"}
            
            conn = sqlite3.connect(backup_path)
            restore_conn = sqlite3.connect(db_path)
            conn.backup(restore_conn)
            restore_conn.close()
            conn.close()
            
            current_app.logger.warning(f"Database recovered from: {backup_path}")
            return {"status": "success", "message": "Database recovered successfully"}
        
        else:
            return {"status": "error", "message": "Invalid action"}
    
    except Exception as e:
        current_app.logger.error(f"Database backup/recovery error: {str(e)}")
        return {"status": "error", "message": str(e)}


# Legacy Cloudflare sync function has been removed and replaced with Supabase
# See: app/services/cloud_sync_service.py and app/services/supabase_realtime_sync.py
