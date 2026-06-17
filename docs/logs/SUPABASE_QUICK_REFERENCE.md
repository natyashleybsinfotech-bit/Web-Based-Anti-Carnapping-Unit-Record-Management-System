# Supabase Real-Time Sync - Quick Reference

## 🎯 What You Get

✅ **Real-time Cloud Database**: PostgreSQL instead of MySQL  
✅ **Automatic Bi-directional Sync**: Changes sync instantly between local and cloud  
✅ **WebSocket Support**: Live updates to all connected clients  
✅ **Conflict Resolution**: Automatic handling of concurrent updates  
✅ **Retry Queue**: Failed syncs are automatically retried  
✅ **Zero Downtime**: Works alongside your existing MySQL  

---

## ⚡ Getting Started in 5 Minutes

### 1️⃣ Create Supabase Account
```
Visit: https://supabase.com/dashboard
Create new project → Copy URL and Keys
```

### 2️⃣ Update `.env`
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_SYNC_ENABLED=True
```

### 3️⃣ Create Tables in Supabase
Copy-paste the SQL from `SUPABASE_SETUP.md` into Supabase SQL Editor

### 4️⃣ Install Packages
```bash
pip install -r requirements.txt
```

### 5️⃣ Migrate Your Data
```bash
python migrate_to_supabase.py
```

✅ **Done!** Your app now uses Supabase real-time sync

---

## 📚 Common Tasks

### Auto-Sync on Create
```python
from app.services.supabase_realtime_sync import supabase_sync

# After inserting into MySQL
case_data = {'id': 1, 'reference_no': 'CASE-001', 'status': 'Pending'}
supabase_sync.sync_record_to_supabase('cases', case_data, 'insert')
```

### Batch Sync Multiple Records
```python
cases = [
    {'id': 1, 'status': 'Ongoing'},
    {'id': 2, 'status': 'Closed'}
]
supabase_sync.batch_sync_to_supabase('cases', cases, 'update')
```

### Listen to Real-Time Changes
```python
def on_change(payload):
    print(f"Change: {payload['eventType']}")
    print(f"Data: {payload['new']}")

supabase_sync.subscribe_to_table('cases', on_change)
```

### Pull Data from Supabase
```python
# Get all pending cases
pending = supabase_sync.pull_from_supabase('cases', {'status': 'Pending'})
```

### Check Sync Health
```python
status = supabase_sync.get_sync_status()
print(f"Ready: {status['is_ready']}")
print(f"Subscriptions: {status['active_subscriptions']}")
print(f"Pending syncs: {status['pending_syncs']}")
```

### Retry Failed Syncs
```python
result = supabase_sync.retry_failed_syncs()
print(f"Retried: {result['retried']}, Failed: {result['failed']}")
```

---

## 🔧 Frontend Real-Time Updates

Add to your HTML template:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
const { createClient } = window.supabase
const supabase = createClient(
  '{{ SUPABASE_URL }}',
  '{{ SUPABASE_ANON_KEY }}'
)

// Subscribe to case changes
supabase
  .channel('cases')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'cases' },
    (payload) => {
      console.log('Case updated:', payload)
      // Update UI here
    }
  )
  .subscribe()
</script>
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Connection Failed** | Check SUPABASE_URL and SUPABASE_ANON_KEY in `.env` |
| **Real-time Not Working** | Ensure `REPLICA IDENTITY FULL` is set on tables |
| **Sync Queue Growing** | Run `supabase_sync.retry_failed_syncs()` |
| **Missing Records** | Run migration script: `python migrate_to_supabase.py` |
| **High Latency** | Check WebSocket connection in browser DevTools |

---

## 📊 Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Your Flask App │◄───────►│   Supabase       │
│  (Local MySQL)  │ REST/WS │  (PostgreSQL)    │
└─────────────────┘         └──────────────────┘
       │                            ▲
       │ Insert/Update/Delete       │ Real-time Changes
       │                            │
    sync_record_to_              Auto-notify
    supabase()                  connected clients
```

---

## 📖 Documentation Files

- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Complete setup guide with all SQL
- **[SUPABASE_INTEGRATION_EXAMPLES.md](SUPABASE_INTEGRATION_EXAMPLES.md)** - Code examples
- **[migrate_to_supabase.py](migrate_to_supabase.py)** - Data migration script
- **[app/services/supabase_realtime_sync.py](app/services/supabase_realtime_sync.py)** - Core sync service

---

## 🆘 Need Help?

- Check logs: `supabase_sync.get_sync_status()`
- Debug with: `print(supabase_sync.sync_queue)`
- Health endpoint: `/admin/sync-status`
- Supabase docs: https://supabase.com/docs
