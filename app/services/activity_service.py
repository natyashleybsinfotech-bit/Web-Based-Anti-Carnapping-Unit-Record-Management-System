"""
Activity Logging Service
Handles detailed logging of all user activities and system events.
"""

from datetime import datetime
from flask import current_app


def log_activity(user_id, action, description=None, case_id=None, metadata=None):
    """
    Log a specific user activity with detailed information.

    Args:
        user_id: User performing the action
        action: Type of action (e.g., 'case_created', 'case_status_updated', 'login')
        description: Detailed description of the action
        case_id: Related case ID (if applicable)
        metadata: Additional metadata as dictionary

    Returns:
        Activity log record
    """
    try:
        activity_record = {
            "user_id": user_id,
            "action": action,
            "description": description,
            "case_id": case_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }

        current_app.logger.info(
            f"Activity logged: [{action}] by user {user_id} - {description}"
        )
        return {"status": "logged", "activity": activity_record}

    except Exception as e:
        current_app.logger.error(f"Error logging activity: {str(e)}")
        return {"status": "error", "message": str(e)}


def log_case_activity(user_id, case_id, action, description=None):
    """
    Log case-specific activities.

    Args:
        user_id: User performing the action
        case_id: Case ID
        action: Type of action (created, status_updated, assigned, etc.)
        description: Activity description

    Returns:
        Activity log record
    """
    try:
        case_activity = {
            "user_id": user_id,
            "case_id": case_id,
            "action": f"case_{action}",
            "description": description or f"Case {action}",
            "timestamp": datetime.now().isoformat(),
        }

        current_app.logger.info(
            f"Case activity: Case {case_id} - {action} by user {user_id}"
        )
        return {"status": "logged", "activity": case_activity}

    except Exception as e:
        current_app.logger.error(f"Error logging case activity: {str(e)}")
        return {"status": "error", "message": str(e)}


def log_login_activity(user_id, username, ip_address, success=True):
    """
    Log user login activities.

    Args:
        user_id: User ID
        username: Username
        ip_address: Client IP address
        success: Whether login was successful

    Returns:
        Login activity record
    """
    try:
        login_activity = {
            "user_id": user_id,
            "username": username,
            "action": "login",
            "status": "success" if success else "failed",
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
        }

        if success:
            current_app.logger.info(f"User {username} logged in from {ip_address}")
        else:
            current_app.logger.warning(
                f"Failed login attempt for {username} from {ip_address}"
            )

        return {"status": "logged", "activity": login_activity}

    except Exception as e:
        current_app.logger.error(f"Error logging login activity: {str(e)}")
        return {"status": "error", "message": str(e)}


def log_user_management_activity(admin_id, target_user_id, action, description=None):
    """
    Log user management activities (create, update, delete users).

    Args:
        admin_id: Admin performing the action
        target_user_id: Target user being managed
        action: Type of management action (created, updated, removed)
        description: Activity description

    Returns:
        User management activity record
    """
    try:
        user_mgmt_activity = {
            "admin_id": admin_id,
            "target_user_id": target_user_id,
            "action": f"user_{action}",
            "description": description or f"User {action}",
            "timestamp": datetime.now().isoformat(),
        }

        current_app.logger.warning(
            f"User management: User {target_user_id} was {action} by admin {admin_id}"
        )
        return {"status": "logged", "activity": user_mgmt_activity}

    except Exception as e:
        current_app.logger.error(f"Error logging user management activity: {str(e)}")
        return {"status": "error", "message": str(e)}


def log_database_activity(user_id, action, operation_type, description=None):
    """
    Log database operations (backup, restore, sync).

    Args:
        user_id: User performing the action
        action: Type of database action
        operation_type: backup, restore, or sync
        description: Operation description

    Returns:
        Database activity record
    """
    try:
        db_activity = {
            "user_id": user_id,
            "action": action,
            "operation_type": operation_type,
            "description": description or f"Database {operation_type}",
            "timestamp": datetime.now().isoformat(),
        }

        current_app.logger.warning(
            f"Database operation: {operation_type} performed by user {user_id}"
        )
        return {"status": "logged", "activity": db_activity}

    except Exception as e:
        current_app.logger.error(f"Error logging database activity: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_activity_logs(user_id=None, case_id=None, action=None, limit=100):
    """
    Retrieve activity logs with optional filters.

    Args:
        user_id: Filter by user (optional)
        case_id: Filter by case (optional)
        action: Filter by action type (optional)
        limit: Maximum records to return

    Returns:
        List of activity logs
    """
    try:
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if case_id:
            filters["case_id"] = case_id
        if action:
            filters["action"] = action

        logs = {
            "filters": filters,
            "limit": limit,
            "retrieved_at": datetime.now().isoformat(),
            "activities": [],
        }

        current_app.logger.info(f"Activity logs retrieved with filters: {filters}")
        return {"status": "success", "logs": logs}

    except Exception as e:
        current_app.logger.error(f"Error retrieving activity logs: {str(e)}")
        return {"status": "error", "message": str(e)}


def generate_activity_report(start_date, end_date, report_type="summary"):
    """
    Generate activity report for a date range.

    Args:
        start_date: Report start date
        end_date: Report end date
        report_type: 'summary' or 'detailed'

    Returns:
        Activity report
    """
    try:
        report = {
            "report_type": report_type,
            "period": {"start": start_date, "end": end_date},
            "generated_at": datetime.now().isoformat(),
            "total_activities": 0,
            "by_action_type": {},
            "by_user": {},
        }

        current_app.logger.info(
            f"Activity report generated for period {start_date} to {end_date}"
        )
        return {"status": "success", "report": report}

    except Exception as e:
        current_app.logger.error(f"Error generating activity report: {str(e)}")
        return {"status": "error", "message": str(e)}
