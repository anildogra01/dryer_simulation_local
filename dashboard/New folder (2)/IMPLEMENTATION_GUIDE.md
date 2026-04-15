# GRAIN DRYER SYSTEM - IMPLEMENTATION GUIDE
## Remaining Features Implementation

### COMPLETED ✅
1. **Prominent Back to Home Button** - Added at bottom alongside STOP and RESTART buttons
2. **User Model in Database** - Added User table with authentication fields
3. **Database Schema Updates** - Added user_id to Simulation and Comment models

### TO IMPLEMENT 📋

---

## 1. USER AUTHENTICATION SYSTEM

### A. Create Login/Register Pages

**File: `/templates/login.html`**
```html
- Login form with username/password
- "Register" link
- "Remember Me" checkbox
- Session management with Flask-Login
```

**File: `/templates/register.html`**
```html
- Registration form: username, email, password, full_name
- Password confirmation
- Auto-create first user as admin
```

### B. Update app.py for Authentication

```python
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
@app.route('/logout')
```

### C. Protect Routes

```python
@app.route('/simulation')
@login_required
def simulation():
    # Only logged-in users can run simulations

@app.route('/settings')
@login_required  
def settings():
    if not current_user.is_admin:
        abort(403)  # Admin-only access
```

### D. Link Simulations to Users

```python
# When creating simulation:
simulation = Simulation(
    user_id=current_user.id,  # Link to logged-in user
    crop_id=crop_id,
    ...
)
```

---

## 2. SETTINGS PAGE ENHANCEMENTS

### A. Add Subtitles for All Pages

Update `settings.html` to include:

```html
<!-- Page Subtitles Section -->
<div class="settings-box">
    <h3>📝 Page Subtitles & Descriptions</h3>
    
    <div class="mb-3">
        <label>Home Page Subtitle:</label>
        <input id="homeSubtitle" value="Advanced Modeling & Analysis Platform">
    </div>
    
    <div class="mb-3">
        <label>Simulation Page Subtitle:</label>
        <input id="simSubtitle" value="Real-Time Monitoring & Control">
    </div>
    
    <div class="mb-3">
        <label>Crop Management Subtitle:</label>
        <input id="cropSubtitle" value="Manage grain types and their properties">
    </div>
    
    <div class="mb-3">
        <label>History Page Subtitle:</label>
        <input id="historySubtitle" value="View and analyze past simulation runs">
    </div>
    
    <div class="mb-3">
        <label>Reports Page Subtitle:</label>
        <input id="reportsSubtitle" value="Generate comprehensive simulation reports">
    </div>
</div>

<!-- Description Text Section -->
<div class="settings-box">
    <h3>📄 Page Description Blocks</h3>
    
    <div class="mb-3">
        <label>Simulation Page Description:</label>
        <textarea id="simDescription" rows="3">Execute grain drying simulations...</textarea>
    </div>
    
    <div class="mb-3">
        <label>Crop Management Description:</label>
        <textarea id="cropDescription" rows="3">Manage grain types...</textarea>
    </div>
    
    <!-- Add for all pages -->
</div>
```

### B. Apply Subtitles Globally

In each page's script section:
```javascript
if (settings.subtitles) {
    document.querySelector('.subtitle').textContent = settings.subtitles.simulation;
}
```

---

## 3. PERSONAL HISTORY FILTERING

### A. Update History Page

```python
@app.route('/history')
@login_required
def history():
    # Show only current user's simulations
    simulations = Simulation.query.filter_by(
        user_id=current_user.id
    ).order_by(Simulation.created_at.desc()).all()
    
    return render_template('history.html', 
                         simulations=simulations,
                         user=current_user)
```

### B. Add User Info to History Template

```html
<div class="header">
    <h1>📊 My Simulation History</h1>
    <p>Viewing simulations for: <strong>{{ user.full_name }}</strong></p>
    <p>Total Simulations: <strong>{{ simulations|length }}</strong></p>
</div>
```

---

## 4. ADMIN-ONLY SETTINGS ACCESS

### A. Add Admin Check Decorator

```python
from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.route('/settings')
@admin_required
def settings():
    return render_template('settings.html')
```

### B. Hide Settings Link for Non-Admins

In index.html:
```html
{% if current_user.is_authenticated and current_user.is_admin %}
<a href="/settings">⚙️ Settings</a>
{% endif %}
```

---

## 5. DATABASE INITIALIZATION

### A. Create Default Admin User

```python
def init_db(app):
    with app.app_context():
        db.create_all()
        
        # Create default admin if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@graindrying.com',
                full_name='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this!
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created - username: admin, password: admin123")
```

---

## 6. REQUIRED PACKAGES

Add to `requirements.txt`:
```
Flask-Login==0.6.3
```

Install with:
```bash
pip install Flask-Login --break-system-packages
```

---

## IMPLEMENTATION STEPS

### Step 1: Database
```bash
# Delete old database
del grain_dryer.db

# Restart server - will create new schema with User table
python run_local.py
```

### Step 2: Create Login Pages
- Create login.html
- Create register.html
- Add authentication routes to app.py

### Step 3: Protect Routes
- Add @login_required to simulation, history, reports
- Add @admin_required to settings
- Add current_user checks in templates

### Step 4: Update Templates
- Add user info displays
- Filter history by user_id
- Hide/show features based on user role

### Step 5: Test
- Register new user
- Login/logout
- Run simulations (should be linked to user)
- View personal history
- Try accessing settings (admin vs non-admin)

---

## SECURITY CONSIDERATIONS

1. **Change Default Admin Password** after first login
2. **Use HTTPS** in production
3. **Add CSRF Protection** with Flask-WTF
4. **Add Rate Limiting** on login attempts
5. **Add Email Verification** for registration
6. **Store sessions securely** with app.secret_key

---

## CURRENT STATE

✅ Database models ready
✅ User/Simulation/Comment relationships defined
✅ Back to Home button prominent
✅ Icon customization complete
✅ Settings page structure ready

⏳ Need to implement:
- Login/Register pages
- Flask-Login integration
- Route protection
- User filtering in queries
- Admin checks
- Subtitle/description customization

