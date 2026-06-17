# Case Submission Process Analysis

## Overview
The Flask app uses a **direct MySQL approach** for case submissions with placeholder cloud sync capabilities. Below is a complete analysis with code excerpts and line numbers.

---

## 1. CASE SUBMISSION ENDPOINT (routes.py)

### Location: [app/routes.py](app/routes.py#L230-L312)

**Endpoint**: `POST /cases/new`  
**Access Control**: Requires admin or officer role  
**Purpose**: Handle new case submission form and save to database

```python
# Lines 230-312
@bp.route("/cases/new", methods=["GET", "POST"])
@login_required
@role_required("admin", "officer")
def new_case():
    if request.method == "POST":
        data = {
            "reference_no": generate_reference(),
            "complainant_name": request.form["complainant_name"],
            "complainant_email": request.form["complainant_email"],
            "complainant_contact": request.form.get("complainant_contact", ""),
            "incident_date": request.form["incident_date"],
            "incident_location": request.form["incident_location"],
            "barangay_number": request.form.get("barangay_number"),
            "vehicle_details": request.form.get("vehicle_details", ""),
            "narrative": request.form["narrative"],
            "status": "Pending"
        }

        try:
            assigned_officer_id = assign_round_robin()

            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO cases
                (
                    reference_no,
                    complainant_name,
                    complainant_email,
                    complainant_contact,
                    incident_date,
                    incident_location,
                    barangay_number,
                    vehicle_details,
                    narrative,
                    status,
                    assigned_officer_id,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["reference_no"],
                    data["complainant_name"],
                    data["complainant_email"],
                    data["complainant_contact"],
                    data["incident_date"],
                    data["incident_location"],
                    data["barangay_number"],
                    data["vehicle_details"],
                    data["narrative"],
                    data["status"],
                    assigned_officer_id,
                    session["user_id"]
                )
            )

            case_id = cur.lastrowid
            mysql.connection.commit()
            cur.close()

            qr_path, track_url = generate_qr(data["reference_no"])
            pdf_path = generate_reference_pdf(data, qr_path)

            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO report_exports (case_id, pdf_path, qr_path, emailed_to)
                VALUES (%s, %s, %s, %s)
                """,
                (case_id, pdf_path, qr_path, data["complainant_email"])
            )
            mysql.connection.commit()
            cur.close()

            try:
                send_reference_email(
                    data["complainant_email"],
                    data["reference_no"],
                    track_url
                )
            except Exception as mail_error:
                print("EMAIL ERROR:", mail_error)

            log_activity(
                session["user_id"],
                "Create Case",
                f"Created case {data['reference_no']} assigned to officer ID {assigned_officer_id}"
            )

            flash(f"Case saved successfully. Reference No: {data['reference_no']}")
            return redirect(url_for("main.reference_slip", reference_no=data["reference_no"]))

        except Exception as e:
            print("CASE SAVE ERROR:", e)
            flash(f"Error saving case: {e}")
            return redirect(url_for("main.new_case"))

    # Get all districts with barangays for the form
    from .services.hotspot_service import MANILA_DISTRICTS
    
    districts_list = []
    for district_id in sorted(MANILA_DISTRICTS.keys()):
        district_data = MANILA_DISTRICTS[district_id]
        barangays = district_data['barangays']
        districts_list.append({
            'id': district_id,
            'name': district_data['name'],
            'barangays': barangays
        })
    
    return render_template("process_case.html", districts=districts_list)
```

### Key Steps in Case Submission:
1. **Lines 233-243**: Collect form data with generated reference number
2. **Lines 245-268**: Get round-robin assigned officer
3. **Lines 270-290**: Insert case into MySQL database
4. **Lines 292-298**: Generate QR code and PDF
5. **Lines 300-305**: Insert export record to database
6. **Lines 307-311**: Send reference email (wrapped in try-catch for resilience)
7. **Line 313-315**: Log activity audit trail
8. **Line 320**: Redirect to reference slip page

---

## 2. CASE SAVING IN DATABASE

### Direct MySQL Operations (NOT a separate service)

The actual case saving happens **directly in routes.py** using raw SQL:

**MySQL INSERT Operation** (lines 270-290):
```sql
INSERT INTO cases
(
    reference_no,
    complainant_name,
    complainant_email,
    complainant_contact,
    incident_date,
    incident_location,
    barangay_number,
    vehicle_details,
    narrative,
    status,
    assigned_officer_id,
    created_by
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
```

### case_service.py Analysis

**Location**: [app/services/case_service.py](app/services/case_service.py)

⚠️ **IMPORTANT**: The `case_service.py` file contains **placeholder/template functions that do NOT access the database**. These are:
- `create_case()` (lines 7-45)
- `update_case_status()` (lines 48-71)
- `get_case_details()` (lines 74-92)
- `assign_case_to_officer()` (lines 95-114)
- `get_case_statistics()` (lines 117-139)

These functions only log to Flask logger but don't execute actual SQL or database operations. **The actual case submission uses direct MySQL cursor operations in routes.py, not these service functions.**

---

## 3. DATABASES BEING USED

### Primary Database: MySQL (Local)

**Configuration** in [app/__init__.py](app/__init__.py#L1-L28):
```python
# Lines 7-18
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "carnapping_db")
```

**Package**: Flask-MySQLdb 2.0.0  
**Database**: carnapping_db  
**Connection**: Initialized via `mysql.init_app(app)` (line 22)

**Tables** in [schema.sql](schema.sql):
- `users` - Admin and officer accounts
- `cases` - Main case records
- `activity_logs` - Audit trail
- `report_exports` - PDF/QR exports

### Cloud Database: Supabase PostgreSQL (Real-Time Sync ACTIVE)

**Configuration** in `.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_SYNC_ENABLED=True
```

✅ **ACTIVE**: Automatic real-time sync to Supabase on case creation and updates!

**Sync Service**: [app/services/supabase_realtime_sync.py](app/services/supabase_realtime_sync.py)

---

## 4. ERROR HANDLING & LOGGING

### Error Handling in Case Submission

**Try-Catch Block** (lines 245-326):
```python
try:
    # Case submission logic
except Exception as e:
    print("CASE SAVE ERROR:", e)
    flash(f"Error saving case: {e}")
    return redirect(url_for("main.new_case"))
```

### Supabase Sync Error Handling

**Non-blocking sync**:
```python
# Sync case to Supabase
if supabase_sync and supabase_sync.is_ready():
    supabase_sync.sync_record_to_supabase('cases', case_data, 'insert')
    # Errors don't block case creation
```

### Error Handling Methods:
1. **Print statements** (line 322): `print("CASE SAVE ERROR:", e)`
2. **User feedback**: `flash()` messages displayed on page
3. **Fallback redirect**: Returns to form if error occurs
4. **Email resilience** (lines 310-311): Email errors don't block case creation
5. **Supabase resilience**: Cloud sync errors queued for retry

### Activity Logging

**Function** in [app/routes.py](app/routes.py#L14-L22):
```python
def log_activity(user_id, action, description):
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO activity_logs (user_id, action, description) VALUES (%s, %s, %s)",
            (user_id, action, description)
        )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("LOG ACTIVITY ERROR:", e)
```

**Activity Log Entry** (line 315):
```python
log_activity(
    session["user_id"],
    "Create Case",
    f"Created case {data['reference_no']} assigned to officer ID {assigned_officer_id}"
)
```

### Service-Level Logging

**In case_service.py** (uses Flask logger):
```python
current_app.logger.info(f"Case created: {case_data['reference_no']} with status {status}")
current_app.logger.error(f"Error creating case: {str(e)}")
```

---

## 5. CLOUD DATABASE CONNECTIONS

### Supabase Real-Time Sync Service

**Location**: [app/services/supabase_realtime_sync.py](app/services/supabase_realtime_sync.py)

**Features**:
- ✅ Real-time WebSocket synchronization
- ✅ Automatic bi-directional sync
- ✅ Conflict resolution (last-write-wins)
- ✅ Automatic retry queue for failed operations
- ✅ Batch operations support
- ✅ Non-blocking (doesn't interrupt case creation)

**Integration in routes.py**:
```python
# After case is saved to MySQL
if supabase_sync and supabase_sync.is_ready():
    case_data = {...}
    supabase_sync.sync_record_to_supabase('cases', case_data, 'insert')
```

**Configuration** (from `.env`):
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_KEY=your-key
SUPABASE_SYNC_ENABLED=True
```
        if not all([account_id, database_id, api_token]):
            return {"status": "error", "message": "Missing Cloudflare D1 configuration"}
        
        d1_api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        if operation == "push":
            # Push local data to D1 cloud
            if data is None or len(data) == 0:
                return {"status": "error", "message": "No data to sync"}
            
            try:
                # Prepare SQL INSERT statements for D1
                sql_statements = []
                
                if isinstance(data, list):
                    for record in data:
                        sql = f"""INSERT INTO cases (reference_no, complainant_name, complainant_email, 
                                  incident_location, status, created_at) 
                                  VALUES ('{record.get('reference_no')}', '{record.get('complainant_name')}', 
                                  '{record.get('complainant_email')}', '{record.get('incident_location')}', 
                                  '{record.get('status')}', '{datetime.now().isoformat()}')"""
                        sql_statements.append(sql)
                else:
                    sql = f"""INSERT INTO cases (reference_no, complainant_name, complainant_email, 
                              incident_location, status, created_at) 
                              VALUES ('{data.get('reference_no')}', '{data.get('complainant_name')}', 
                              '{data.get('complainant_email')}', '{data.get('incident_location')}', 
                              '{data.get('status')}', '{datetime.now().isoformat()}')"""
                    sql_statements = [sql]
                
                response = requests.post(
                    d1_api_url,
                    json={"sql": "; ".join(sql_statements)},
                    headers=headers,
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                current_app.logger.info(f"Data pushed to D1 successfully at {datetime.now()}")
                return {
                    "status": "success",
                    "message": "Data synced to cloud successfully",
                    "records_synced": len(data) if isinstance(data, list) else 1
                }
            
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Failed to push data to D1: {str(e)}")
                return {"status": "error", "message": f"Cloud sync failed: {str(e)}"}
        
        elif operation == "pull":
            # Pull latest data from D1 cloud
            try:
                sql = "SELECT * FROM cases ORDER BY created_at DESC LIMIT 100"
                
                response = requests.post(
                    d1_api_url,
                    json={"sql": sql},
                    headers=headers,
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                current_app.logger.info(f"Data pulled from D1 successfully at {datetime.now()}")
                return {
                    "status": "success",
                    "message": "Data synced from cloud successfully",
                    "cloud_data": result.get("result", [])
                }
            
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Failed to pull data from D1: {str(e)}")
                return {"status": "error", "message": f"Cloud sync failed: {str(e)}"}
        
        else:
            return {"status": "error", "message": "Invalid operation"}
    
    except Exception as e:
        current_app.logger.error(f"Cloud sync error: {str(e)}")
        return {"status": "error", "message": str(e)}
```

### Key Features:
- **Endpoint**: `https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query`
- **Authentication**: Bearer token in Authorization header
- **Operations**: 
  - `push`: Send local data to D1 cloud
  - `pull`: Retrieve data from D1 cloud
- **Error Handling**: 
  - Request timeout: 30 seconds
  - Detailed logging with Flask logger
  - Response validation with `raise_for_status()`

### ⚠️ Critical Issue: SQL Injection Vulnerability
The D1 sync function uses f-string string interpolation for SQL (not parameterized queries):
```python
sql = f"""INSERT INTO cases (reference_no, complainant_name, ...) 
          VALUES ('{record.get('reference_no')}', '{record.get('complainant_name')}', ...)"""
```
This is a **SQL injection vulnerability** and should use parameterized queries.

---

## 6. ROUND-ROBIN OFFICER ASSIGNMENT

**Function**: `assign_round_robin()` in [app/routes.py](app/routes.py#L25-L59)

```python
# Lines 25-59
def assign_round_robin():
    """
    Assign the next active officer in sequence.
    """
    try:
        cur = mysql.connection.cursor()

        # Get all active officers
        cur.execute("""
            SELECT id
            FROM users
            WHERE role='officer' AND is_active=1
            ORDER BY id ASC
        """)
        officers = [row[0] for row in cur.fetchall()]

        if not officers:
            cur.close()
            return None

        # Find last assigned officer
        cur.execute("""
            SELECT assigned_officer_id
            FROM cases
            WHERE assigned_officer_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
        """)
        last = cur.fetchone()
        cur.close()

        if not last or last[0] not in officers:
            return officers[0]

        idx = officers.index(last[0])
        return officers[(idx + 1) % len(officers)]

    except Exception as e:
        print("ROUND ROBIN ERROR:", e)
        return None
```

---

## 7. CASE EDIT/UPDATE ENDPOINT

**Location**: [app/routes.py](app/routes.py#L329-L417)  
**Endpoint**: `POST/GET /cases/edit/<reference_no>`

The update uses direct SQL with parameterized queries (better practice than the D1 sync):
```python
# Lines 387-405
cur.execute("""
    UPDATE cases
    SET
        complainant_name=%s,
        complainant_email=%s,
        complainant_contact=%s,
        incident_date=%s,
        incident_location=%s,
        vehicle_details=%s,
        narrative=%s,
        status=%s,
        assigned_officer_id=%s
    WHERE reference_no=%s
""", (
    complainant_name,
    complainant_email,
    complainant_contact,
    incident_date,
    incident_location,
    vehicle_details,
    narrative,
    status,
    assigned_officer_id,
    reference_no
))
```

---

## 8. REQUIREMENTS & DEPENDENCIES

**File**: [requirements.txt](requirements.txt)

```
Flask==3.1.0
Flask-MySQLdb==2.0.0
Flask-Mail==0.10.0
python-dotenv==1.0.1
qrcode==8.0
Pillow==11.1.0
reportlab==4.2.5
bcrypt==4.2.1
requests==2.31.0
```

**No Cloud SDKs installed** - Only `requests` library for HTTP calls to Cloudflare API

---

## 9. SUMMARY TABLE

| Component | Location | Type | Status |
|-----------|----------|------|--------|
| **Case Submission Endpoint** | routes.py L230-312 | POST /cases/new | ✅ Active |
| **Case Service** | case_service.py L7-139 | Placeholder Functions | ❌ Not Used |
| **MySQL Database** | __init__.py L7-18 | Local Database | ✅ Active |
| **Cloudflare D1** | __init__.py L19-21 | Cloud DB Config | ⚠️ Configured, Not Used |
| **D1 Sync Function** | pdf_service.py L110-249 | Cloud Sync | ⚠️ Exists, Never Called |
| **Error Handling** | routes.py L245-326 | Try-Catch | ✅ Basic |
| **Activity Logging** | routes.py L14-22 | Audit Trail | ✅ Active |
| **Officer Assignment** | routes.py L25-59 | Round-Robin | ✅ Active |

---

## 10. WORKFLOW DIAGRAM

```
User submits case form
         ↓
POST /cases/new endpoint (L230)
         ↓
Generate reference number (L233)
         ↓
Call assign_round_robin() (L245)
         ↓
INSERT into MySQL cases table (L270-290)
         ↓
Generate QR code & PDF (L292-298)
         ↓
INSERT into MySQL report_exports (L300-305)
         ↓
Try to send email (L307-311)
         ↓
Log activity (L313-315)
         ↓
Flash success message (L317)
         ↓
Redirect to reference slip (L318)
```

**Note**: Cloud sync (Cloudflare D1) is NOT part of this workflow.

---

## Recommendations

1. **Remove unused case_service.py functions** - They serve no purpose
2. **Integrate cloud sync** - Call `sync_with_cloud_database()` after case insertion if cloud backup is needed
3. **Fix SQL injection** - Use parameterized queries in D1 sync function
4. **Improve logging** - Replace `print()` statements with Flask logger
5. **Add case service layer** - Actually use the service functions for better separation of concerns
