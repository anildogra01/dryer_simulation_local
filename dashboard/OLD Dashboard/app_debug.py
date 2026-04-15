"""
DEBUG VERSION - Flask App with Maximum Verbosity
This will show us EXACTLY what's happening
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from pathlib import Path
import sys
import os

# Set up paths
BASE_DIR = Path(__file__).parent.absolute()
DATABASE_DIR = BASE_DIR / 'database'
TEMPLATES_DIR = BASE_DIR / 'templates'

DATABASE_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

print("="*70)
print("DEBUG MODE - GRAIN DRYER SIMULATION")
print("="*70)
print(f"Base Directory: {BASE_DIR}")
print(f"Database Directory: {DATABASE_DIR}")
print(f"Templates Directory: {TEMPLATES_DIR}")
print("="*70)

from crop_master_database import CropMasterDB
from simulation_transaction_db import SimulationTransactionDB
from enhanced_fortran_interface import EnhancedFortranDryerInterface

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))
app.config['SECRET_KEY'] = 'debug-key'

# Initialize databases
crop_db = CropMasterDB(db_path=str(DATABASE_DIR / 'crop_master.db'))
transaction_db = SimulationTransactionDB(db_path=str(DATABASE_DIR / 'simulation_transactions.db'))
fortran = EnhancedFortranDryerInterface()

# Log every request
@app.before_request
def log_request():
    print(f"\n{'='*70}")
    print(f"🌐 INCOMING REQUEST")
    print(f"{'='*70}")
    print(f"Method: {request.method}")
    print(f"Path: {request.path}")
    print(f"Full URL: {request.url}")
    print(f"{'='*70}\n")

# Log every response
@app.after_request
def log_response(response):
    print(f"\n{'='*70}")
    print(f"📤 OUTGOING RESPONSE")
    print(f"{'='*70}")
    print(f"Status: {response.status}")
    print(f"For path: {request.path}")
    print(f"{'='*70}\n")
    return response

# Route 1: Home
@app.route('/')
def index():
    print("✅ HOME ROUTE CALLED")
    crops = crop_db.get_all_crops()
    return render_template('dashboard_with_monitoring.html', crops=crops)

# Route 2: Crop Master - WITH EXTRA DEBUGGING
@app.route('/crop_master')
def crop_master():
    print("="*70)
    print("🎯 CROP_MASTER ROUTE WAS CALLED!")
    print("="*70)
    print("This proves the route is registered and working!")
    print("="*70)
    
    try:
        crops = crop_db.get_all_crops()
        print(f"Retrieved {len(crops)} crops from database")
        
        template_path = TEMPLATES_DIR / 'crop_master_ui.html'
        print(f"Template path: {template_path}")
        print(f"Template exists: {template_path.exists()}")
        
        return render_template('crop_master_ui.html', crops=crops)
    except Exception as e:
        print(f"❌ ERROR IN CROP_MASTER: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error in crop_master</h1><pre>{traceback.format_exc()}</pre>"

# Route 3: History
@app.route('/history')
def history():
    print("✅ HISTORY ROUTE CALLED")
    simulations = transaction_db.get_recent_simulations(limit=50)
    return render_template('simulation_history.html', simulations=simulations)

# Route 4: API Health with route listing
@app.route('/api/health')
def health():
    print("✅ HEALTH CHECK CALLED")
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'path': str(rule),
            'methods': list(rule.methods),
            'endpoint': rule.endpoint
        })
    
    return jsonify({
        'status': 'ok',
        'total_routes': len(routes),
        'routes': routes,
        'crop_master_exists': any('/crop_master' in str(r['path']) for r in routes)
    })

# Route 5: Debug route list
@app.route('/debug/routes')
def debug_routes():
    print("✅ DEBUG ROUTES CALLED")
    output = "<h1>Registered Routes</h1><ul>"
    for rule in app.url_map.iter_rules():
        output += f"<li><b>{rule.methods}</b> {rule} → {rule.endpoint}</li>"
    output += "</ul>"
    return output

# Custom 404 handler
@app.errorhandler(404)
def not_found(e):
    print("="*70)
    print("❌ 404 ERROR HANDLER TRIGGERED!")
    print("="*70)
    print(f"Requested path: {request.path}")
    print(f"Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  - {rule}")
    print("="*70)
    
    return f"""
    <h1>404 - Not Found</h1>
    <p>Path requested: <b>{request.path}</b></p>
    <p>This path is not registered!</p>
    <h2>Available routes:</h2>
    <ul>
    {''.join([f'<li><a href="{rule}">{rule}</a></li>' for rule in app.url_map.iter_rules() if 'GET' in rule.methods])}
    </ul>
    """, 404

if __name__ == '__main__':
    print("\n" + "="*70)
    print("STARTING DEBUG SERVER")
    print("="*70)
    print("📋 Registered Routes:")
    for rule in app.url_map.iter_rules():
        methods = ', '.join(rule.methods)
        print(f"   {methods:40} {str(rule):30} → {rule.endpoint}")
    print("="*70)
    print("\n🌐 Server URLs:")
    print("   Main: http://127.0.0.1:5000/")
    print("   Crop Master: http://127.0.0.1:5000/crop_master")
    print("   Health Check: http://127.0.0.1:5000/api/health")
    print("   Debug Routes: http://127.0.0.1:5000/debug/routes")
    print("="*70)
    print("\nWatch this terminal for detailed logs!\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
