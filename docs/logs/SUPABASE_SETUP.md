# Supabase Real-Time Integration Guide

## 🚀 Quick Setup

### Step 1: Create Supabase Project
1. Go to https://supabase.com and create a new account/project
2. Create a new PostgreSQL database
3. Copy your project credentials:
   - **Project URL**: `https://[project-id].supabase.co`
   - **Anon Key**: Found in Settings → API → Project API keys
   - **Service Role Key**: For server-side operations (keep secret!)

### Step 2: Environment Configuration

Add these to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
SUPABASE_SYNC_ENABLED=True

# Real-time Settings
REALTIME_SYNC_INTERVAL=5  # seconds
REALTIME_MAX_RETRIES=3
```

### Step 3: Create Tables in Supabase

Run this SQL in Supabase SQL Editor:

```sql
-- Create users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'admin' or 'officer'
    email VARCHAR(150),
    is_active BOOLEAN DEFAULT true,
    force_password_change BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create cases table
CREATE TABLE cases (
    id BIGSERIAL PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE NOT NULL,
    complainant_name VARCHAR(100) NOT NULL,
    complainant_email VARCHAR(150) NOT NULL,
    complainant_contact VARCHAR(30),
    incident_date DATE NOT NULL,
    incident_location VARCHAR(255) NOT NULL,
    barangay_number INT,
    vehicle_details VARCHAR(255),
    narrative TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending', -- 'Pending', 'Ongoing', 'Closed'
    assigned_officer_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create activity_logs table
CREATE TABLE activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create report_exports table
CREATE TABLE report_exports (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    pdf_path VARCHAR(255),
    qr_path VARCHAR(255),
    emailed_to VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable Realtime for all tables
ALTER TABLE users REPLICA IDENTITY FULL;
ALTER TABLE cases REPLICA IDENTITY FULL;
ALTER TABLE activity_logs REPLICA IDENTITY FULL;
ALTER TABLE report_exports REPLICA IDENTITY FULL;
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📝 Usage Examples

### Example 1: Auto-Sync on Insert

```python
from app.services.supabase_realtime_sync import sync_to_supabase

@sync_to_supabase('cases', 'insert')
def create_case(case_data):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO cases (reference_no, complainant_name, ...)
        VALUES (...)
    """)
    mysql.connection.commit()
    return case_data  # This gets synced to Supabase
```

### Example 2: Manual Sync

```python
from app.services.supabase_realtime_sync import supabase_sync

# Sync a single record
supabase_sync.sync_record_to_supabase('cases', {
    'id': 1,
    'reference_no': 'CASE-2024-001',
    'status': 'Pending'
}, operation='update')

# Batch sync multiple records
supabase_sync.batch_sync_to_supabase('cases', [
    {'id': 1, 'status': 'Ongoing'},
    {'id': 2, 'status': 'Closed'}
], operation='update')
```

### Example 3: Subscribe to Real-Time Changes

```python
from app.services.supabase_realtime_sync import supabase_sync

def on_cases_change(payload):
    """Called when cases table changes in Supabase"""
    print(f"Change event: {payload['eventType']}")
    print(f"New record: {payload['new']}")
    print(f"Old record: {payload['old']}")
    # Update local cache or UI

# Subscribe to all changes
supabase_sync.subscribe_to_table('cases', on_cases_change)
```

### Example 4: Pull Data from Supabase

```python
# Get all active users
users = supabase_sync.pull_from_supabase('users', {'is_active': True})

# Get specific case
cases = supabase_sync.pull_from_supabase('cases', {'reference_no': 'CASE-2024-001'})
```

### Example 5: Check Sync Status

```python
status = supabase_sync.get_sync_status()
print(f"Ready: {status['is_ready']}")
print(f"Active subscriptions: {status['active_subscriptions']}")
print(f"Pending syncs: {status['pending_syncs']}")
```

### Example 6: Retry Failed Syncs

```python
# Automatically retry any failed sync operations
result = supabase_sync.retry_failed_syncs()
print(f"Retried: {result['retried']}, Still failing: {result['failed']}")
```

---

## 🔄 How Real-Time Sync Works

### Flow Diagram

```
Local Database (MySQL)  →  Supabase (PostgreSQL)
         ↓                         ↓
    Insert/Update          Real-time trigger
    to local DB                    ↓
         ↓                    Webhook/Event
    @sync_decorator              ↓
         ↓                  Connected Clients
    Sync to Supabase      (WebSocket notify)
         ↓                         ↓
    Success/Queue          Update UI in real-time
```

### Key Features

1. **Bi-directional Sync**: Changes on either side propagate automatically
2. **Conflict Resolution**: Last-write-wins with timestamp comparison
3. **Retry Queue**: Failed syncs are queued and retried
4. **WebSocket Pooling**: Efficient connection management
5. **Error Handling**: Graceful degradation if Supabase unavailable

---

## 🔌 Frontend Real-Time Updates (JavaScript)

Add to your HTML template:

```html
<script>
// Import Supabase client
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

<script>
const { createClient } = window.supabase

const supabaseUrl = '{{ supabase_url }}'
const supabaseKey = '{{ supabase_anon_key }}'
const supabase = createClient(supabaseUrl, supabaseKey)

// Subscribe to case updates
supabase
  .channel('public:cases')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'cases' },
    (payload) => {
      console.log('Case updated:', payload)
      // Update your UI here
      location.reload() // or update specific elements
    }
  )
  .subscribe()
</script>
```

---

## 🛠️ Migration from MySQL to Supabase

### Option 1: Automated Migration

Use the provided migration script:

```bash
python migrate_to_supabase.py
```

### Option 2: Manual Migration

1. Export MySQL data:
   ```bash
   mysqldump -u user -p carnapping_db > backup.sql
   ```

2. Convert SQL syntax (MySQL → PostgreSQL):
   - Replace `INT AUTO_INCREMENT` with `BIGSERIAL`
   - Replace `TINYINT` with `BOOLEAN`
   - Replace `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` with `TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP`

3. Import to Supabase using SQL Editor

---

## ✅ Troubleshooting

### Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Check firewall/network connectivity to supabase.co
- Enable Row Level Security (RLS) policies if needed

### Real-Time Not Working
- Ensure `REPLICA IDENTITY FULL` is set on tables
- Check Supabase Realtime is enabled in project settings
- Verify browser console for WebSocket errors

### Sync Queue Growing
- Check network connectivity
- Retry with: `supabase_sync.retry_failed_syncs()`
- View errors in logs: `supabase_sync.get_sync_status()`

### Performance Issues
- Use batch operations for bulk updates
- Set appropriate `REALTIME_SYNC_INTERVAL`
- Monitor active subscriptions: `supabase_sync.get_sync_status()`

---

## 📊 Monitoring

Check sync health:

```python
from app.services.supabase_realtime_sync import supabase_sync

@app.route('/admin/sync-status')
def sync_status():
    status = supabase_sync.get_sync_status()
    return status  # JSON response
```

---

## 🔐 Security Considerations

1. **Environment Variables**: Never commit `.env` with credentials
2. **Row Level Security (RLS)**: Enable RLS policies in Supabase
3. **API Keys**: Use `ANON_KEY` for frontend, `SERVICE_KEY` for backend
4. **Permissions**: Set appropriate database role permissions

---

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Realtime Subscriptions](https://supabase.com/docs/guides/realtime)
- [Python Client Library](https://github.com/supabase-community/supabase-py)
- [PostgreSQL to MySQL Schema Conversion](https://wiki.postgresql.org/wiki/MySQL_to_PostgreSQL)
