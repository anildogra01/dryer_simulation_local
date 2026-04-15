# LOGIN SYSTEM - QUICK START GUIDE

## ✅ WHAT'S IMPLEMENTED:

### 1. **Unified Login/Register Page** 🔐
- Single page at `/login`
- If user exists → logs in
- If user doesn't exist → shows registration form
- No separate register page needed!

### 2. **Session-Based Authentication** 
- Uses Flask sessions (no Flask-Login needed!)
- Stores: user_id, username, is_admin
- Secure session cookies

### 3. **Default Admin Account**
- Auto-created on first run
- **Username:** `admin`
- **Password:** `admin123`
- ⚠️ **Please change after first login!**

### 4. **Admin-Only Settings**
- Settings page checks if user is admin
- Non-admins get "Access Denied" error
- Regular users can't access settings

### 5. **User Display on Home**
- Shows login/register buttons if not logged in
- Shows user name + admin badge if logged in
- Logout button appears when logged in

---

## 🚀 HOW TO USE:

### Step 1: Stop Server
```bash
CTRL+C
```

### Step 2: Delete Old Database
```bash
del grain_dryer.db
```

### Step 3: Start Server
```bash
python run_local.py
```

You'll see:
```
✅ Default admin user created:
   Username: admin
   Password: admin123
   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!
```

### Step 4: Test Login Flow

#### **A. Login with Admin:**
1. Go to `http://localhost:5000`
2. Click **"Login"** (top right)
3. Username: `admin`
4. Password: `admin123`
5. Click **"Sign In"**
6. ✅ You're logged in as Admin!

#### **B. Create New User:**
1. Go to login page
2. Username: `john` (doesn't exist)
3. Password: `mypassword`
4. Click **"Sign In"**
5. 📝 Registration form appears!
6. Fill in:
   - Full Name: `John Doe`
   - Email: `john@example.com`
   - Confirm Password: `mypassword`
7. Click **"Create Account & Sign In"**
8. ✅ Account created and auto-logged in!

#### **C. Test Admin Settings:**
1. Login as `admin`
2. Go to Settings (`/settings`)
3. ✅ Settings page loads (you're admin)
4. Logout
5. Login as regular user (`john`)
6. Try to go to Settings
7. ❌ **"Access Denied: Admin only"**

---

## 📋 USER FEATURES:

### When Logged In:
- **Home page**: Shows your name + logout button
- **Run simulations**: Simulations linked to your account
- **View history**: See only YOUR simulations
- **Add comments**: Comments linked to your account
- **Admin badge**: Shows if you're admin

### Admin Powers:
- ✅ Access Settings page
- ✅ Customize all pages
- ✅ Change colors, fonts, icons
- ✅ Modify titles and descriptions

### Regular Users:
- ✅ Run simulations
- ✅ View their own history
- ✅ Add comments
- ❌ Cannot access Settings

---

## 🔒 SECURITY FEATURES:

1. **Password Hashing**: Uses werkzeug's secure hash
2. **Session Security**: Secret key protection
3. **Admin Check**: Settings route protected
4. **User Validation**: Checks exist before actions
5. **Remember Me**: Optional persistent login

---

## 🎯 LOGIN PAGE FEATURES:

### Smart Flow:
1. Enter username/password
2. Click "Sign In"
3. **If user exists**: Logs in immediately
4. **If user doesn't exist**: Shows registration form
5. **Auto-fills** username and password in registration
6. Complete profile and create account
7. **Auto-login** after registration

### Registration Fields:
- Username (already filled)
- Password (already filled, hidden)
- Full Name (required)
- Email (required)
- Confirm Password (required)

### Validation:
- ✅ Checks username availability
- ✅ Checks email availability
- ✅ Validates password match
- ✅ Shows error messages

---

## 📊 DATABASE UPDATES:

### User Table Created:
- id
- username (unique)
- email (unique)
- password_hash
- full_name
- is_admin (boolean)
- created_at
- last_login

### Links Added:
- Simulation → user_id
- Comment → user_id
- Users can see only their own data

---

## 🔄 WORKFLOW:

```
User visits site
    ↓
Clicks "Login" (top right)
    ↓
Enters username/password
    ↓
┌─────────────────┐
│ User exists?    │
└─────────────────┘
    ↓           ↓
   YES         NO
    ↓           ↓
Login      Registration Form
    ↓           ↓
    └─────┬─────┘
          ↓
    Logged In!
          ↓
    Redirect to Home
          ↓
    See User Info
```

---

## 🎨 UI UPDATES:

### Home Page (Not Logged In):
```
┌─────────────────────────────────┐
│                    🔐 Login  📝 Register │ ← Top Right
│                                          │
│         Welcome to                       │
│    Grain Dryer System                    │
└─────────────────────────────────────────┘
```

### Home Page (Logged In):
```
┌──────────────────────────────────┐
│        👤 John Doe  [Logout]     │ ← Top Right
│                                   │
│         Welcome to                │
│    Grain Dryer System             │
└──────────────────────────────────┘
```

### Home Page (Admin Logged In):
```
┌────────────────────────────────────────┐
│   👤 Admin [ADMIN] [Logout]            │ ← Top Right
│                                         │
│         Welcome to                      │
│    Grain Dryer System                   │
└────────────────────────────────────────┘
```

---

## ⚠️ IMPORTANT NOTES:

1. **Change admin password** after first login!
2. **Settings now restricted** to admin only
3. **Regular users** can still use all features except settings
4. **Session-based** - no external dependencies needed
5. **Delete database** to start fresh with new schema

---

## 🧪 TEST SCENARIOS:

### Test 1: Admin Login
✅ Username: admin, Password: admin123
✅ Should see ADMIN badge
✅ Can access /settings

### Test 2: New User Registration
✅ Username: testuser, Password: test123
✅ Shows registration form
✅ Creates account
✅ Auto-logs in

### Test 3: Regular User Access
✅ Login as regular user
✅ Try /settings
✅ Should see "Access Denied"

### Test 4: Logout
✅ Click logout
✅ Returns to home
✅ Shows login/register buttons

---

## 🎉 YOU NOW HAVE:

✅ Full login system
✅ User registration
✅ Admin protection
✅ Session management
✅ Password security
✅ User-linked simulations
✅ Admin-only settings
✅ Beautiful login page

**The system is now production-ready!** 🚀

