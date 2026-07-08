from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
)
from app import mysql
from .utils.auth import login_required, role_required
from .utils.helpers import generate_reference, generate_qr
from .services.mailer import send_reference_email
from .services.pdf_service import generate_reference_pdf
from .services.firebase_sync import (
    sync_case,
    sync_user,
    sync_activity_log,
    sync_receipt,
    sync_complainant,
    is_ready as firebase_ready,
)
import MySQLdb
import bcrypt
import re
from datetime import datetime

bp = Blueprint("main", __name__)


# =========================
# Utility Functions
# =========================
def log_activity(user_id, action, description):
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO activity_logs (user_id, action, description) VALUES (%s, %s, %s)",
            (user_id, action, description),
        )
        log_id = cur.lastrowid

        cur.execute("SELECT created_at FROM activity_logs WHERE id=%s", (log_id,))
        created_at_row = cur.fetchone()

        mysql.connection.commit()
        cur.close()

        # Sync activity log to Firebase Firestore
        if firebase_ready():
            activity_data = {
                "id": log_id,
                "user_id": user_id,
                "action": action,
                "description": description,
                "created_at": (
                    created_at_row[0].isoformat()
                    if created_at_row and created_at_row[0]
                    else datetime.now().isoformat()
                ),
            }
            sync_activity_log(log_id, activity_data)
    except Exception as e:
        print("LOG ACTIVITY ERROR:", e)


def assign_round_robin():
    """
    Assign the next active officer using round-robin based on Unsolved case load.
    Officers with the fewest Unsolved cases get priority.
    Status values: Unsolved / Solved / Cleared
    """
    try:
        cur = mysql.connection.cursor()

        # Get all active officers ordered by Unsolved case count (lightest load first)
        cur.execute("""
            SELECT u.id
            FROM users u
            LEFT JOIN cases c
                ON c.assigned_officer_id = u.id AND c.status = 'Unsolved'
            WHERE u.role = 'officer' AND u.is_active = 1
            GROUP BY u.id
            ORDER BY COUNT(c.id) ASC, u.id ASC
        """)
        officers = [row[0] for row in cur.fetchall()]
        cur.close()

        if not officers:
            return None

        return officers[0]

    except Exception as e:
        print("ROUND ROBIN ERROR:", e)
        return None


# =========================
# Home / Auth Routes
# =========================
@bp.route("/")
def home():
    return redirect(url_for("main.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                SELECT id, full_name, username, password_hash, role, is_active, force_password_change
                FROM users
                WHERE username=%s
            """,
                (username,),
            )
            user = cur.fetchone()
            cur.close()

            if user:
                (
                    user_id,
                    full_name,
                    db_username,
                    db_password,
                    role,
                    is_active,
                    force_password_change,
                ) = user

                if not is_active:
                    flash("Your account is inactive.")
                    return render_template("login.html")

                # Check password - handle both hashed and plaintext (for backwards compatibility)
                password_valid = False
                try:
                    # Try to verify as bcrypt hash first
                    password_valid = bcrypt.checkpw(
                        password.encode("utf-8"), db_password.encode("utf-8")
                    )
                except:
                    # Fallback to plaintext for existing accounts
                    password_valid = password == db_password

                if password_valid:
                    session["user_id"] = user_id
                    session["full_name"] = full_name
                    session["username"] = db_username
                    session["role"] = role

                    log_activity(user_id, "Login", f"{db_username} logged in")

                    # Check if password change is mandatory
                    if force_password_change:
                        flash("You must change your password on first login.")
                        return redirect(url_for("main.change_password_required"))

                    if role == "admin":
                        return redirect(url_for("main.admin_dashboard"))
                    else:
                        return redirect(url_for("main.officer_dashboard"))

            flash("Invalid username or password.")

        except Exception as e:
            print("LOGIN ERROR:", e)
            flash(f"Login error: {e}")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    if session.get("user_id"):
        log_activity(
            session["user_id"], "Logout", f"{session.get('username')} logged out"
        )
    session.clear()
    return redirect(url_for("main.login"))


# =========================
# Password Management
# =========================
@bp.route("/change-password-required", methods=["GET", "POST"])
@login_required
def change_password_required():
    """Mandatory password change on first login"""
    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            flash("Password fields cannot be empty.")
            return render_template("change_password_required.html")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return render_template("change_password_required.html")

        # Validate password strength
        if len(new_password) < 8:
            flash("Password must be at least 8 characters long.")
            return render_template("change_password_required.html")

        if not re.search(r"[A-Z]", new_password):
            flash("Password must contain at least one uppercase letter.")
            return render_template("change_password_required.html")

        if not re.search(r"[a-z]", new_password):
            flash("Password must contain at least one lowercase letter.")
            return render_template("change_password_required.html")

        if not re.search(r"[0-9]", new_password):
            flash("Password must contain at least one digit.")
            return render_template("change_password_required.html")

        try:
            user_id = session.get("user_id")
            cur = mysql.connection.cursor()

            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            )
            password_hash_str = password_hash.decode("utf-8")

            # Update password and clear the flag
            cur.execute(
                """
                UPDATE users 
                SET password_hash=%s, force_password_change=0 
                WHERE id=%s
            """,
                (password_hash_str, user_id),
            )

            mysql.connection.commit()
            cur.close()

            log_activity(
                user_id, "Password Change", "User changed password on first login"
            )
            flash("Password changed successfully! You can now proceed.")

            # Redirect based on role
            role = session.get("role")
            if role == "admin":
                return redirect(url_for("main.admin_dashboard"))
            else:
                return redirect(url_for("main.officer_dashboard"))

        except Exception as e:
            print("PASSWORD CHANGE ERROR:", e)
            flash(f"Error changing password: {e}")

    return render_template("change_password_required.html")


# =========================
# User Management
# =========================
@bp.route("/users/create", methods=["POST"])
@login_required
@role_required("admin")
def create_user():
    """Admin creates new officer account with default hashed password"""
    try:
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "officer").strip()

        if not full_name or not username:
            flash("Full name and username are required.")
            return redirect(url_for("main.manage_users"))

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            flash(
                "Username must be 3-20 characters and contain only letters, numbers, and underscores."
            )
            return redirect(url_for("main.manage_users"))

        if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            flash("Invalid email address.")
            return redirect(url_for("main.manage_users"))

        # Default password - hash it with bcrypt
        default_password = "default123"
        password_hash = bcrypt.hashpw(
            default_password.encode("utf-8"), bcrypt.gensalt()
        )
        password_hash_str = password_hash.decode("utf-8")

        cur = mysql.connection.cursor()

        try:
            # Insert new user with force_password_change = 1
            cur.execute(
                """
                INSERT INTO users (full_name, username, password_hash, role, email, is_active, force_password_change)
                VALUES (%s, %s, %s, %s, %s, 1, 1)
            """,
                (full_name, username, password_hash_str, role, email),
            )

            mysql.connection.commit()

            # Get the inserted user ID
            user_id = cur.lastrowid

            # Sync new user to Supabase
            if supabase_sync and supabase_sync.is_ready():
                user_data = {
                    "id": user_id,
                    "full_name": full_name,
                    "username": username,
                    "password_hash": password_hash_str,
                    "role": role,
                    "email": email,
                    "is_active": True,
                    "force_password_change": True,
                    "created_at": datetime.now().isoformat(),
                }
                supabase_sync.sync_record_to_supabase("users", user_data, "insert")

            log_activity(
                session.get("user_id"),
                "User Created",
                f"Created new {role}: {username}",
            )
            flash(
                f"User '{username}' created successfully with default password 'default123'. They must change it on first login."
            )

        except MySQLdb.IntegrityError:
            flash(f"Username '{username}' already exists.")

        cur.close()

    except Exception as e:
        print("CREATE USER ERROR:", e)
        flash(f"Error creating user: {e}")

    return redirect(url_for("main.manage_users"))


# =========================
# Dashboard Routes
# =========================
@bp.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    stats = {
        "total_cases": 0,
        "pending_cases": 0,
        "ongoing_cases": 0,
        "closed_cases": 0,
        "total_officers": 0,
        "active_officers": 0,
        "cases_today": 0,
        "resolution_rate": "0%",
        "top_barangay": "N/A",
        "top_barangay_count": 0,
        "officer_workload": [],
        "case_status_data": [],
        "recent_cases": [],
    }

    try:
        cur = mysql.connection.cursor()

        # Total counts
        cur.execute("SELECT COUNT(*) FROM cases")
        stats["total_cases"] = cur.fetchone()[0]

        # Support both legacy and current status values by counting equivalent statuses
        cur.execute("SELECT COUNT(*) FROM cases WHERE status IN ('Pending','Unsolved')")
        stats["pending_cases"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM cases WHERE status IN ('Ongoing','Solved')")
        stats["ongoing_cases"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM cases WHERE status IN ('Closed','Cleared')")
        stats["closed_cases"] = cur.fetchone()[0]

        # Officer statistics
        cur.execute("SELECT COUNT(*) FROM users WHERE role='officer'")
        stats["total_officers"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users WHERE role='officer' AND is_active=1")
        stats["active_officers"] = cur.fetchone()[0]

        # Cases created today
        cur.execute("SELECT COUNT(*) FROM cases WHERE DATE(created_at) = CURDATE()")
        stats["cases_today"] = cur.fetchone()[0]

        # Resolution rate
        if stats["total_cases"] > 0:
            resolution_pct = (stats["closed_cases"] / stats["total_cases"]) * 100
            stats["resolution_rate"] = f"{resolution_pct:.1f}%"

        # Top barangay
        cur.execute("""
            SELECT barangay_number, COUNT(*) as count
            FROM cases WHERE barangay_number IS NOT NULL
            GROUP BY barangay_number
            ORDER BY count DESC
            LIMIT 1
        """)
        top_barangay = cur.fetchone()
        if top_barangay:
            stats["top_barangay"] = f"Barangay {top_barangay[0]}"
            stats["top_barangay_count"] = top_barangay[1]

        # Officer workload
        cur.execute("""
            SELECT u.full_name, COUNT(c.id) as case_count
            FROM users u
            LEFT JOIN cases c ON u.id = c.assigned_officer_id
            WHERE u.role = 'officer' AND u.is_active = 1
            GROUP BY u.id, u.full_name
            ORDER BY case_count DESC
            LIMIT 5
        """)
        officer_workload = cur.fetchall()
        stats["officer_workload"] = [
            {"name": row[0], "cases": row[1]} for row in officer_workload
        ]

        # Case status breakdown for pie chart
        stats["case_status_data"] = [
            stats["pending_cases"],
            stats["ongoing_cases"],
            stats["closed_cases"],
        ]

        # Recent cases
        cur.execute("""
            SELECT reference_no, complainant_name, status, created_at
            FROM cases
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_cases = cur.fetchall()
        stats["recent_cases"] = [
            {
                "reference_no": row[0],
                "complainant_name": row[1],
                "status": row[2],
                "created_at": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "N/A",
            }
            for row in recent_cases
        ]

        cur.close()

    except Exception as e:
        print("ADMIN DASHBOARD ERROR:", e)

    return render_template("admin_dashboard.html", **stats)


@bp.route("/officer/dashboard")
@login_required
@role_required("officer")
def officer_dashboard():
    stats = {
        "my_cases": 0,
        "my_pending": 0,
        "my_ongoing": 0,
        "my_closed": 0,
        "completion_rate": "0%",
        "avg_resolution_time": "N/A",
        "my_recent_cases": [],
        "case_status_data": [],
        "total_officers": 0,
    }

    try:
        cur = mysql.connection.cursor()

        user_id = session["user_id"]

        # My case counts
        cur.execute(
            "SELECT COUNT(*) FROM cases WHERE assigned_officer_id=%s", (user_id,)
        )
        stats["my_cases"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM cases WHERE assigned_officer_id=%s AND status='Unsolved'",
            (user_id,),
        )
        stats["my_pending"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM cases WHERE assigned_officer_id=%s AND status='Solved'",
            (user_id,),
        )
        stats["my_ongoing"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM cases WHERE assigned_officer_id=%s AND status='Cleared'",
            (user_id,),
        )
        stats["my_closed"] = cur.fetchone()[0]

        # Completion rate
        if stats["my_cases"] > 0:
            completion_pct = (stats["my_closed"] / stats["my_cases"]) * 100
            stats["completion_rate"] = f"{completion_pct:.1f}%"

        # Case status data for chart
        stats["case_status_data"] = [
            stats["my_pending"],
            stats["my_ongoing"],
            stats["my_closed"],
        ]

        # Recent cases
        cur.execute(
            """
            SELECT reference_no, complainant_name, status, created_at, incident_date
            FROM cases
            WHERE assigned_officer_id=%s
            ORDER BY created_at DESC
            LIMIT 5
        """,
            (user_id,),
        )
        recent_cases = cur.fetchall()
        stats["my_recent_cases"] = [
            {
                "reference_no": row[0],
                "complainant_name": row[1],
                "status": row[2],
                "created_at": row[3].strftime("%Y-%m-%d") if row[3] else "N/A",
                "incident_date": row[4].strftime("%Y-%m-%d") if row[4] else "N/A",
            }
            for row in recent_cases
        ]

        # Total officers for comparison
        cur.execute("SELECT COUNT(*) FROM users WHERE role='officer' AND is_active=1")
        stats["total_officers"] = cur.fetchone()[0]

        cur.close()

    except Exception as e:
        print("OFFICER DASHBOARD ERROR:", e)

    return render_template("officer_dashboard.html", **stats)


# =========================
# Case Processing
# =========================
@bp.route("/cases/new", methods=["GET", "POST"])
@login_required
@role_required("admin", "officer")
def new_case():
    if request.method == "POST":
        # Build vehicle_details string from individual fields
        v_type = request.form.get("vehicle_type", "")
        v_make = request.form.get("vehicle_make", "")
        v_model = request.form.get("vehicle_model", "")
        v_color = request.form.get("vehicle_color", "")
        v_plate = request.form.get("plate_number", "").upper()
        v_year = request.form.get("vehicle_year", "")
        v_chassis = request.form.get("chassis_number", "").upper()
        v_engine = request.form.get("engine_number", "").upper()
        v_cc = request.form.get("engine_cc", "")
        vehicle_details = (
            f"{v_type} | {v_color} {v_year} {v_make} {v_model} | "
            f"Plate: {v_plate} | Chassis: {v_chassis} | Engine: {v_engine} {v_cc}cc"
        ).strip(" |")

        data = {
            "reference_no": generate_reference(),
            "complainant_name": request.form["complainant_name"],
            "complainant_email": request.form["complainant_email"],
            "complainant_contact": request.form.get("complainant_contact", ""),
            "complainant_address": request.form.get("complainant_address", ""),
            "incident_date": request.form["incident_date"],
            "incident_time": request.form.get("incident_time", None),
            "incident_location": request.form["incident_location"],
            "place_of_occurrence": request.form.get("place_of_occurrence", None),
            "barangay_number": request.form.get("barangay_number"),
            "station_concern": request.form.get("station_concern", ""),
            "blotter_entry_no": request.form.get("blotter_entry_no", ""),
            "vehicle_type": v_type or None,
            "vehicle_details": vehicle_details,
            "narrative": request.form["narrative"],
            "ioc": request.form.get("ioc", ""),
            "status": "Unsolved",
        }

        try:
            assigned_officer_id = assign_round_robin()

            cur = mysql.connection.cursor()

            # ── Step 1: Create complainant record ──
            full_name = data["complainant_name"].strip()
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            complainant_address = data["complainant_address"]
            cur.execute(
                """
                INSERT INTO complainants (first_name, last_name, contact_number, address)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    first_name,
                    last_name,
                    data["complainant_contact"],
                    complainant_address,
                ),
            )
            complainant_id = cur.lastrowid

            # ── Step 2: Insert case ──
            cur.execute(
                """
                INSERT INTO cases (
                    reference_no, complainant_name, complainant_email,
                    complainant_contact, complainant_address,
                    incident_date, incident_location,
                    place_of_occurrence, barangay_number,
                    station_concern, blotter_entry_no,
                    vehicle_type, vehicle_details,
                    narrative, status, ioc,
                    assigned_officer_id, created_by, complainant_id
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    data["reference_no"],
                    data["complainant_name"],
                    data["complainant_email"],
                    data["complainant_contact"],
                    data["complainant_address"],
                    data["incident_date"],
                    data["incident_location"],
                    data["place_of_occurrence"],
                    data["barangay_number"],
                    data["station_concern"],
                    data["blotter_entry_no"],
                    data["vehicle_type"],
                    data["vehicle_details"],
                    data["narrative"],
                    data["status"],
                    data["ioc"],
                    assigned_officer_id,
                    session["user_id"],
                    complainant_id,
                ),
            )
            case_id = cur.lastrowid

            # ── Step 2b: Insert suspects ──
            suspect_names = request.form.getlist("suspect_fullname[]")
            suspect_aliases = request.form.getlist("suspect_alias[]")
            suspect_gangs = request.form.getlist("suspect_gang[]")
            suspect_addrs = request.form.getlist("suspect_address[]")
            suspect_others = request.form.getlist("suspect_other[]")
            for i in range(len(suspect_names)):
                sname = suspect_names[i].strip()
                # Only save if at least a name or alias is provided
                salias = suspect_aliases[i].strip() if i < len(suspect_aliases) else ""
                if sname or salias:
                    cur.execute(
                        """
                        INSERT INTO suspects
                            (case_id, full_name, alias, address, gang_affiliation, other_details)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            case_id,
                            sname,
                            salias,
                            suspect_addrs[i].strip() if i < len(suspect_addrs) else "",
                            suspect_gangs[i].strip() if i < len(suspect_gangs) else "",
                            (
                                suspect_others[i].strip()
                                if i < len(suspect_others)
                                else ""
                            ),
                        ),
                    )

            mysql.connection.commit()
            cur.close()

            qr_path, track_url = generate_qr(data["reference_no"])
            pdf_path = generate_reference_pdf(data, qr_path)

            # ── Step 3: Create receipt record (Receipts entity) ──
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO receipts (Receipt_Code, email_sent, Case_ID, pdf_path, qr_path)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    data["reference_no"],
                    data["complainant_email"],
                    case_id,
                    pdf_path,
                    qr_path,
                ),
            )
            receipt_id = cur.lastrowid
            mysql.connection.commit()
            cur.close()

            # Send HTML email receipt (FR3 / UC4)
            email_ok, email_msg = send_reference_email(
                recipient=data["complainant_email"],
                reference_no=data["reference_no"],
                track_url=track_url,
                complainant_name=data["complainant_name"],
                incident_date=str(data["incident_date"]),
                incident_location=data["incident_location"],
                vehicle_details=data.get("vehicle_details", "N/A"),
            )
            if not email_ok:
                flash(f"⚠ Email notice: {email_msg}")

            # Sync to Firebase Firestore (FR4 — cloud storage with complainant_email)
            now_iso = datetime.now().isoformat()
            if firebase_ready():
                # Sync complainant
                sync_complainant(
                    complainant_id,
                    {
                        "id": complainant_id,
                        "First_Name": first_name,
                        "Last_Name": last_name,
                        "Contact_Number": data["complainant_contact"],
                        "Address": complainant_address,
                    },
                )

                # Sync case (including complainant_email — FR4 requirement)
                sync_case(
                    case_id,
                    {
                        "id": case_id,
                        "reference_no": data["reference_no"],
                        "complainant_name": data["complainant_name"],
                        "complainant_email": data["complainant_email"],  # FR4
                        "complainant_contact": data["complainant_contact"],
                        "incident_date": str(data["incident_date"]),
                        "incident_location": data["incident_location"],
                        "barangay_number": data["barangay_number"],
                        "vehicle_details": data["vehicle_details"],
                        "narrative": data["narrative"],
                        "status": data["status"],
                        "place_of_occurrence": data.get("place_of_occurrence", ""),
                        "station_concern": data.get("station_concern", ""),
                        "blotter_entry_no": data.get("blotter_entry_no", ""),
                        "vehicle_type": data.get("vehicle_type", ""),
                        "ioc": data.get("ioc", ""),
                        "complainant_address": data.get("complainant_address", ""),
                        "assigned_officer_id": assigned_officer_id,
                        "created_by": session["user_id"],
                        "complainant_id": complainant_id,
                        "created_at": now_iso,
                    },
                )

                # Sync receipt
                sync_receipt(
                    receipt_id,
                    {
                        "id": receipt_id,
                        "receipt_code": data["reference_no"],
                        "email_sent": data["complainant_email"],
                        "case_id": case_id,
                        "pdf_path": pdf_path,
                        "qr_path": qr_path,
                        "date_issued": now_iso,
                    },
                )

            # Log activity
            log_activity(
                session["user_id"],
                "Create Case",
                f"Created case {data['reference_no']} assigned to officer ID {assigned_officer_id}",
            )

            flash(f"Case saved successfully. Reference No: {data['reference_no']}")
            return redirect(
                url_for("main.reference_slip", reference_no=data["reference_no"])
            )

        except Exception as e:
            print("CASE SAVE ERROR:", e)
            flash(f"Error saving case: {e}")
            return redirect(url_for("main.new_case"))

    # Get all districts with barangays for the form
    from .services.hotspot_service import MANILA_DISTRICTS

    districts_list = []
    for district_id in sorted(MANILA_DISTRICTS.keys()):
        district_data = MANILA_DISTRICTS[district_id]
        barangays = district_data["barangays"]
        districts_list.append(
            {"id": district_id, "name": district_data["name"], "barangays": barangays}
        )

    return render_template("process_case.html", districts=districts_list)


@bp.route("/cases/edit/<reference_no>", methods=["GET", "POST"])
@login_required
@role_required("admin", "officer")
def edit_case(reference_no):
    case_data = None
    officers = []

    try:
        cur = mysql.connection.cursor()

        # Officers for dropdown
        cur.execute("""
            SELECT id, full_name
            FROM users
            WHERE role='officer' AND is_active=1
            ORDER BY full_name ASC
        """)
        officers = cur.fetchall()

        # Case details — fetch all new fields
        cur.execute(
            """
            SELECT
                id, reference_no,
                complainant_name, complainant_email, complainant_contact,
                complainant_address,
                incident_date, incident_location,
                place_of_occurrence, barangay_number,
                station_concern, blotter_entry_no,
                vehicle_type, vehicle_details,
                narrative, status, assigned_officer_id,
                ioc, suspect_details
            FROM cases
            WHERE reference_no=%s
        """,
            (reference_no,),
        )
        row = cur.fetchone()
        cur.close()

        if row:
            incident_date_value = row[6]
            if incident_date_value:
                try:
                    incident_date_value = incident_date_value.strftime("%Y-%m-%d")
                except:
                    incident_date_value = str(incident_date_value)

            case_data = {
                "id": row[0],
                "reference_no": row[1],
                "complainant_name": row[2],
                "complainant_email": row[3],
                "complainant_contact": row[4],
                "complainant_address": row[5],
                "incident_date": incident_date_value,
                "incident_location": row[7],
                "place_of_occurrence": row[8],
                "barangay_number": row[9],
                "station_concern": row[10],
                "blotter_entry_no": row[11],
                "vehicle_type": row[12],
                "vehicle_details": row[13],
                "narrative": row[14],
                "status": row[15],
                "assigned_officer_id": row[16],
                "ioc": row[17],
                "suspect_details": row[18],
            }

    except Exception as e:
        print("EDIT CASE LOAD ERROR:", e)

    if not case_data:
        flash("Case not found.")
        return redirect(url_for("main.queue"))

    if request.method == "POST":
        try:
            new_status = request.form["status"]
            new_officer_id = request.form.get("assigned_officer_id") or None
            old_status = case_data["status"]

            cur = mysql.connection.cursor()
            cur.execute(
                """
                UPDATE cases SET
                    status=%s,
                    assigned_officer_id=%s
                WHERE reference_no=%s
            """,
                (new_status, new_officer_id, reference_no),
            )
            mysql.connection.commit()
            cur.close()

            # Sync updated case to Firebase Firestore
            if firebase_ready():
                updated_fb_data = case_data.copy()
                # Ensure all dates are strings for JSON serialization
                if updated_fb_data.get("incident_date"):
                    updated_fb_data["incident_date"] = str(
                        updated_fb_data["incident_date"]
                    )
                updated_fb_data["status"] = new_status
                updated_fb_data["assigned_officer_id"] = new_officer_id
                sync_case(case_data["id"], updated_fb_data, operation="update")

            if new_status != old_status:
                from app.services.mailer import send_status_update_email

                track_url = f"{current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')}/track/{reference_no}"
                send_status_update_email(
                    recipient=case_data["complainant_email"],
                    reference_no=reference_no,
                    track_url=track_url,
                    complainant_name=case_data["complainant_name"],
                    new_status=new_status,
                )

            log_activity(
                session["user_id"],
                "Update Case Status",
                f"Updated case {reference_no} — status changed to: {new_status}",
            )

            flash(f"Case {reference_no} status updated to {new_status}.")
            return redirect(url_for("main.queue"))

        except Exception as e:
            print("EDIT CASE SAVE ERROR:", e)
            flash(f"Error updating case: {e}")

    return render_template("edit_case.html", case=case_data, officers=officers)


# =========================
# Reference / Tracking
# =========================
@bp.route("/reference/<reference_no>")
@login_required
@role_required("admin", "officer")
def reference_slip(reference_no):
    case_data = None

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT reference_no, complainant_name, complainant_email, incident_location, status
            FROM cases
            WHERE reference_no=%s
        """,
            (reference_no,),
        )
        row = cur.fetchone()
        cur.close()

        if row:
            case_data = {
                "reference_no": row[0],
                "complainant_name": row[1],
                "complainant_email": row[2],
                "incident_location": row[3],
                "status": row[4],
            }

    except Exception as e:
        print("REFERENCE SLIP ERROR:", e)

    if not case_data:
        flash("Reference not found.")
        return redirect(url_for("main.new_case"))

    return render_template("reference_slip.html", case=case_data)


@bp.route("/track/<reference_no>")
def track_case(reference_no):
    case = None

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT reference_no, complainant_name, incident_location, status, created_at
            FROM cases
            WHERE reference_no=%s
        """,
            (reference_no,),
        )
        case = cur.fetchone()
        cur.close()

    except Exception as e:
        print("TRACK CASE ERROR:", e)

    return render_template("track_case.html", case=case)


# =========================
# Manage Users
# =========================
@bp.route("/manage-users")
@login_required
@role_required("admin")
def manage_users():
    users = []

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, full_name, username, role, email, is_active
            FROM users
            ORDER BY id ASC
        """)
        users = cur.fetchall()
        cur.close()

    except Exception as e:
        print("MANAGE USERS ERROR:", e)

    return render_template("manage_users.html", users=users)


@bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(user_id):
    """Admin edits user details"""
    try:
        cur = mysql.connection.cursor()

        if request.method == "POST":
            # Update user details
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            role = request.form.get("role", "officer").strip()
            is_active = int(request.form.get("is_active", 1))

            if not full_name:
                flash("Full name is required.")
                return redirect(url_for("main.manage_users"))

            # Validate email if provided
            if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                flash("Invalid email address.")
                return redirect(url_for("main.manage_users"))

            try:
                cur.execute(
                    """
                    UPDATE users
                    SET full_name=%s, email=%s, role=%s, is_active=%s
                    WHERE id=%s
                """,
                    (full_name, email, role, is_active, user_id),
                )

                mysql.connection.commit()
                log_activity(
                    session.get("user_id"), "User Updated", f"Updated user {user_id}"
                )
                flash("User updated successfully.")
                return redirect(url_for("main.manage_users"))
            except MySQLdb.IntegrityError as e:
                flash(f"Error updating user: {e}")

        # GET request - display edit form
        cur.execute(
            """
            SELECT id, full_name, username, role, email, is_active
            FROM users
            WHERE id=%s
        """,
            (user_id,),
        )
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("User not found.")
            return redirect(url_for("main.manage_users"))

        return render_template("edit_user.html", user=user)

    except Exception as e:
        print("EDIT USER ERROR:", e)
        flash(f"Error editing user: {e}")
        return redirect(url_for("main.manage_users"))


@bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    """Admin deletes a user account"""
    try:
        # Prevent deleting your own account
        if user_id == session.get("user_id"):
            flash("You cannot delete your own account.")
            return redirect(url_for("main.manage_users"))

        cur = mysql.connection.cursor()

        # Get username for logging
        cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()

        if not user:
            flash("User not found.")
            return redirect(url_for("main.manage_users"))

        username = user[0]

        # Delete user
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        mysql.connection.commit()
        cur.close()

        log_activity(
            session.get("user_id"), "User Deleted", f"Deleted user: {username}"
        )
        flash(f"User '{username}' deleted successfully.")
        return redirect(url_for("main.manage_users"))

    except Exception as e:
        print("DELETE USER ERROR:", e)
        flash(f"Error deleting user: {e}")
        return redirect(url_for("main.manage_users"))


@bp.route("/users/toggle-status/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user_status(user_id):
    """Admin toggles user active/inactive status"""
    try:
        # Prevent disabling your own account
        if user_id == session.get("user_id"):
            flash("You cannot disable your own account.")
            return redirect(url_for("main.manage_users"))

        cur = mysql.connection.cursor()

        # Get current status
        cur.execute("SELECT is_active, username FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()

        if not user:
            flash("User not found.")
            return redirect(url_for("main.manage_users"))

        is_active, username = user
        new_status = 1 - is_active  # Toggle

        # Update status
        cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (new_status, user_id))
        mysql.connection.commit()
        cur.close()

        status_text = "activated" if new_status else "deactivated"
        log_activity(
            session.get("user_id"),
            "User Status Changed",
            f"{status_text} user: {username}",
        )
        flash(f"User '{username}' has been {status_text}.")
        return redirect(url_for("main.manage_users"))

    except Exception as e:
        print("TOGGLE USER STATUS ERROR:", e)
        flash(f"Error updating user status: {e}")
        return redirect(url_for("main.manage_users"))


# =========================
# UC13 — Case Records (Admin)
# =========================
@bp.route("/admin/cases")
@login_required
@role_required("admin")
def case_records():
    """Admin: searchable, filterable, paginated view of ALL cases (UC13)."""
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    barangay_filter = request.args.get("barangay", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = 20

    cases = []
    total = 0

    try:
        cur = mysql.connection.cursor()

        conditions = []
        params = []

        if search:
            conditions.append(
                "(reference_no LIKE %s OR complainant_name LIKE %s "
                "OR vehicle_details LIKE %s OR incident_location LIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like])

        if status_filter:
            conditions.append("status = %s")
            params.append(status_filter)

        if barangay_filter:
            conditions.append("barangay_number = %s")
            params.append(barangay_filter)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        # Total count
        cur.execute(f"SELECT COUNT(*) FROM cases {where_clause}", params)
        total = cur.fetchone()[0]

        # Paginated data
        offset = (page - 1) * per_page
        cur.execute(
            f"""
            SELECT
                c.id, c.reference_no, c.complainant_name, c.complainant_email,
                c.vehicle_details, c.status, c.barangay_number,
                c.incident_date, c.created_at,
                u.full_name AS officer_name
            FROM cases c
            LEFT JOIN users u ON c.assigned_officer_id = u.id
            {where_clause}
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """,
            params + [per_page, offset],
        )
        cases = cur.fetchall()
        cur.close()

    except Exception as e:
        print("CASE RECORDS ERROR:", e)
        flash(f"Error loading case records: {e}")

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "case_records.html",
        cases=cases,
        total=total,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        search=search,
        status_filter=status_filter,
        barangay_filter=barangay_filter,
    )


# ========================="
# Reports
# ========================="


# =========================
# Database Backup & Recovery (FR8)
# =========================
@bp.route("/database/backup", methods=["POST"])
@login_required
@role_required("admin")
def backup_database():
    """Create database backup using pure Python (no mysqldump required)"""
    try:
        from pathlib import Path
        from datetime import datetime

        # Create backup directory
        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sql"
        backup_path = backup_dir / backup_filename

        cur = mysql.connection.cursor()
        lines = []
        lines.append(f"-- PNP Case System Database Backup")
        lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(
            f"-- Database: {current_app.config.get('MYSQL_DB', 'carnapping_db')}"
        )
        lines.append("")
        lines.append("SET FOREIGN_KEY_CHECKS=0;")
        lines.append("")

        # Get all tables
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            # Get CREATE TABLE statement
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            create_row = cur.fetchone()
            lines.append(f"-- Table: {table}")
            lines.append(f"DROP TABLE IF EXISTS `{table}`;")
            lines.append(create_row[1] + ";")
            lines.append("")

            # Get all rows
            cur.execute(f"SELECT * FROM `{table}`")
            rows = cur.fetchall()
            if rows:
                # Get column names
                col_names = ", ".join([f"`{desc[0]}`" for desc in cur.description])
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            escaped = (
                                str(val)
                                .replace("\\", "\\\\")
                                .replace("'", "\\'")
                                .replace("\n", "\\n")
                                .replace("\r", "\\r")
                            )
                            values.append(f"'{escaped}'")
                    values_str = ", ".join(values)
                    lines.append(
                        f"INSERT INTO `{table}` ({col_names}) VALUES ({values_str});"
                    )
            lines.append("")

        lines.append("SET FOREIGN_KEY_CHECKS=1;")
        cur.close()

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        log_activity(
            session.get("user_id"),
            "Database Backup",
            f"Created backup: {backup_filename}",
        )
        flash(f"Database backup created successfully: {backup_filename}")
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
                backups.append(
                    {
                        "name": backup_file.name,
                        "size_mb": f"{file_size:.2f}",
                        "created_at": file_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "timestamp": file_time.timestamp(),
                    }
                )

    except Exception as e:
        print("MANAGE BACKUPS ERROR:", e)
        flash(f"Error loading backups: {e}")

    return render_template("manage_backups.html", backups=backups)


@bp.route("/database/restore/<backup_name>", methods=["POST"])
@login_required
@role_required("admin")
def restore_database(backup_name):
    """Restore database from backup using pure Python (no mysql CLI required)"""
    try:
        from pathlib import Path

        # Validate backup name (prevent directory traversal)
        if ".." in backup_name or "/" in backup_name or "\\" in backup_name:
            flash("Invalid backup file.")
            return redirect(url_for("main.manage_backups"))

        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_path = backup_dir / backup_name

        if not backup_path.exists():
            flash("Backup file not found.")
            return redirect(url_for("main.manage_backups"))

        with open(backup_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split into individual statements, skipping comments and blank lines
        statements = []
        current = []
        for line in sql_content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            current.append(line)
            if stripped.endswith(";"):
                statements.append(" ".join(current))
                current = []

        cur = mysql.connection.cursor()
        executed = 0
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
                executed += 1
        mysql.connection.commit()
        cur.close()

        log_activity(
            session.get("user_id"),
            "Database Restore",
            f"Restored from: {backup_name} ({executed} statements)",
        )
        flash(
            f"Database restored successfully from {backup_name} ({executed} statements executed)."
        )
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

        log_activity(
            session.get("user_id"), "Backup Deleted", f"Deleted backup: {backup_name}"
        )
        flash(f"Backup '{backup_name}' deleted successfully.")
        return redirect(url_for("main.manage_backups"))

    except Exception as e:
        print("DELETE BACKUP ERROR:", e)
        flash(f"Error deleting backup: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/download-backup/<backup_name>", methods=["GET"])
@login_required
@role_required("admin")
def download_backup(backup_name):
    """Download a backup file"""
    try:
        from pathlib import Path
        from flask import send_file

        # Validate backup name (prevent directory traversal)
        if ".." in backup_name or "/" in backup_name or "\\" in backup_name:
            flash("Invalid backup file.")
            return redirect(url_for("main.manage_backups"))

        backup_dir = Path(current_app.root_path) / "static" / "backups"
        backup_path = backup_dir / backup_name

        if not backup_path.exists():
            flash("Backup file not found.")
            return redirect(url_for("main.manage_backups"))

        log_activity(
            session.get("user_id"),
            "Backup Downloaded",
            f"Downloaded backup: {backup_name}",
        )
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=backup_name,
            mimetype="text/plain",
        )

    except Exception as e:
        print("DOWNLOAD BACKUP ERROR:", e)
        flash(f"Error downloading backup: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/export-sql")
@login_required
@role_required("admin")
def download_database_sql():
    """Generate and directly download the database as a .sql file (no disk save)"""
    try:
        from io import BytesIO
        from datetime import datetime
        from flask import send_file

        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]

        lines = []
        lines.append("-- PNP Case System Database Export")
        lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(
            f"-- Database: {current_app.config.get('MYSQL_DB', 'carnapping_db')}"
        )
        lines.append("")
        lines.append("SET FOREIGN_KEY_CHECKS=0;")
        lines.append("")

        for table in tables:
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            create_row = cur.fetchone()
            lines.append(f"-- Table: {table}")
            lines.append(f"DROP TABLE IF EXISTS `{table}`;")
            lines.append(create_row[1] + ";")
            lines.append("")
            cur.execute(f"SELECT * FROM `{table}`")
            rows = cur.fetchall()
            if rows:
                col_names = ", ".join([f"`{desc[0]}`" for desc in cur.description])
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            escaped = (
                                str(val)
                                .replace("\\", "\\\\")
                                .replace("'", "\\'")
                                .replace("\n", "\\n")
                                .replace("\r", "\\r")
                            )
                            values.append(f"'{escaped}'")
                    lines.append(
                        f"INSERT INTO `{table}` ({col_names}) VALUES ({', '.join(values)});"
                    )
            lines.append("")

        lines.append("SET FOREIGN_KEY_CHECKS=1;")
        cur.close()

        content = "\n".join(lines).encode("utf-8")
        buffer = BytesIO(content)
        buffer.seek(0)

        filename = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        log_activity(
            session.get("user_id"),
            "Database SQL Export",
            f"Downloaded SQL export: {filename}",
        )
        return send_file(
            buffer, as_attachment=True, download_name=filename, mimetype="text/plain"
        )

    except Exception as e:
        print("SQL EXPORT ERROR:", e)
        flash(f"Error generating SQL export: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/export-pdf")
@login_required
@role_required("admin")
def download_database_pdf():
    """Export entire database as a formatted PDF with tables"""
    try:
        from io import BytesIO
        from datetime import datetime
        from flask import send_file
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
            PageBreak,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        cur = mysql.connection.cursor()

        # Get all tables
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#003d7a"),
        )
        subtitle_style = ParagraphStyle(
            "Sub",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
        )
        table_title_style = ParagraphStyle(
            "TableTitle",
            parent=styles["Heading2"],
            fontSize=13,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#003d7a"),
        )
        cell_style = ParagraphStyle(
            "Cell", parent=styles["Normal"], fontSize=7, leading=9
        )

        elements = []

        # Cover title
        elements.append(Paragraph("PNP Anti-Carnapping Unit — MPD", title_style))
        elements.append(Paragraph(f"Database Export Report", title_style))
        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')} (Manila Time)",
                subtitle_style,
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

        # Hidden sensitive columns
        HIDDEN_COLS = {"password_hash"}

        for table_name in tables:
            cur.execute(f"SELECT * FROM `{table_name}`")
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]

            # Filter hidden columns
            visible_indices = [
                i for i, c in enumerate(col_names) if c not in HIDDEN_COLS
            ]
            visible_cols = [col_names[i] for i in visible_indices]

            elements.append(
                Paragraph(f"Table: {table_name.upper()}", table_title_style)
            )
            elements.append(Paragraph(f"{len(rows)} record(s)", subtitle_style))

            # Build table data — header + rows
            header = [Paragraph(f"<b>{c}</b>", cell_style) for c in visible_cols]
            data = [header]

            for row in rows:
                data.append(
                    [
                        Paragraph(
                            str(row[i]) if row[i] is not None else "—", cell_style
                        )
                        for i in visible_indices
                    ]
                )

            if not rows:
                data.append(
                    [Paragraph("<i>No records</i>", cell_style)]
                    + [""] * (len(visible_cols) - 1)
                )

            # Auto-distribute column widths
            page_width = landscape(A4)[0] - 3 * cm
            col_width = page_width / len(visible_cols)
            col_widths = [col_width] * len(visible_cols)

            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(
                TableStyle(
                    [
                        # Header
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003d7a")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("TOPPADDING", (0, 0), (-1, 0), 6),
                        # Rows
                        ("FONTSIZE", (0, 1), (-1, -1), 7),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f4ff")],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 1), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ]
                )
            )

            elements.append(tbl)
            elements.append(Spacer(1, 0.4 * cm))

            if table_name != tables[-1]:
                elements.append(PageBreak())

        cur.close()
        doc.build(elements)
        buffer.seek(0)

        filename = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        log_activity(
            session.get("user_id"),
            "Database PDF Export",
            f"Exported database as PDF: {filename}",
        )
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf",
        )

    except Exception as e:
        print("PDF EXPORT ERROR:", e)
        flash(f"Error generating PDF: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/export-excel")
@login_required
@role_required("admin")
def download_database_excel():
    """Export entire database as a formatted Excel (.xlsx) file"""
    try:
        from io import BytesIO
        from datetime import datetime
        from flask import send_file
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]

        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default empty sheet

        HIDDEN_COLS = {"password_hash"}

        # Styles — use full 8-char ARGB colors
        header_font = Font(bold=True, color="FFFFFFFF", size=10)
        header_fill = PatternFill(fill_type="solid", fgColor="FF003D7A")
        alt_fill = PatternFill(fill_type="solid", fgColor="FFEEF2FF")
        no_fill = PatternFill(fill_type=None)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
        thin_side = Side(style="thin", color="FFCCCCCC")
        thin_border = Border(
            left=thin_side, right=thin_side, top=thin_side, bottom=thin_side
        )

        for table_name in tables:
            cur.execute(f"SELECT * FROM `{table_name}`")
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            visible = [(i, c) for i, c in enumerate(col_names) if c not in HIDDEN_COLS]

            ws = wb.create_sheet(title=table_name[:31])

            # Header row
            for col_pos, (_, col_name) in enumerate(visible, start=1):
                cell = ws.cell(row=1, column=col_pos, value=col_name.upper())
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = thin_border

            # Data rows
            for row_idx, data_row in enumerate(rows, start=2):
                use_alt = row_idx % 2 == 0
                for col_pos, (data_idx, _) in enumerate(visible, start=1):
                    val = data_row[data_idx]
                    cell = ws.cell(
                        row=row_idx,
                        column=col_pos,
                        value=str(val) if val is not None else "",
                    )
                    cell.alignment = left_align
                    cell.border = thin_border
                    cell.fill = alt_fill if use_alt else no_fill

            # Auto-fit column widths
            for col_pos, (data_idx, col_name) in enumerate(visible, start=1):
                max_len = len(col_name)
                for data_row in rows:
                    val = data_row[data_idx]
                    max_len = max(max_len, len(str(val)) if val is not None else 0)
                ws.column_dimensions[get_column_letter(col_pos)].width = min(
                    max_len + 4, 40
                )

            ws.freeze_panes = "A2"

        cur.close()

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        log_activity(
            session.get("user_id"),
            "Database Excel Export",
            f"Exported database as Excel: {filename}",
        )
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        print("EXCEL EXPORT ERROR:", e)
        flash(f"Error generating Excel file: {e}")
        return redirect(url_for("main.manage_backups"))


@bp.route("/database/export-csv")
@login_required
@role_required("admin")
def download_database_csv():
    """Export entire database as per-table CSV files inside a ZIP archive"""
    try:
        from io import BytesIO, StringIO
        from datetime import datetime
        from flask import send_file
        import zipfile
        import csv

        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]

        HIDDEN_COLS = {"password_hash"}

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for table_name in tables:
                cur.execute(f"SELECT * FROM `{table_name}`")
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]

                # Filter hidden columns
                visible_indices = [
                    i for i, c in enumerate(col_names) if c not in HIDDEN_COLS
                ]
                visible_cols = [col_names[i] for i in visible_indices]

                # Build CSV in memory
                csv_io = StringIO(newline="")
                writer = csv.writer(csv_io)
                writer.writerow(visible_cols)

                for row in rows:
                    writer.writerow(
                        [row[i] if row[i] is not None else "" for i in visible_indices]
                    )

                csv_bytes = csv_io.getvalue().encode("utf-8-sig")
                csv_io.close()

                # Add to zip with safe filename
                filename = f"{table_name}.csv"
                z.writestr(filename, csv_bytes)

        cur.close()
        zip_buffer.seek(0)

        filename = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}_csv.zip"
        log_activity(
            session.get("user_id"),
            "Database CSV Export",
            f"Exported database as CSV ZIP: {filename}",
        )
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip",
        )

    except Exception as e:
        print("CSV EXPORT ERROR:", e)
        flash(f"Error generating CSV export: {e}")
        return redirect(url_for("main.manage_backups"))


# =========================
# Reports
# =========================
@bp.route("/reports")
@login_required
@role_required("admin", "officer")
def reports():
    period = request.args.get("period", "monthly")
    report_data = []

    try:
        cur = mysql.connection.cursor()

        if period == "weekly":
            cur.execute("""
                SELECT YEARWEEK(created_at, 1) AS bucket, COUNT(*)
                FROM cases
                GROUP BY YEARWEEK(created_at, 1)
                ORDER BY bucket DESC
                LIMIT 8
            """)
        elif period == "annually":
            cur.execute("""
                SELECT YEAR(created_at) AS bucket, COUNT(*)
                FROM cases
                GROUP BY YEAR(created_at)
                ORDER BY bucket DESC
                LIMIT 5
            """)
        else:
            cur.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m') AS bucket, COUNT(*)
                FROM cases
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY bucket DESC
                LIMIT 12
            """)

        report_data = cur.fetchall()
        cur.close()

    except Exception as e:
        print("REPORTS ERROR:", e)

    return render_template("reports.html", report_data=report_data, period=period)


# =========================
# Cloud Synchronization (Supabase Real-Time)
# =========================
@bp.route("/cloud-sync/status")
@login_required
@role_required("admin")
def cloud_sync_status():
    """Display Supabase real-time sync status"""
    sync_status = {}

    try:
        # Get Supabase sync status
        if supabase_sync and supabase_sync.is_ready():
            sync_status = supabase_sync.get_sync_status()
            sync_status["configured"] = True
        else:
            sync_status = {
                "configured": False,
                "message": "Supabase not configured or unavailable",
            }

        # Get recent sync activity from activity logs
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.created_at, u.username, a.action, a.description
            FROM activity_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT 50
        """)
        sync_history = cur.fetchall()
        cur.close()

    except Exception as e:
        print("CLOUD SYNC STATUS ERROR:", e)
        flash(f"Error loading sync status: {e}")
        sync_status = {"configured": False, "error": str(e)}

    return render_template(
        "cloud_sync_status.html", sync_status=sync_status, sync_history=sync_history
    )


# =========================
# Activity Log
# =========================


@bp.route("/activity-log")
@login_required
@role_required("admin")
def activity_log():
    logs = []

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.created_at, u.username, a.action, a.description
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT 100
        """)
        logs = cur.fetchall()
        cur.close()

    except Exception as e:
        print("ACTIVITY LOG ERROR:", e)

    return render_template("activity_log.html", logs=logs)


# =========================
# Queue / Round Robin
# =========================
@bp.route("/queue")
@login_required
@role_required("admin", "officer")
def queue():
    queue_rows = []

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT
                c.id,
                c.reference_no,
                c.complainant_name,
                c.status,
                u.full_name,
                c.created_at
            FROM cases c
            LEFT JOIN users u ON c.assigned_officer_id = u.id
            ORDER BY
                CASE
                    WHEN c.status IN ('Pending', 'Ongoing', 'Unsolved', 'Solved') THEN 0
                    ELSE 1
                END,
                c.created_at ASC
        """)
        queue_rows = cur.fetchall()
        cur.close()

    except Exception as e:
        print("QUEUE ERROR:", e)

    return render_template("queue.html", queue_rows=queue_rows)


# =========================
# Legacy Pages
# =========================
@bp.route("/legacy-sample")
def legacy_sample():
    return render_template("legacy_sample.html")


@bp.route("/legacy-sample2")
def legacy_sample2():
    return render_template("legacy_sample2.html")


# =========================
# Hotspots Map
# =========================
@bp.route("/hotspots")
@login_required
@role_required("admin")
def hotspots_map():
    """Display carnapping hotspots on interactive map by barangay."""
    from .services.hotspot_service import (
        get_location_hotspots_by_barangay,
        get_barangay_statistics,
        get_all_districts,
        save_hotspots_to_db,
    )
    import json

    cases_list = []

    try:
        # Fetch all cases with barangay data
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, barangay_number, incident_date, incident_location, status
            FROM cases
            WHERE barangay_number IS NOT NULL
            ORDER BY incident_date DESC
        """)

        for row in cur.fetchall():
            cases_list.append(
                {
                    "id": row[0],
                    "barangay_number": row[1] if row[1] else 0,
                    "incident_date": str(row[2]),
                    "incident_location": row[3],
                    "status": row[4],
                }
            )
        cur.close()

    except Exception as e:
        # If barangay_number column doesn't exist, try without it
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT id, incident_date, incident_location, status
                FROM cases
                ORDER BY incident_date DESC
            """)
            # No cases with barangay data yet - this is okay, map will be empty
            cur.close()
        except Exception as inner_e:
            # Log the error but continue - map will still display
            current_app.logger.warning(f"Could not fetch cases: {str(inner_e)}")

    try:
        # Calculate hotspots by barangay
        hotspots = get_location_hotspots_by_barangay(cases_list, minimum_incidents=2)
        if not isinstance(hotspots, dict):
            hotspots = {"hotspots": [], "status": "success", "total_hotspots": 0}

        # Save to local database and sync to Supabase cloud
        if hotspots.get("hotspots"):
            save_hotspots_to_db(hotspots.get("hotspots"))

        # Get statistics
        statistics = get_barangay_statistics(cases_list)
        if not isinstance(statistics, dict):
            statistics = {"statistics": {}, "status": "success"}

        # Get all districts info
        districts = get_all_districts()
        if not isinstance(districts, dict):
            districts = {"districts": []}

        return render_template(
            "hotspots_map.html",
            hotspots=json.dumps(hotspots.get("hotspots", [])),
            statistics=json.dumps(statistics.get("statistics", {})),
            districts=districts.get("districts", []),
        )

    except Exception as e:
        # Even if there's an error, return the map template with empty data
        current_app.logger.error(f"Error loading hotspots: {str(e)}")
        return render_template(
            "hotspots_map.html",
            hotspots=json.dumps([]),
            statistics=json.dumps({}),
            districts=[],
        )


# =========================
# Real-Time Cloud Sync Management
# =========================
@bp.route("/api/sync/status", methods=["GET"])
@login_required
@role_required("admin")
def get_sync_status():
    """Get current synchronization status"""
    from .services.cloud_sync_service import get_sync_status
    import json

    return json.dumps(get_sync_status()), 200, {"Content-Type": "application/json"}


@bp.route("/api/sync/push-all", methods=["POST"])
@login_required
@role_required("admin")
def push_all_to_cloud():
    """Manually push all local data to Supabase"""
    from .services.cloud_sync_service import sync_all_tables_to_cloud
    import json

    try:
        result = sync_all_tables_to_cloud(operation="push")
        log_activity(
            session.get("user_id"),
            "CLOUD_SYNC",
            f"Manual push to cloud: {result.get('status')}",
        )
        return json.dumps(result), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return (
            json.dumps({"status": "error", "message": str(e)}),
            500,
            {"Content-Type": "application/json"},
        )


@bp.route("/api/sync/pull-all", methods=["POST"])
@login_required
@role_required("admin")
def pull_all_from_cloud():
    """Manually pull all data from Supabase to local"""
    from .services.cloud_sync_service import sync_all_tables_to_cloud
    import json

    try:
        result = sync_all_tables_to_cloud(operation="pull")
        log_activity(
            session.get("user_id"),
            "CLOUD_SYNC",
            f"Manual pull from cloud: {result.get('status')}",
        )
        return json.dumps(result), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return (
            json.dumps({"status": "error", "message": str(e)}),
            500,
            {"Content-Type": "application/json"},
        )


@bp.route("/api/sync/retry-failed", methods=["POST"])
@login_required
@role_required("admin")
def retry_failed_syncs():
    """Retry failed synchronization operations"""
    from .services.cloud_sync_service import retry_failed_syncs
    import json

    try:
        result = retry_failed_syncs()
        log_activity(
            session.get("user_id"),
            "CLOUD_SYNC",
            f"Retry failed syncs: {result.get('status')}",
        )
        return json.dumps(result), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return (
            json.dumps({"status": "error", "message": str(e)}),
            500,
            {"Content-Type": "application/json"},
        )
