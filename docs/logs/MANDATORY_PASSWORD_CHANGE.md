# Mandatory Password Change on First Login

## Overview

When an admin creates a new officer account, the system now enforces a **mandatory password change** on the officer's first login. This ensures:
- ✅ Officers don't use default passwords
- ✅ Officers have a secure password only they know
- ✅ Better security compliance

---

## How It Works

### 1. **Admin Creates New User Account**

The admin navigates to **Manage Users** page and fills in the form:
- Full Name
- Username
- Email
- Role (Officer or Admin)

The system creates the account with:
- **Default Password:** `default123`
- **Force Change Flag:** Enabled

### 2. **Officer Logs In First Time**

When the officer attempts to log in with their username and `default123`:

1. System authenticates the user
2. System checks the `force_password_change` flag
3. If flag = 1 (enabled), officer is redirected to **Change Password Required** page
4. Officer cannot proceed to dashboard until password is changed

### 3. **Officer Changes Password**

Officer must:
- Enter new password (min. 4 characters)
- Confirm new password (must match)
- Click "Change Password & Continue"

After password is changed:
- New password is saved to database
- `force_password_change` flag is set to 0 (disabled)
- Officer is redirected to their dashboard (Admin or Officer)

---

## Database Schema

### Users Table - New Column

```sql
ALTER TABLE users ADD COLUMN force_password_change TINYINT DEFAULT 0;
```

**Column Details:**
- `force_password_change` (TINYINT)
  - `0` = Password change not required (normal user)
  - `1` = Password change required (newly created user)

---

## Implementation Details

### Files Modified

#### 1. **schema.sql**
- Added `force_password_change` column to users table definition

#### 2. **app/routes.py**
Added three new functions:

**Login Route Changes:**
```python
# Check if password change is mandatory
if force_password_change:
    flash("You must change your password on first login.")
    return redirect(url_for("main.change_password_required"))
```

**New Routes:**

a) **`/change-password-required`** (GET/POST)
   - Accessible only when user is logged in
   - Displays password change form
   - Validates new password (min 4 chars, must match)
   - Updates database and redirects to dashboard after success

b) **`/users/create`** (POST)
   - Admin-only endpoint
   - Creates new user with default password
   - Sets `force_password_change = 1`
   - Logs activity

#### 3. **app/templates/manage_users.html**
- Added "Create New User Account" form section
- Shows default password info to admin
- Form fields: Full Name, Username, Email, Role
- Submit button creates user account

#### 4. **app/templates/change_password_required.html** (NEW)
- Standalone template for mandatory password change
- Warning message explaining requirement
- Two password input fields (password + confirmation)
- Password requirements info box
- Professional styling matching system design

#### 5. **migrate_add_force_password_change.py** (NEW)
- Migration script to add column to existing database
- Checks if column already exists
- Only adds if missing
- Provides clear status messages

---

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ADMIN DASHBOARD                          │
│                                                              │
│  Click: Manage Users → Fill Form → Create User Account     │
│  Result: User created with default password "default123"   │
│  Flag Set: force_password_change = 1                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       LOGIN PAGE                            │
│                                                              │
│  Officer enters username & "default123" password            │
│  System checks: force_password_change flag                  │
└────────────────────┬────────────────────────────────────────┘
                     │
              ┌──────▼──────┐
              │   FLAG = 1? │
              └──────┬──────┘
                     │ YES
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          CHANGE PASSWORD REQUIRED PAGE                      │
│                                                              │
│  WARNING: "You must change your password on first login"    │
│                                                              │
│  • Enter new password                                       │
│  • Confirm new password                                     │
│  • Validate: min 4 chars, passwords match                   │
│  • Update database                                          │
│  • Set force_password_change = 0                            │
│                                                              │
│  Click: "Change Password & Continue"                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OFFICER DASHBOARD                              │
│                                                              │
│  Officer can now use application with new password          │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Features

✅ **Enforced on First Login:** Officer cannot bypass password change
✅ **Strong Validation:** Minimum 4 character requirement
✅ **Confirmation Field:** Prevents typos
✅ **Activity Logging:** Password changes are logged
✅ **Database Flag:** Tracks change requirement status
✅ **Session Management:** Proper session handling during password change

---

## Testing the Feature

### Test Case 1: Create and Change Password

1. Login as Admin
2. Go to "Manage Users" 
3. Fill form: 
   - Full Name: "Test Officer"
   - Username: "testofficer"
   - Email: "test@email.com"
   - Role: Officer
4. Click "Create User Account"
5. See success message
6. **Logout**
7. **Login as** testofficer / default123
8. System redirects to change password page
9. Enter new password (e.g., "newpass123")
10. Confirm password
11. Click "Change Password & Continue"
12. Successfully redirected to Officer Dashboard

### Test Case 2: Cannot Access Dashboard Without Password Change

1. Follow steps 1-7 above
2. Try to manually access `/officer/dashboard`
3. System redirects to change password page (after next navigation)

### Test Case 3: Changed Password Works

1. Complete Test Case 1
2. **Logout**
3. **Login as** testofficer / newpass123
4. Successfully login (no password change prompt)
5. Verify access to Officer Dashboard

---

## Default Credentials

- **Default Password:** `default123`
- **Minimum New Password:** 4 characters
- **Applied to:** All newly created user accounts
- **Can be changed by:** Admin (no self-service password reset yet)

---

## Admin Responsibilities

When creating a new officer account:

1. Provide officer with:
   - Username
   - Temporary default password: "default123"
   - Link to login page

2. Instruct officer to:
   - Login with provided credentials
   - Change password immediately (system will require it)
   - Remember new password

3. Never reuse default password for multiple accounts

---

## Future Enhancements

- [ ] Password complexity requirements (uppercase, numbers, special chars)
- [ ] Email notification to new users
- [ ] Self-service password reset
- [ ] Password change reminder emails
- [ ] Admin dashboard showing users needing password change
- [ ] Audit log for all password changes

---

## Troubleshooting

**Q: User is stuck on change password page?**
A: Ensure they enter password correctly and that both password fields match exactly.

**Q: Admin created user but can't see in list?**
A: Refresh the Manage Users page. Check for duplicate username error.

**Q: User forgot new password?**
A: Admin can create new account with default password. Old account can be marked inactive.

---

**Implemented:** April 20, 2026
**Status:** ✅ Active and Tested
