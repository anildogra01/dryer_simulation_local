#!/usr/bin/env python3
"""
Local development server runner
This script sets up and runs the Flask application locally
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask-cors', 'flask-sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("⚠️  Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Installing missing packages...")
        
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        
        print("✅ All packages installed!\n")
    else:
        print("✅ All dependencies are installed\n")

def create_templates_folder():
    """Create templates folder if it doesn't exist"""
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    print(f"✅ Templates directory: {templates_dir}\n")
    return templates_dir

def check_files():
    """Check if required files exist"""
    base_dir = Path(__file__).parent
    required_files = {
        'app.py': base_dir / 'app.py',
        'dashboard.html': base_dir / 'templates' / 'dashboard.html'
    }
    
    missing_files = []
    for name, path in required_files.items():
        if not path.exists():
            missing_files.append(name)
            print(f"⚠️  Missing: {name}")
        else:
            print(f"✅ Found: {name}")
    
    print()
    
    if missing_files:
        print("⚠️  Some files are missing. Please ensure all files are in place.")
        return False
    
    return True

def run_server():
    """Run the Flask development server"""
    print("=" * 60)
    print("🚀 Starting Flask Development Server")
    print("=" * 60)
    print()
    print("📍 Server will be available at:")
    print("   Local:   http://localhost:5000")
    print("   Network: http://0.0.0.0:5000")
    print()
    print("📊 Dashboard: http://localhost:5000")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Import and run the app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main function to set up and run the local server"""
    print("\n" + "=" * 60)
    print("🔧 Flask Local Development Setup")
    print("=" * 60)
    print()
    
    # Check dependencies
    print("1️⃣  Checking dependencies...")
    check_dependencies()
    
    # Create templates folder
    print("2️⃣  Setting up directories...")
    create_templates_folder()
    
    # Check files
    print("3️⃣  Checking required files...")
    if not check_files():
        sys.exit(1)
    
    # Run server
    print("4️⃣  Starting server...")
    print()
    run_server()

if __name__ == '__main__':
    main()
