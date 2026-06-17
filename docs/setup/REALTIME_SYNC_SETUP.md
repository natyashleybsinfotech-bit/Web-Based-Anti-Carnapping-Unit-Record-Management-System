# Real-Time Database Sync Setup Guide

This guide explains how to set up and use the real-time synchronization between your local MySQL database and Supabase PostgreSQL.

## 📋 Prerequisites

✅ You already have:
- Supabase URL: `https://zgdivjdowrwdnausyawa.supabase.co`
- Supabase ANON KEY: Already in `.env`
- Python packages installed: `supabase`, `realtime`, `websockets`

## 🚀 Setup Steps

### Step 1: Create Tables in Supabase

Run the setup script to create tables in your Supabase database:

```bash
python setup_supabase_tables.py
```

**What this does:**
- Connects to your Supabase project
- Creates 4 tables: `users`, `cases`, `activity_logs`, `report_exports`
- Enables real-time updates for all tables
- Creates performance indexes

**If tables already exist:**
- The script will verify they're configured correctly
- If not, it will show you the SQL to run manually

### Step 2: Verify .env Configuration

Your `.env` file should have:

```env
# Supabase Configuration
SUPABASE_URL=https://zgdivjdowrwdnausyawa.supabase.co
SUPABASE_ANON_KEY=REDACTED_FOR_SECURITY
SUPABASE_SYNC_ENABLED=True
```

The `SUPABASE_SYNC_ENABLED` flag is already set to `True` by default.

### Step 3: Start Your Application

```bash
python run.py
```

**On startup, the app will:**
1. ✓ Initialize Supabase connection
2. ✓ Set up real-time listeners for all tables
3. ✓ Perform an initial sync (push all local data to Supabase)
4. ✓ Listen for changes on both sides

Check the console for messages like:
```
✓ Supabase real-time listeners initialized
✓ Initial sync to cloud completed: success
```

## 🔄 How Real-Time Sync Works

### Automatic (Real-Time)

When data is modified in either database:

1. **Local Change → Cloud (Automatic)**
   - When you create/update/delete a case, user, etc. in MySQL
   - The change is automatically sent to Supabase
   - Happens instantly via the sync decorator

2. **Cloud Change → Local (Real-Time Listener)**
   - When another client updates Supabase directly
   - Changes are received via WebSocket
   - Automatically applied to local MySQL
   - Enables true bi-directional sync

### Manual Sync (Available)

Use these API endpoints for manual control:

#### Get Current Sync Status
```bash
curl -X GET http://127.0.0.1:5000/api/sync/status \
  -H "Accept: application/json"
```

Response:
```json
{
  "is_ready": true,
  "active_subscriptions": 4,
  "pending_syncs": 0,
  "last_sync_times": {
    "users": "2024-04-25T12:30:45.123456",
    "cases": "2024-04-25T12:30:50.654321"
  },
  "timestamp": "2024-04-25T12:35:00.123456"
}
```

#### Push All Local Data to Supabase
```bash
curl -X POST http://127.0.0.1:5000/api/sync/push-all \
  -H "Content-Type: application/json" \
  -d '{"token": "your_session_token"}'
```

#### Pull All Data from Supabase to Local
```bash
curl -X POST http://127.0.0.1:5000/api/sync/pull-all \
  -H "Content-Type: application/json" \
  -d '{"token": "your_session_token"}'
```

#### Retry Failed Syncs
```bash
curl -X POST http://127.0.0.1:5000/api/sync/retry-failed \
  -H "Content-Type: application/json" \
  -d '{"token": "your_session_token"}'
```

## 📊 Synced Tables

All 4 tables are synced in real-time:

| Table | Fields | Sync Type |
|-------|--------|-----------|
| **users** | id, full_name, username, password_hash, role, email, is_active, force_password_change, created_at | Bi-directional |
| **cases** | id, reference_no, complainant_name, complainant_email, complainant_contact, incident_date, incident_location, barangay_number, vehicle_details, narrative, status, assigned_officer_id, created_by, created_at, updated_at | Bi-directional |
| **activity_logs** | id, user_id, action, description, created_at | Bi-directional |
| **report_exports** | id, case_id, pdf_path, qr_path, emailed_to, created_at | Bi-directional |

## ✨ Features

### ✓ Automatic Insert Sync
When you create a new case:
```python
# In local MySQL
INSERT INTO cases (...) VALUES (...)

# Automatically pushed to Supabase in real-time
# Available in Supabase within milliseconds
```

### ✓ Automatic Update Sync
When you update a case:
```python
# In local MySQL
UPDATE cases SET status='Closed' WHERE id=1

# Automatically updated in Supabase
# All fields stay in sync
```

### ✓ Automatic Delete Sync
When a record is deleted:
```python
# In local MySQL
DELETE FROM cases WHERE id=1

# Automatically deleted from Supabase
# Maintains data consistency
```

### ✓ Bi-Directional Real-Time
Changes from Supabase are pulled back to local:
```
Supabase (via Admin Panel/API) 
    ↓ (Real-time listener)
    ↓ (WebSocket)
Local MySQL
```

### ✓ Conflict Resolution
- **Local writes always win** in case of conflicts
- Failed syncs are queued for retry
- Automatic retry mechanism built-in

### ✓ Batch Operations
- Large data syncs use batch operations (1000 records at a time)
- More efficient than one-by-one
- Handles errors per batch

## 🐛 Troubleshooting

### Issue: "Supabase not configured"

**Solution:** Verify `.env` has both `SUPABASE_URL` and `SUPABASE_ANON_KEY`

```bash
# Check .env
cat .env | grep SUPABASE
```

### Issue: "Tables don't exist in Supabase"

**Solution:** Run the setup script

```bash
python setup_supabase_tables.py
```

Then follow the instructions to copy/paste SQL in Supabase SQL Editor.

### Issue: Syncs pending but not completing

**Causes:**
1. Network issue
2. Supabase tables not properly configured
3. Column type mismatch

**Solution:**
```bash
# Retry failed syncs
curl -X POST http://127.0.0.1:5000/api/sync/retry-failed

# Check logs for specific errors
# Look for messages like "Failed to sync: [table_name]"
```

### Issue: Real-time listener not working

**Causes:**
1. Real-time not enabled in Supabase for the table
2. Network connectivity issue

**Solution:**
1. Go to Supabase Dashboard
2. Go to Database → Publications
3. Make sure `supabase_realtime` includes all 4 tables
4. Enable with SQL if needed:

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE public.users;
ALTER PUBLICATION supabase_realtime ADD TABLE public.cases;
ALTER PUBLICATION supabase_realtime ADD TABLE public.activity_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.report_exports;
```

## 📈 Monitoring

### View Logs

Check application logs for sync activity:
```bash
# In terminal where app is running
# Look for messages like:
# ✓ Successfully synced insert to Supabase: cases
# ✓ Subscribed to real-time changes on users
```

### Database Check

Verify data in Supabase:
1. Go to Supabase Dashboard
2. Click on your project
3. Go to Table Editor
4. Select each table to verify data is there
5. Check timestamps to see when syncs happened

### Activity Monitoring

Check the activity logs endpoint:
```bash
curl http://127.0.0.1:5000/activity-log
```

Look for entries with action `CLOUD_SYNC` to see when syncs occurred.

## 🔒 Security Notes

### Current Setup
- Using public/anon key (OK for initial setup)
- RLS (Row Level Security) is disabled by default
- All data can be read by anyone with the anon key

### For Production
Enable Row Level Security:

```sql
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_exports ENABLE ROW LEVEL SECURITY;

-- Create policies as needed
-- Example: Users can only see their own data
```

## 📞 Support

If sync doesn't start:

1. Check logs for errors
2. Verify Supabase tables exist
3. Ensure `.env` has correct credentials
4. Try manual sync via API endpoints
5. Check Supabase dashboard for connectivity

## ✅ Verification Checklist

- [ ] `.env` has `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- [ ] Ran `setup_supabase_tables.py` successfully
- [ ] App starts without Supabase errors
- [ ] See "✓ Supabase real-time listeners initialized" in logs
- [ ] `/api/sync/status` endpoint returns data
- [ ] Create a test case and verify it appears in Supabase
- [ ] Create a case in Supabase and verify it syncs to MySQL

## 🎯 Next Steps

1. **Test the sync:**
   - Create a new case via web interface
   - Check Supabase dashboard to see it appeared
   - Edit the case and verify Supabase updates

2. **Monitor sync:**
   - Keep browser open to `/api/sync/status`
   - Watch logs for sync messages

3. **Enable in production:**
   - Implement Row Level Security
   - Use service keys for admin operations
   - Set up proper error monitoring

---

**Need help?** Check the logs and error messages for specific guidance.
