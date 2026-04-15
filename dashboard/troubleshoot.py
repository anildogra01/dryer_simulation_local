#!/usr/bin/env python3
"""
Troubleshooting script for Flask Dashboard
"""

import sys
import os

print("=" * 60)
print("🔍 TROUBLESHOOTING FLASK DASHBOARD")
print("=" * 60)
print()

# Test 1: Check Python version
print("1️⃣  Checking Python version...")
print(f"   Python: {sys.version}")
if sys.version_info < (3, 7):
    print("   ⚠️  Warning: Python 3.7+ recommended")
else:
    print("   ✅ Python version OK")
print()

# Test 2: Check required packages
print("2️⃣  Checking required packages...")
required = {
    'flask': 'Flask',
    'flask_cors': 'flask-cors',
    'flask_sqlalchemy': 'Flask-SQLAlchemy'
}

missing = []
for module, package in required.items():
    try:
        __import__(module)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} - MISSING")
        missing.append(package)

if missing:
    print(f"\n   ⚠️  Missing packages: {', '.join(missing)}")
    print(f"   Install with: pip install {' '.join(missing)}")
else:
    print("\n   ✅ All packages installed")
print()

# Test 3: Check if port 5000 is available
print("3️⃣  Checking if port 5000 is available...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 5000))
sock.close()

if result == 0:
    print("   ⚠️  Port 5000 is already in use!")
    print("   Solution: Kill the process or use a different port")
    print("   To find process: lsof -i :5000")
else:
    print("   ✅ Port 5000 is available")
print()

# Test 4: Check file structure
print("4️⃣  Checking file structure...")
required_files = {
    'app.py': 'Main application',
    'database.py': 'Database models',
    'templates/dashboard.html': 'Dashboard template',
    'templates/components/header.html': 'Header component',
    'templates/components/metrics.html': 'Metrics component',
    'templates/components/chart.html': 'Chart component',
    'templates/components/activity_feed.html': 'Activity feed component',
    'templates/components/styles.css': 'Styles component',
    'templates/components/scripts.js': 'Scripts component',
}

all_found = True
for filepath, description in required_files.items():
    if os.path.exists(filepath):
        print(f"   ✅ {filepath}")
    else:
        print(f"   ❌ {filepath} - MISSING")
        all_found = False

if not all_found:
    print("\n   ⚠️  Some files are missing!")
else:
    print("\n   ✅ All required files found")
print()

# Test 5: Try to import the app
print("5️⃣  Testing app import...")
try:
    from app import app
    print("   ✅ App imported successfully")
    
    # Check routes
    print("\n   📍 Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"      {rule.endpoint:20s} {rule.rule}")
    
except Exception as e:
    print(f"   ❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 6: Try to initialize database
print("6️⃣  Testing database initialization...")
try:
    from app import app
    from database import db
    
    with app.app_context():
        db.create_all()
        print("   ✅ Database initialized successfully")
        
        # Check tables
        from database import Metric, Activity, ChartData, User
        print(f"\n   📊 Table counts:")
        print(f"      Metrics:    {Metric.query.count()}")
        print(f"      Activities: {Activity.query.count()}")
        print(f"      ChartData:  {ChartData.query.count()}")
        print(f"      Users:      {User.query.count()}")
        
        if Metric.query.count() == 0:
            print("\n   ⚠️  Database is empty. Run: python db_manager.py seed")
            
except Exception as e:
    print(f"   ❌ Database error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 7: Start test server
print("7️⃣  Would you like to start a test server? (yes/no)")
response = input("   > ").lower()

if response in ['yes', 'y']:
    print("\n" + "=" * 60)
    print("🚀 STARTING TEST SERVER")
    print("=" * 60)
    print()
    print("   🌐 Server starting at: http://localhost:5000")
    print("   📊 Dashboard: http://localhost:5000")
    print("   🔌 API: http://localhost:5000/api/metrics")
    print()
    print("   Press CTRL+C to stop")
    print("=" * 60)
    print()
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n✅ Diagnostic complete!")
    print()
    print("Next steps:")
    print("1. Fix any issues shown above")
    print("2. Run: python run_local.py")
    print("3. Open: http://localhost:5000")
    print()

print("=" * 60)
