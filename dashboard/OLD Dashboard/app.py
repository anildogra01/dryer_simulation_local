"""
Flask App for Grain Dryer Simulation
Main application file with all routes
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from pathlib import Path
import sys
import os

# Set up paths
BASE_DIR = Path(__file__).parent.absolute()
DATABASE_DIR = BASE_DIR / 'database'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Create directories if they don't exist
DATABASE_DIR.mkdir(exist_ok=True)

# Add current directory to path
sys.path.insert(0, str(BASE_DIR))

# Change to base directory
os.chdir(BASE_DIR)

print("="*70)
print("INITIALIZING GRAIN DRYER SIMULATION")
print("="*70)
print(f"Base Directory: {BASE_DIR}")
print(f"Database Directory: {DATABASE_DIR}")
print(f"Templates Directory: {TEMPLATES_DIR}")
print("="*70)

from crop_master_database import CropMasterDB
from simulation_transaction_db import SimulationTransactionDB
from enhanced_fortran_interface import EnhancedFortranDryerInterface

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize databases with explicit paths
print("\n📊 Initializing databases...")
try:
    crop_db = CropMasterDB(db_path=str(DATABASE_DIR / 'crop_master.db'))
    print("✅ Crop database initialized")
    crops = crop_db.get_all_crops()
    print(f"✅ Found {len(crops)} crops in database:")
    for crop in crops:
        print(f"   - {crop['crop_name']}")
except Exception as e:
    print(f"❌ Crop database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    transaction_db = SimulationTransactionDB(db_path=str(DATABASE_DIR / 'simulation_transactions.db'))
    print("✅ Transaction database initialized")
except Exception as e:
    print(f"❌ Transaction database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    fortran = EnhancedFortranDryerInterface()
    print("✅ Fortran interface initialized")
except Exception as e:
    print(f"❌ Fortran interface initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*70)

@app.route('/')
def index():
    """Main dashboard"""
    try:
        crops = crop_db.get_all_crops()
        print(f"📊 Loading dashboard with {len(crops)} crops")
        for crop in crops:
            print(f"   - {crop['crop_name']}")
        return render_template('dashboard_with_monitoring.html', crops=crops)
    except Exception as e:
        print(f"❌ Error loading dashboard: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><pre>{traceback.format_exc()}</pre>"

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    """Run the dryer simulation"""
    try:
        # Get form data
        user_info = {
            'user_name': request.form.get('user_name'),
            'project_name': request.form.get('project_name'),
            'address': request.form.get('address')
        }
        
        crop_name = request.form.get('crop_name')
        model_type = request.form.get('model_type', 'fixed_bed')
        
        process_params = {
            'initial_moisture': float(request.form.get('initial_moisture')),
            'target_moisture': float(request.form.get('target_moisture')),
            'grain_temp': float(request.form.get('grain_temp')),
            'air_temp': float(request.form.get('air_temp')),
            'air_rh': float(request.form.get('air_rh')),
            'air_flow_rate': float(request.form.get('air_flow_rate')),
            'grain_flow_rate': float(request.form.get('grain_flow_rate', 0)),
            'width': float(request.form.get('width', 1.0)),
            'length': float(request.form.get('length', 5.0))
        }
        
        # Run simulation
        print("\n" + "="*70)
        print("STARTING SIMULATION")
        print("="*70)
        result = fortran.run_simulation(model_type, crop_name, process_params, user_info)
        
        if result.get('success'):
            # Redirect to results page
            sim_id = result.get('sim_id')
            return redirect(url_for('results', sim_id=sim_id))
        else:
            return f"<h1>Error</h1><p>{result.get('error')}</p><a href='/'>Back</a>"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><p>{str(e)}</p><a href='/'>Back</a>"

@app.route('/results/<int:sim_id>')
def results(sim_id):
    """Display simulation results"""
    # Get simulation from database
    sim = transaction_db.get_simulation_by_id(sim_id)
    
    if not sim:
        return "<h1>Simulation not found</h1><a href='/'>Back</a>"
    
    # Parse results JSON
    import json
    if sim['results_json']:
        parsed = json.loads(sim['results_json'])
    else:
        parsed = {}
    
    # Prepare data for template
    if 'parsed' in parsed and parsed['parsed'].get('success'):
        data = parsed['parsed']
        time_series = data.get('time_series', [])
        times = [p['time_hr'] for p in time_series]
        moistures = [p['avg_moisture_pct'] for p in time_series]
    else:
        data = {}
        times = []
        moistures = []
    
    return render_template('results.html',
                         sim_id=sim_id,
                         sim=sim,
                         user_info={'user_name': sim['user_name'], 
                                   'project_name': sim['project_name'],
                                   'address': sim['address']},
                         crop_name=sim['crop_name'],
                         input_params=data.get('input_params', {}),
                         summary=data.get('summary', {}),
                         time_series=data.get('time_series', []),
                         times=times,
                         moistures=moistures)

@app.route('/download_pdf/<int:sim_id>')
def download_pdf(sim_id):
    """Download PDF report"""
    sim = transaction_db.get_simulation_by_id(sim_id)
    
    if not sim or not sim['pdf_report_path']:
        return "<h1>PDF not found</h1><a href='/'>Back</a>"
    
    pdf_path = Path(sim['pdf_report_path'])
    if pdf_path.exists():
        return send_file(str(pdf_path), as_attachment=True, 
                        download_name=f"dryer_report_{sim_id}.pdf")
    else:
        return "<h1>PDF file not found</h1><a href='/'>Back</a>"

@app.route('/crop_master')
def crop_master():
    """Crop master database management"""
    try:
        crops = crop_db.get_all_crops()
        print(f"📊 Loading crop master with {len(crops)} crops")
        return render_template('crop_master_ui.html', crops=crops)
    except Exception as e:
        print(f"❌ Error loading crop master: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><pre>{traceback.format_exc()}</pre>"

@app.route('/crop_master/add', methods=['POST'])
def add_crop():
    """Add new crop"""
    crop_data = {
        'crop_name': request.form.get('crop_name'),
        'specific_surface_area': float(request.form.get('specific_surface_area')),
        'heat_capacity_air': float(request.form.get('heat_capacity_air')),
        'heat_capacity_dry_product': float(request.form.get('heat_capacity_dry_product')),
        'heat_capacity_water_vapor': float(request.form.get('heat_capacity_water_vapor')),
        'dry_bulk_density': float(request.form.get('dry_bulk_density')),
        'latent_heat_water': float(request.form.get('latent_heat_water'))
    }
    
    crop_db.add_crop(crop_data)
    return redirect(url_for('crop_master'))

@app.route('/crop_master/delete/<int:crop_id>', methods=['POST'])
def delete_crop(crop_id):
    """Delete crop"""
    crop_db.delete_crop(crop_id)
    return redirect(url_for('crop_master'))

@app.route('/history')
def history():
    """View simulation history"""
    simulations = transaction_db.get_recent_simulations(limit=50)
    return render_template('simulation_history.html', simulations=simulations)

@app.route('/api/crops')
def api_crops():
    """API endpoint for crops"""
    crops = crop_db.get_all_crops()
    return jsonify(crops)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        crops = crop_db.get_all_crops()
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        
        return jsonify({
            'status': 'ok',
            'routes': routes,
            'crop_master_exists': '/crop_master' in routes,
            'crops_count': len(crops)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("="*70)
    print("GRAIN DRYER SIMULATION - Flask Server")
    print("="*70)
    print("Dashboard: http://127.0.0.1:5000/")
    print("Crop Master: http://127.0.0.1:5000/crop_master")
    print("History: http://127.0.0.1:5000/history")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)
