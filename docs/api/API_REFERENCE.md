# API Reference - Barangay Hotspot System

## Core Functions

### Hotspot Service (`app/services/hotspot_service.py`)

#### 1. Get District from Barangay
```python
from app.services.hotspot_service import get_district_from_barangay

result = get_district_from_barangay(barangay_number)
# Returns:
# {
#   'district_id': 1,
#   'district_name': 'Tondo (West/Proper)',
#   'barangay_number': 100,
#   'status': 'success'
# }
```

#### 2. Record Incident Location
```python
from app.services.hotspot_service import record_incident_location

result = record_incident_location(
    case_id=123,
    barangay_number=45,
    narrative="Carnapping incident at street X"
)
# Returns: {'status': 'success', 'message': '...'}
```

#### 3. Get Hotspots by Barangay
```python
from app.services.hotspot_service import get_location_hotspots_by_barangay

cases_data = [
    {'id': 1, 'barangay_number': 10, 'incident_date': '2026-04-20', ...},
    {'id': 2, 'barangay_number': 25, 'incident_date': '2026-04-19', ...},
    ...
]

hotspots = get_location_hotspots_by_barangay(
    cases_data=cases_data,
    minimum_incidents=2  # Only barangays with 2+ incidents
)
# Returns:
# {
#   'status': 'success',
#   'hotspots': [
#     {
#       'barangay_number': 10,
#       'district_id': 1,
#       'district_name': 'Tondo (West/Proper)',
#       'incident_count': 15,
#       'status': 'high_risk',
#       'last_incident': '2026-04-20T...'
#     },
#     ...
#   ],
#   'total_hotspots': 3
# }
```

#### 4. Get Barangay Statistics
```python
from app.services.hotspot_service import get_barangay_statistics

stats = get_barangay_statistics(cases_data=cases_data)
# Returns:
# {
#   'status': 'success',
#   'total_incidents': 50,
#   'barangays_with_incidents': 12,
#   'high_risk_count': 3,
#   'medium_risk_count': 4,
#   'low_risk_count': 5,
#   'statistics': {...}
# }
```

#### 5. Get Incidents by Barangay
```python
from app.services.hotspot_service import get_incidents_by_barangay

incidents = get_incidents_by_barangay(
    barangay_number=42,
    cases_data=cases_data
)
# Returns: [case1, case2, ...] - filtered cases
```

#### 6. Get All Districts
```python
from app.services.hotspot_service import get_all_districts

result = get_all_districts()
# Returns:
# {
#   'status': 'success',
#   'districts': [
#     {
#       'district_id': 1,
#       'district_name': 'Tondo (West/Proper)',
#       'barangay_count': 146,
#       'barangay_range': '1 - 146'
#     },
#     ...
#   ]
# }
```

#### 7. Get District Info
```python
from app.services.hotspot_service import get_district_info

info = get_district_info(district_id=1)
# Returns: {'district_name': '...', 'barangays': [...]}
```

---

### Case Service (`app/services/case_service.py`)

#### 1. Create Case
```python
from app.services.case_service import create_case

case_data = {
    'complainant_name': 'John Doe',
    'complainant_email': 'john@example.com',
    'complainant_contact': '09123456789',
    'incident_date': '2026-04-20',
    'incident_location': 'Tondo West Proper',
    'barangay_number': 10,  # ← Key field!
    'vehicle_details': 'Silver Honda Civic, Plate: ABC123',
    'narrative': 'Vehicle stolen from parking lot'
}

result = create_case(case_data)
# Returns: {'status': 'success', 'case_id': 123, 'reference_no': 'REF001'}
```

#### 2. Update Case Status
```python
from app.services.case_service import update_case_status

result = update_case_status(
    case_id=123,
    new_status='Closed'  # 'Opening', 'Pending', 'Closed'
)
# Returns: {'status': 'success', 'message': '...'}
```

#### 3. Assign Case to Officer
```python
from app.services.case_service import assign_case_to_officer

result = assign_case_to_officer(
    case_id=123,
    officer_id=5
)
# Returns: {'status': 'success', 'message': '...'}
```

#### 4. Get Case Statistics
```python
from app.services.case_service import get_case_statistics

stats = get_case_statistics()
# Returns: {
#   'total_cases': 100,
#   'opening': 20,
#   'pending': 50,
#   'closed': 30
# }
```

---

### Activity Service (`app/services/activity_service.py`)

#### 1. Log General Activity
```python
from app.services.activity_service import log_activity

log_activity(
    user_id=1,
    action='case_created',
    description='Created carnapping case',
    case_id=123,
    metadata={'barangay': 10, 'vehicle': 'Honda Civic'}
)
```

#### 2. Log Case Activity
```python
from app.services.activity_service import log_case_activity

log_case_activity(
    user_id=1,
    case_id=123,
    action='status_changed',
    description='Changed case status to Pending'
)
```

#### 3. Log Login Activity
```python
from app.services.activity_service import log_login_activity

log_login_activity(
    user_id=1,
    username='officer_john',
    ip_address='192.168.1.100',
    success=True
)
```

#### 4. Get Activity Logs
```python
from app.services.activity_service import get_activity_logs

logs = get_activity_logs(
    user_id=1,          # Optional
    case_id=123,        # Optional
    action='case_created',  # Optional
    limit=50
)
# Returns: [log1, log2, ...]
```

#### 5. Generate Activity Report
```python
from app.services.activity_service import generate_activity_report

report = generate_activity_report(
    start_date='2026-04-01',
    end_date='2026-04-30',
    report_type='activity'  # 'activity', 'login', 'case'
)
# Returns: detailed report with counts and details
```

---

### PDF Service (`app/services/pdf_service.py`)

#### 1. Manage User (FR7)
```python
from app.services.pdf_service import manage_user

result = manage_user(
    user_id=None,  # None for create, ID for update/delete
    action='add',  # 'add', 'update', 'remove'
    user_data={
        'username': 'officer_new',
        'email': 'officer@police.gov',
        'role': 'officer',
        'name': 'Officer John Reyes'
    }
)
# Returns: {'status': 'success', 'message': '...'}
```

#### 2. Manage Database Backup (FR8)
```python
from app.services.pdf_service import manage_database_backup

# Create backup
result = manage_database_backup(
    action='backup',
    backup_path='./backups/db_20260420.db'
)

# Restore from backup
result = manage_database_backup(
    action='restore',
    backup_path='./backups/db_20260420.db'
)
# Returns: {'status': 'success', 'message': '...'}
```

#### 3. Sync with Cloud Database (FR9)
```python
from app.services.pdf_service import sync_with_cloud_database

# Push to cloud
result = sync_with_cloud_database(
    data=[{'id': 1, 'reference_no': 'REF001', ...}],
    operation='push'
)

# Pull from cloud
result = sync_with_cloud_database(
    data=[],  # Empty for pull
    operation='pull'
)
# Returns: {'status': 'success', 'records_synced': 10}
```

---

### Authentication (`app/utils/auth.py`)

#### 1. Log Login Attempt
```python
from app.utils.auth import log_login_attempt

log_login_attempt(
    username='officer_john',
    success=True,
    ip_address='192.168.1.100'
)
```

#### 2. Track Session
```python
from app.utils.auth import track_session

track_session(
    user_id=1,
    username='officer_john',
    role='officer'
)
```

---

### Helpers (`app/utils/helpers.py`)

#### 1. Create Case with Logging
```python
from app.utils.helpers import create_case_with_logging

result = create_case_with_logging(
    case_data={...},
    user_id=1
)
# Automatically logs activity
```

#### 2. Update Case with Logging
```python
from app.utils.helpers import update_case_with_logging

result = update_case_with_logging(
    case_id=123,
    new_status='Closed',
    user_id=1
)
# Automatically logs activity
```

#### 3. Validate Case Status
```python
from app.utils.helpers import validate_case_status

is_valid = validate_case_status('Pending')  # True
is_valid = validate_case_status('Invalid')  # False
```

---

## Routes

### Case Management
```
POST /cases/new
  Form Data:
    - complainant_name
    - complainant_email
    - complainant_contact
    - incident_date
    - incident_location
    - barangay_number ← SELECT from dropdown (1-905)
    - vehicle_details
    - narrative
  Returns: Reference PDF + email + case ID
```

### Hotspots Map
```
GET /hotspots
  Returns: Interactive map visualization
  Data Sources:
    - Queries MySQL: All cases with barangay_number
    - Calculates hotspots: High/Medium/Low risk
    - Renders: Leaflet.js with circle markers
```

### Admin Dashboard
```
GET /admin
  Returns: Case statistics
  - Total cases by status
  - Officers workload
  - Recent activity
```

---

## Geographic Data Structure

### MANILA_DISTRICTS (in hotspot_service.py)
```python
MANILA_DISTRICTS = {
    'district_1': {
        'name': 'Tondo (West/Proper)',
        'barangays': [1, 2, 3, ..., 146]
    },
    'district_2': {
        'name': 'Tondo (East/Gagalangin)',
        'barangays': [147, 148, ..., 267]
    },
    'district_3': {
        'name': 'Binondo, Quiapo, San Nicolas, Santa Cruz',
        'barangays': [268, 269, ..., 394]
    },
    'district_4': {
        'name': 'Sampaloc',
        'barangays': [395, 396, ..., 586]
    },
    'district_5': {
        'name': 'Ermita, Malate, Intramuros, Port Area',
        'barangays': [649, 650, ..., 828]
    },
    'district_6': {
        'name': 'North Paco, Pandacan, San Miguel, Santa Ana, Santa Mesa',
        'barangays': [587, 588, ..., 648, 829, 830, ..., 905]
    }
}
```

---

## Example Workflow

```python
# 1. Officer creates a case
from app.services.case_service import create_case

case = create_case({
    'complainant_name': 'Maria Santos',
    'incident_location': 'Tondo',
    'barangay_number': 42,  # ← From form dropdown
    'vehicle_details': 'Red Toyota Vios',
    'narrative': 'Stolen from residential area',
    'incident_date': '2026-04-20'
})
# case_id = 123

# 2. System logs the activity
from app.services.activity_service import log_case_activity
log_case_activity(user_id=1, case_id=123, action='created', description='...')

# 3. Admin checks hotspots
from app.services.hotspot_service import get_location_hotspots_by_barangay
# Backend queries cases with barangays → calculates hotspots → renders map

# 4. Map displays:
# - Barangay 42: 8 incidents (🟠 MEDIUM RISK)
# - Barangay 41: 12 incidents (🔴 HIGH RISK)
# - Barangay 50: 3 incidents (🔵 LOW RISK)
```

---

## Error Handling

All functions return response dictionaries:

```python
# Success
{'status': 'success', 'message': '...', 'data': {...}}

# Error
{'status': 'error', 'message': 'Description of error'}
```

Check the `status` field before using returned data!

---

**API Reference Last Updated**: April 20, 2026  
**System Status**: 🟢 Production Ready
