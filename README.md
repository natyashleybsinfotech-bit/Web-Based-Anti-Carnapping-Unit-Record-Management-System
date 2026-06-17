# Carnapping Records Starter Project

Starter project using:
- Front-End: HTML, CSS, JavaScript
- Back-End: Python (Flask)
- Database: MySQL
- Tools/Libraries: Chart.js, jsPDF, Print.js

Included functional requirements:
1. Officers can record and submit reports filed by complainants.
2. System generates a printable reference paper with QR code.
3. System sends a digital copy to the complainant's Gmail.
4. All report details are stored in a centralized online MySQL database.
5. Officers and admins can generate weekly and monthly reports.
6. Round robin queue for pending cases, prioritizing unfinished ones on top.

Retained legacy pages:
- `legacy-sample.html`
- `legacy-sample2.html`

## Quick start
1. Create MySQL database named `carnapping_db`
2. Import `schema.sql`
3. Copy `.env.example` to `.env`
4. Install dependencies:
   `pip install -r requirements.txt`
5. Run:
   `python run.py`

Note: the SQL file includes demo users, but the included password hashes may not match the demo passwords exactly. You can update them after setup if needed.

## Documentation

### API
- [API Reference](docs/api/API_REFERENCE.md)

### Setup & Configuration
- [Quick Start Guide](docs/setup/QUICK_START.md)
- [Realtime Sync Setup](docs/setup/REALTIME_SYNC_SETUP.md)

### Planning
- [Action Plan](docs/planning/ACTION_PLAN.md)
- [Implementation Summary](docs/planning/IMPLEMENTATION_SUMMARY.md)

### Logs & Notes
- [Case Submission Analysis](docs/logs/CASE_SUBMISSION_ANALYSIS.md)
- [Cloudflare Removal Complete](docs/logs/CLOUDFLARE_REMOVAL_COMPLETE.md)
- [Cloud Sync Fix](docs/logs/CLOUD_SYNC_FIX.md)
- [Cloud Sync Verification](docs/logs/CLOUD_SYNC_VERIFICATION.md)
- [Dashboard Enhancement](docs/logs/DASHBOARD_ENHANCEMENT.md)
- [District Selector Update](docs/logs/DISTRICT_SELECTOR_UPDATE.md)
- [Implementation Complete](docs/logs/IMPLEMENTATION_COMPLETE.md)
- [Mandatory Password Change](docs/logs/MANDATORY_PASSWORD_CHANGE.md)
- [Password Change Quick Reference](docs/logs/PASSWORD_CHANGE_QUICK_REFERENCE.md)
- [Supabase Integration Examples](docs/logs/SUPABASE_INTEGRATION_EXAMPLES.md)
- [Supabase Quick Reference](docs/logs/SUPABASE_QUICK_REFERENCE.md)
- [Supabase Setup](docs/logs/SUPABASE_SETUP.md)
- [Sync Quick Start](docs/logs/SYNC_QUICK_START.md)
- [UI Enhancement Process Reports](docs/logs/UI_ENHANCEMENT_PROCESS_REPORTS.md)
- [Visual Summary](docs/logs/VISUAL_SUMMARY.md)
