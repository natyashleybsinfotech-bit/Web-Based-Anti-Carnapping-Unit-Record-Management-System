from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from datetime import datetime
import logging

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.")
                return redirect(url_for("main.login"))
            if session.get("role") not in roles:
                flash("Unauthorized access.")
                return redirect(url_for("main.login"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# Enhanced Login Management
def log_login_attempt(username, success=True, ip_address=None):
    """
    Log user login attempts with timestamp and IP address.
    
    Args:
        username: Username attempting to login
        success: Whether login was successful
        ip_address: Client IP address
    
    Returns:
        Dictionary with login status
    """
    try:
        timestamp = datetime.now().isoformat()
        status = "success" if success else "failed"
        
        log_entry = {
            "username": username,
            "status": status,
            "timestamp": timestamp,
            "ip_address": ip_address
        }
        
        if success:
            current_app.logger.info(f"Login success for user: {username} from {ip_address}")
        else:
            current_app.logger.warning(f"Login failed for user: {username} from {ip_address}")
        
        return {"status": "logged", "entry": log_entry}
    
    except Exception as e:
        current_app.logger.error(f"Error logging login attempt: {str(e)}")
        return {"status": "error", "message": str(e)}


def track_session(user_id, username, role):
    """
    Track user session with login details.
    
    Args:
        user_id: User ID
        username: Username
        role: User role (admin, officer)
    
    Returns:
        Session data
    """
    try:
        session_data = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "login_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        current_app.logger.info(f"Session started for user: {username} (role: {role})")
        return {"status": "success", "session": session_data}
    
    except Exception as e:
        current_app.logger.error(f"Error tracking session: {str(e)}")
        return {"status": "error", "message": str(e)}
