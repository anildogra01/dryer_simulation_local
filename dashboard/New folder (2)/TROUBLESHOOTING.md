# 🔧 TROUBLESHOOTING GUIDE

## Problem: "No response on localhost:5000"

### Quick Diagnostics

Run this first to diagnose the issue:
```bash
python troubleshoot.py
```

This will check:
- Python version
- Required packages
- Port availability
- File structure
- Database initialization

---

## Common Issues & Solutions

### 1. ❌ Port 5000 Already in Use

**Symptoms:**
- "Address already in use" error
- Cannot connect to localhost:5000

**Solutions:**

**Option A: Kill the process using port 5000**
```bash
# On Linux/Mac
lsof -i :5000
kill -9 <PID>

# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Option B: Use a different port**
Edit `app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
```
Then access: http://localhost:5001

---

### 2. ❌ Missing Dependencies

**Symptoms:**
- "ModuleNotFoundError: No module named 'flask'"
- Import errors

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install Flask flask-cors Flask-SQLAlchemy
```

**Still not working?**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Try with --user flag
pip install --user -r requirements.txt
```

---

### 3. ❌ Template Not Found Error

**Symptoms:**
- "TemplateNotFound: dashboard.html"
- "jinja2.exceptions.TemplateNotFound"

**Solution:**

Check file structure:
```bash
ls -la templates/
ls -la templates/components/
```

Should show:
```
templates/
├── dashboard.html
└── components/
    ├── header.html
    ├── metrics.html
    ├── chart.html
    ├── activity_feed.html
    ├── styles.css
    └── scripts.js
```

**If files are missing**, re-download the complete package.

---

### 4. ❌ Database Errors

**Symptoms:**
- "OperationalError: no such table"
- "Database is locked"

**Solution:**

Reset the database:
```bash
# Remove old database
rm dashboard.db

# Initialize fresh database
python db_manager.py init
python db_manager.py seed
```

---

### 5. ❌ Server Starts But Page Won't Load

**Symptoms:**
- Server logs show "Running on http://0.0.0.0:5000"
- Browser shows "This site can't be reached"

**Solutions:**

**A. Try different localhost variants:**
- http://localhost:5000
- http://127.0.0.1:5000
- http://0.0.0.0:5000

**B. Check firewall:**
```bash
# Linux/Mac
sudo ufw allow 5000

# Windows - Allow through Windows Firewall
```

**C. Try the simple test app:**
```bash
python simple_app.py
```

---

### 6. ❌ Blank Page or 404 Error

**Symptoms:**
- Page loads but is blank
- "404 Not Found" error

**Solutions:**

**A. Check routes:**
```bash
python -c "from app import app; print([str(r) for r in app.url_map.iter_rules()])"
```

**B. Clear browser cache:**
- Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

**C. Test API directly:**
```bash
curl http://localhost:5000/api/metrics
```

Should return JSON data.

---

### 7. ❌ JavaScript Errors in Browser Console

**Symptoms:**
- Charts not loading
- Data not displaying
- Console shows errors

**Solutions:**

**A. Check browser console:**
- Press F12
- Go to Console tab
- Look for errors

**B. Common JavaScript fixes:**

If Chart.js fails to load:
```html
<!-- In dashboard.html, verify this line exists: -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

If fetch fails:
- Check browser console for CORS errors
- Verify flask-cors is installed

---

## Step-by-Step Fresh Start

If nothing works, try this clean installation:

```bash
# 1. Remove old files
rm dashboard.db
rm -rf __pycache__

# 2. Create fresh virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python db_manager.py init
python db_manager.py seed

# 5. Test with simple app first
python simple_app.py

# 6. If simple app works, try full app
python app.py
```

---

## Testing Checklist

Use this checklist to verify everything works:

- [ ] Python 3.7+ installed
- [ ] All dependencies installed (`pip list | grep -i flask`)
- [ ] Port 5000 is available
- [ ] All template files exist in `templates/` and `templates/components/`
- [ ] Database initialized (`dashboard.db` exists)
- [ ] Can run `python simple_app.py` successfully
- [ ] Browser can access http://localhost:5000
- [ ] API endpoints return data (test with curl or browser)
- [ ] Dashboard displays metrics and activities
- [ ] No errors in terminal
- [ ] No errors in browser console (F12)

---

## Alternative: Use Simple App

If the full app still doesn't work, use the simple standalone version:

```bash
python simple_app.py
```

This version:
- ✅ No database required
- ✅ No component dependencies
- ✅ Single file
- ✅ Works immediately

Once this works, you can troubleshoot the full app.

---

## Get More Help

### Enable Debug Mode

In `app.py`, ensure debug is on:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

This shows detailed error messages.

### Check Logs

Look at the terminal where you ran the server for error messages.

### Test Individual Components

```bash
# Test if app imports
python -c "from app import app; print('OK')"

# Test if database imports
python -c "from database import db; print('OK')"

# Test database connection
python db_manager.py info
```

---

## Still Not Working?

1. Run the diagnostic script:
   ```bash
   python troubleshoot.py
   ```

2. Try the simple app:
   ```bash
   python simple_app.py
   ```

3. Check Python version:
   ```bash
   python --version
   ```
   (Should be 3.7 or higher)

4. Verify you're in the correct directory:
   ```bash
   ls -la
   ```
   (Should see app.py, database.py, etc.)

---

## Common Error Messages & Fixes

| Error | Solution |
|-------|----------|
| "Port 5000 is in use" | Kill process or use different port |
| "ModuleNotFoundError" | Install missing package with pip |
| "TemplateNotFound" | Check templates/ directory structure |
| "No such table" | Run `python db_manager.py init` |
| "Connection refused" | Check firewall, try 127.0.0.1 |
| "Blank page" | Check browser console for errors |
| "CORS error" | Install flask-cors package |

---

Good luck! 🚀
