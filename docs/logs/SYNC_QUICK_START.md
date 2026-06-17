# Real-Time Sync - Quick Start Guide

## ⚡ 3-Step Setup

### Step 1: Create Supabase Tables (2 minutes)
```bash
python setup_supabase_tables.py
```

**If you get an error saying tables don't exist:**
1. Go to: https://app.supabase.com/project/YOUR_PROJECT/sql
2. Click "New Query"
3. Copy the SQL from the script output
4. Paste it and click "Run"
5. Run the script again

### Step 2: Start the App
```bash
python run.py
```

**Check for these success messages:**
```
✓ Supabase real-time listeners initialized
✓ Initial sync to cloud completed: success
```

### Step 3: Test It Works
```bash
python test_realtime_sync.py
```

---

## ✅ What You Get

### ✓ Automatic Real-Time Sync
- Create a case in the web app → appears in Supabase instantly
- Update a case → changes sync to Supabase immediately  
- Delete a case → deleted from Supabase too

### ✓ Bi-Directional
- Changes in Supabase → pull back to local MySQL
- Local changes → push to Supabase
- Always in sync!

### ✓ All 4 Tables Synced
- users
- cases
- activity_logs
- report_exports

---

## 📊 Monitor Sync Status

### Via API (for developers)
```bash
curl http://127.0.0.1:5000/api/sync/status
```

### Via Supabase Dashboard
1. Go to Table Editor
2. Click each table to see records
3. Timestamps show when synced

---

## 🔧 Manual Controls (if needed)

### Push All Data to Cloud
```bash
curl -X POST http://127.0.0.1:5000/api/sync/push-all
```

### Pull All Data from Cloud
```bash
curl -X POST http://127.0.0.1:5000/api/sync/pull-all
```

### Retry Failed Syncs
```bash
curl -X POST http://127.0.0.1:5000/api/sync/retry-failed
```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Supabase not configured" | Check `.env` has SUPABASE_URL and SUPABASE_ANON_KEY |
| "Tables don't exist" | Run: `python setup_supabase_tables.py` |
| "Sync not working" | Run: `python test_realtime_sync.py` to diagnose |
| "Real-time not updating" | Check Supabase Dashboard → Database → Publications → Enable for tables |

---

## 📚 Full Documentation

See: [REALTIME_SYNC_SETUP.md](REALTIME_SYNC_SETUP.md)

---

## 🎯 Verification Checklist

After setup, verify:

- [ ] `python setup_supabase_tables.py` runs without errors
- [ ] App starts with sync success message
- [ ] `python test_realtime_sync.py` shows all tests passing
- [ ] Create a test case and see it in Supabase Dashboard
- [ ] Edit case and verify change in Supabase
- [ ] `/api/sync/status` endpoint works

---

**All set? Your local and cloud databases are now syncing in real-time! 🎉**
