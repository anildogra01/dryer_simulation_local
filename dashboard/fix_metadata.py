#!/usr/bin/env python3
"""
Quick fix script to patch the metadata issue
"""

import os
import shutil

print("🔧 Fixing the 'metadata' reserved word issue...")

# Read the current database.py
if not os.path.exists('database.py'):
    print("❌ database.py not found!")
    exit(1)

# Backup the old file
shutil.copy('database.py', 'database.py.backup')
print("✅ Backed up database.py to database.py.backup")

# Read and fix the file
with open('database.py', 'r') as f:
    content = f.read()

# Replace all instances of the problematic metadata field
content = content.replace("metadata = db.Column(db.Text, default='{}')", 
                         "extra_data = db.Column(db.Text, default='{}')")
content = content.replace("'metadata': json.loads(self.metadata)", 
                         "'extra_data': json.loads(self.extra_data)")
content = content.replace("metadata=json.dumps(data.get('metadata', {}))", 
                         "extra_data=json.dumps(data.get('extra_data', {}))")

# Write the fixed file
with open('database.py', 'w') as f:
    f.write(content)

print("✅ Fixed database.py")

# Also fix app.py if it exists
if os.path.exists('app.py'):
    shutil.copy('app.py', 'app.py.backup')
    print("✅ Backed up app.py to app.py.backup")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    content = content.replace("metadata=json.dumps(data.get('metadata', {}))", 
                             "extra_data=json.dumps(data.get('extra_data', {}))")
    
    with open('app.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed app.py")

# Remove old database if it exists
if os.path.exists('dashboard.db'):
    os.remove('dashboard.db')
    print("✅ Removed old database.db")

print("\n" + "="*60)
print("✅ FIX COMPLETE!")
print("="*60)
print("\nNow run:")
print("  python run_local.py")
print("\nOr:")
print("  python app.py")
print("="*60)
