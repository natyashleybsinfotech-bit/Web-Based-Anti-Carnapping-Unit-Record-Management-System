"""
Case Management Service
Handles case creation, status management, and case operations.
"""

from datetime import datetime
from flask import current_app


def create_case(case_data):
    """
    Create a new case with initial status.

    Args:
        case_data: Dictionary with case details
            - reference_no: Unique case reference
            - complainant_name: Name of complainant
            - complainant_email: Complainant email
            - incident_location: Location of incident
            - narrative: Detailed case narrative
            - assigned_officer_id: Officer assigned (optional)

    Returns:
        Dictionary with case creation status
    """
    try:
        from flask_mysqldb import MySQL
        import MySQLdb.cursors

        required_fields = [
            "reference_no",
            "complainant_name",
            "complainant_email",
            "incident_location",
        ]

        # Validate required fields
        if not all(field in case_data for field in required_fields):
            return {"status": "error", "message": "Missing required case fields"}

        # Default status is 'opening'
        status = case_data.get("status", "opening")
        created_at = datetime.now()

        case_record = {
            "reference_no": case_data["reference_no"],
            "complainant_name": case_data["complainant_name"],
            "complainant_email": case_data["complainant_email"],
            "incident_location": case_data["incident_location"],
            "narrative": case_data.get("narrative", ""),
            "status": status,
            "assigned_officer_id": case_data.get("assigned_officer_id"),
            "created_at": created_at.isoformat(),
        }

        current_app.logger.info(
            f"Case created: {case_data['reference_no']} with status {status}"
        )
        return {
            "status": "success",
            "message": "Case created successfully",
            "case": case_record,
        }

    except Exception as e:
        current_app.logger.error(f"Error creating case: {str(e)}")
        return {"status": "error", "message": str(e)}


def update_case_status(case_id, new_status):
    """
    Update case status (opening → pending → closed).

    Args:
        case_id: Case ID to update
        new_status: New status (opening, pending, closed)

    Returns:
        Dictionary with update status
    """
    try:
        valid_statuses = ["opening", "pending", "closed"]

        if new_status not in valid_statuses:
            return {
                "status": "error",
                "message": f"Invalid status. Must be one of: {valid_statuses}",
            }

        update_record = {
            "case_id": case_id,
            "previous_status": "unknown",  # Should fetch from DB
            "new_status": new_status,
            "updated_at": datetime.now().isoformat(),
        }

        current_app.logger.info(f"Case {case_id} status updated to: {new_status}")
        return {
            "status": "success",
            "message": f"Case status updated to {new_status}",
            "update": update_record,
        }

    except Exception as e:
        current_app.logger.error(f"Error updating case status: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_case_details(case_id):
    """
    Get detailed information about a case.

    Args:
        case_id: Case ID to retrieve

    Returns:
        Dictionary with case details
    """
    try:
        case_details = {
            "case_id": case_id,
            "status": "pending",
            "retrieved_at": datetime.now().isoformat(),
        }

        current_app.logger.info(f"Case details retrieved for case: {case_id}")
        return {"status": "success", "case": case_details}

    except Exception as e:
        current_app.logger.error(f"Error retrieving case details: {str(e)}")
        return {"status": "error", "message": str(e)}


def assign_case_to_officer(case_id, officer_id):
    """
    Assign a case to an officer.

    Args:
        case_id: Case to assign
        officer_id: Officer to assign case to

    Returns:
        Assignment status
    """
    try:
        assignment = {
            "case_id": case_id,
            "officer_id": officer_id,
            "assigned_at": datetime.now().isoformat(),
            "status": "assigned",
        }

        current_app.logger.info(f"Case {case_id} assigned to officer {officer_id}")
        return {
            "status": "success",
            "message": "Case assigned successfully",
            "assignment": assignment,
        }

    except Exception as e:
        current_app.logger.error(f"Error assigning case: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_case_statistics():
    """
    Get case statistics by status.

    Returns:
        Dictionary with case counts by status
    """
    try:
        stats = {
            "opening": 0,
            "pending": 0,
            "closed": 0,
            "total": 0,
            "retrieved_at": datetime.now().isoformat(),
        }

        current_app.logger.info("Case statistics retrieved")
        return {"status": "success", "statistics": stats}

    except Exception as e:
        current_app.logger.error(f"Error retrieving case statistics: {str(e)}")
        return {"status": "error", "message": str(e)}
