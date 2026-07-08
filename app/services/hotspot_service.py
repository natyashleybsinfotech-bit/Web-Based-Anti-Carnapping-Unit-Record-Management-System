"""
Hotspot Location Service (Barangay-Based)
Analyzes incident locations by barangay to identify crime hotspots and geographic patterns.
"""

from datetime import datetime
from flask import current_app
from collections import Counter

# Manila Barangay Districts Data
MANILA_DISTRICTS = {
    1: {"name": "Tondo (West/Proper)", "barangays": list(range(1, 147))},
    2: {"name": "Tondo (East/Gagalangin)", "barangays": list(range(147, 268))},
    3: {
        "name": "Binondo, Quiapo, San Nicolas, Santa Cruz",
        "barangays": list(range(268, 395)),
    },
    4: {"name": "Sampaloc", "barangays": list(range(395, 587))},
    5: {
        "name": "Ermita, Malate, Intramuros, Port Area, San Andres, South Paco",
        "barangays": list(range(649, 829)),
    },
    6: {
        "name": "North Paco, Pandacan, San Miguel, Santa Ana, Santa Mesa",
        "barangays": list(range(587, 649)) + list(range(829, 906)),
    },
}


def get_district_from_barangay(barangay_number):
    """Find which district a barangay belongs to."""
    for district_id, district_data in MANILA_DISTRICTS.items():
        if barangay_number in district_data["barangays"]:
            return {"district_id": district_id, "district_name": district_data["name"]}
    return None


def record_incident_location(case_id, barangay_number, narrative=None):
    """
    Record an incident location by barangay for hotspot analysis.

    Args:
        case_id: Case ID
        barangay_number: Barangay number (1-905)
        narrative: Additional location details

    Returns:
        Location record
    """
    try:
        district_info = get_district_from_barangay(barangay_number)

        if not district_info:
            return {
                "status": "error",
                "message": f"Invalid barangay number: {barangay_number}",
            }

        location_record = {
            "case_id": case_id,
            "barangay_number": barangay_number,
            "district_id": district_info["district_id"],
            "district_name": district_info["district_name"],
            "narrative": narrative,
            "recorded_at": datetime.now().isoformat(),
        }

        current_app.logger.info(
            f"Incident location recorded: Barangay {barangay_number} "
            f"({district_info['district_name']}) for case {case_id}"
        )
        return {"status": "success", "location": location_record}

    except Exception as e:
        current_app.logger.error(f"Error recording incident location: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_location_hotspots_by_barangay(cases_data=None, minimum_incidents=2):
    """
    Identify hotspot barangays with high incident frequency.

    Args:
        cases_data: List of case data with barangay_number
        minimum_incidents: Minimum incidents to qualify as hotspot

    Returns:
        List of hotspot barangays
    """
    try:
        if not cases_data or len(cases_data) == 0:
            return {
                "status": "success",
                "hotspots": [],
                "total_hotspots": 0,
                "message": "No incident data to analyze",
            }

        # Count incidents and closed cases by barangay
        barangay_counts = Counter()
        barangay_closed = Counter()
        for case in cases_data:
            if "barangay_number" in case:
                b_num = case["barangay_number"]
                barangay_counts[b_num] += 1
                if case.get("status") == "Closed":
                    barangay_closed[b_num] += 1

        # Filter by minimum incidents and sort
        hotspots = []
        for barangay_num, count in barangay_counts.most_common():
            if count >= minimum_incidents:
                district_info = get_district_from_barangay(barangay_num)

                # Determine risk level
                if count >= 10:
                    risk_level = "high_risk"
                elif count >= 5:
                    risk_level = "medium_risk"
                else:
                    risk_level = "low_risk"

                # Calculate resolution rate
                closed_count = barangay_closed.get(barangay_num, 0)
                res_rate_percent = round((closed_count / count) * 100, 1)
                resolution_rate = f"{closed_count}/{count} ({res_rate_percent}%)"

                hotspots.append(
                    {
                        "barangay_number": barangay_num,
                        "barangay_name": f"Barangay {barangay_num}",
                        "district_id": district_info["district_id"],
                        "district_name": district_info["district_name"],
                        "incident_count": count,
                        "status": risk_level,
                        "resolution_rate": resolution_rate,
                        "last_incident": datetime.now().isoformat(),
                    }
                )

        current_app.logger.info(f"Hotspots identified: {len(hotspots)} barangays")
        return {
            "status": "success",
            "hotspots": hotspots,
            "total_hotspots": len(hotspots),
        }

    except Exception as e:
        current_app.logger.error(f"Error getting hotspots: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_barangay_statistics(cases_data=None):
    """
    Get comprehensive barangay-based statistics.

    Returns:
        Statistics by barangay and district
    """
    try:
        if not cases_data or len(cases_data) == 0:
            return {
                "status": "success",
                "statistics": {
                    "total_locations": 0,
                    "hotspot_locations": 0,
                    "high_risk_areas": 0,
                    "medium_risk_areas": 0,
                    "total_incidents": 0,
                },
            }

        barangay_counts = Counter()
        for case in cases_data:
            if "barangay_number" in case:
                barangay_counts[case["barangay_number"]] += 1

        # Calculate statistics
        high_risk = sum(1 for count in barangay_counts.values() if count >= 10)
        medium_risk = sum(1 for count in barangay_counts.values() if 5 <= count < 10)

        stats = {
            "total_locations": len(barangay_counts),
            "hotspot_locations": sum(
                1 for count in barangay_counts.values() if count >= 2
            ),
            "high_risk_areas": high_risk,
            "medium_risk_areas": medium_risk,
            "total_incidents": sum(barangay_counts.values()),
            "generated_at": datetime.now().isoformat(),
        }

        current_app.logger.info("Barangay statistics generated")
        return {"status": "success", "statistics": stats}

    except Exception as e:
        current_app.logger.error(f"Error getting barangay statistics: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_incidents_by_barangay(barangay_number, cases_data=None):
    """
    Get all incidents for a specific barangay.

    Args:
        barangay_number: Barangay to query
        cases_data: List of case data

    Returns:
        List of incidents in that barangay
    """
    try:
        if not cases_data:
            cases_data = []

        incidents = [
            c for c in cases_data if c.get("barangay_number") == barangay_number
        ]

        district_info = get_district_from_barangay(barangay_number)

        result = {
            "barangay_number": barangay_number,
            "district_name": (
                district_info["district_name"] if district_info else "Unknown"
            ),
            "total_incidents": len(incidents),
            "incidents": incidents,
            "retrieved_at": datetime.now().isoformat(),
        }

        current_app.logger.info(
            f"Incidents retrieved for barangay {barangay_number}: {len(incidents)}"
        )
        return {"status": "success", "incidents": result}

    except Exception as e:
        current_app.logger.error(f"Error getting incidents for barangay: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_district_info(district_id):
    """Get information about a specific district."""
    try:
        if district_id not in MANILA_DISTRICTS:
            return {"status": "error", "message": "Invalid district ID"}

        district = MANILA_DISTRICTS[district_id]
        return {
            "status": "success",
            "district": {
                "district_id": district_id,
                "district_name": district["name"],
                "barangay_count": len(district["barangays"]),
                "barangay_range": f"{district['barangays'][0]} - {district['barangays'][-1]}",
            },
        }

    except Exception as e:
        current_app.logger.error(f"Error getting district info: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_all_districts():
    """Get all districts and their information."""
    try:
        districts = []
        for district_id, district_data in MANILA_DISTRICTS.items():
            districts.append(
                {
                    "district_id": district_id,
                    "district_name": district_data["name"],
                    "barangay_count": len(district_data["barangays"]),
                    "barangay_range": f"{district_data['barangays'][0]} - {district_data['barangays'][-1]}",
                }
            )

        return {
            "status": "success",
            "districts": sorted(districts, key=lambda x: x["district_id"]),
        }

    except Exception as e:
        current_app.logger.error(f"Error getting districts: {str(e)}")
        return {"status": "error", "message": str(e)}


def save_hotspots_to_db(hotspots_data):
    """Save generated hotspots to local database and sync to Supabase."""
    from app import mysql
    from app.services.supabase_realtime_sync import supabase_sync
    import json

    try:
        if not hotspots_data or not isinstance(hotspots_data, list):
            return {"status": "success", "message": "No hotspots to save"}

        cur = mysql.connection.cursor()

        # Clear existing hotspot snapshot data
        cur.execute("DELETE FROM hotspot")

        records_to_sync = []

        for hs in hotspots_data:
            barangay_name = hs.get("barangay_name")
            district_name = hs.get("district_name", "Unknown")
            total_cases = hs.get("incident_count")
            risk_level = hs.get("status")
            resolution_rate = hs.get("resolution_rate", "0%")

            cur.execute(
                """
                INSERT INTO hotspot (barangay_name, district_name, period_type, risk_level, total_cases, resolution_rate)
                VALUES (%s, %s, 'monthly', %s, %s, %s)
            """,
                (
                    barangay_name,
                    district_name,
                    risk_level,
                    total_cases,
                    resolution_rate,
                ),
            )

            # Fetch the generated ID
            new_id = cur.lastrowid

            records_to_sync.append(
                {
                    "Hotspot_ID": new_id,
                    "barangay_name": barangay_name,
                    "district_name": district_name,
                    "period_type": "monthly",
                    "risk_level": risk_level,
                    "total_cases": total_cases,
                    "resolution_rate": resolution_rate,
                }
            )

        mysql.connection.commit()
        cur.close()

        # Sync to Supabase cloud using batch upsert
        if supabase_sync and supabase_sync.is_ready():
            # First, clear the Supabase cloud table so we don't accumulate duplicates
            try:
                # Use a dummy condition that is always true to delete all rows
                supabase_sync.client.table("hotspot").delete().neq(
                    "Hotspot_ID", -1
                ).execute()
            except Exception as se:
                current_app.logger.warning(
                    f"Could not clear Supabase hotspot table: {se}"
                )

            if records_to_sync:
                supabase_sync.batch_sync_to_supabase(
                    "hotspot", records_to_sync, "insert"
                )

        return {
            "status": "success",
            "message": f"Saved {len(records_to_sync)} hotspots",
        }

    except Exception as e:
        current_app.logger.error(f"Error saving hotspots to DB: {str(e)}")
        return {"status": "error", "message": str(e)}
