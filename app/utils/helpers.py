from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from flask import current_app, session
import qrcode

# Philippines timezone (UTC+8)
PH_TZ = ZoneInfo("Asia/Manila")


def get_ph_datetime():
    """Get current datetime in Philippine timezone"""
    return datetime.now(PH_TZ)


def generate_reference():
    return "CAR-" + get_ph_datetime().strftime("%Y%m%d%H%M%S")


def generate_qr(reference_no):
    qr_dir = Path(current_app.root_path) / "static" / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    track_url = f"{current_app.config['BASE_URL']}/track/{reference_no}"
    file_path = qr_dir / f"{reference_no}.png"
    qrcode.make(track_url).save(file_path)
    return f"qr/{reference_no}.png", track_url


# Integration Helpers for Case Management with Activity Logging
def create_case_with_logging(case_data, user_id):
    """
    Create a case and automatically log the activity.

    Args:
        case_data: Case details
        user_id: User creating the case

    Returns:
        Case creation result with activity logged
    """
    try:
        from app.services.case_service import create_case
        from app.services.activity_service import log_case_activity

        # Create the case
        case_result = create_case(case_data)

        # Log the activity
        if case_result["status"] == "success":
            log_case_activity(
                user_id=user_id,
                case_id=case_data.get("reference_no"),
                action="created",
                description=f"Case created: {case_data.get('reference_no')} - Status: opening",
            )

        return case_result

    except Exception as e:
        current_app.logger.error(f"Error in create_case_with_logging: {str(e)}")
        return {"status": "error", "message": str(e)}


def update_case_with_logging(case_id, new_status, user_id):
    """
    Update case status and log the activity.

    Args:
        case_id: Case to update
        new_status: New status
        user_id: User updating the case

    Returns:
        Update result with activity logged
    """
    try:
        from app.services.case_service import update_case_status
        from app.services.activity_service import log_case_activity

        # Update the case
        update_result = update_case_status(case_id, new_status)

        # Log the activity
        if update_result["status"] == "success":
            log_case_activity(
                user_id=user_id,
                case_id=case_id,
                action="status_updated",
                description=f"Case status updated to: {new_status}",
            )

        return update_result

    except Exception as e:
        current_app.logger.error(f"Error in update_case_with_logging: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_current_user_id():
    """Get current user ID from session."""
    return session.get("user_id")


def format_activity_log(activity):
    """Format activity log for display."""
    return {
        "timestamp": activity.get("timestamp"),
        "action": activity.get("action"),
        "description": activity.get("description"),
        "user_id": activity.get("user_id"),
        "case_id": activity.get("case_id"),
    }


def validate_case_status(status):
    """Validate case status is valid."""
    valid_statuses = ["opening", "pending", "closed"]
    return status in valid_statuses
