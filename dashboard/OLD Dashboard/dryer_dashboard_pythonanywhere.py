"""
Grain Dryer Simulation Dashboard - PythonAnywhere Version

WSGI-compatible Flask application for deployment on PythonAnywhere.
Can run alongside existing Flask applications.

Deployment Instructions:
1. Upload all files to PythonAnywhere
2. Install packages in virtual environment
3. Configure WSGI file to mount this app
4. Set up static files and data directories
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import subprocess
import os
import json
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
from datetime import datetime
import shutil
from pathlib import Path
import sys

# Crop Master Integration
from crop_master_database import CropMasterDB
import sqlite3

crop_db = CropMasterDB()


# Configuration for PythonAnywhere
class Config:
    # Base directory - adjust based on your PythonAnywhere path
    BASE_DIR = Path('/home/akdsmartgrow/dryer_simulation/dashboard')
    
    # Working directory for simulations
    WORK_DIR = BASE_DIR / 'simulation_runs'
    
    # Executables directory
    EXE_DIR = BASE_DIR / 'executables'
    
    # Templates directory
    TEMPLATE_DIR = BASE_DIR / 'templates'
    
    # Secret key
    SECRET_KEY = 'dryer_simulation_secret_key_2025'
    
    # Max content length (for file uploads if needed)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

def create_app(config=None):
    """Application factory pattern for PythonAnywhere"""
    
    app = Flask(__name__, 
                template_folder=str(Config.TEMPLATE_DIR))
    
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)
    
    # Ensure directories exist
    Config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize simulation manager
    app.sim_manager = DryerSimulationManager(
        work_dir=Config.WORK_DIR,
        exe_dir=Config.EXE_DIR
    )
    
    # Register routes
    register_routes(app)
    

    # ============================================================
    # CROP MASTER API ENDPOINTS
    # ============================================================
    
    @app.route('/api/crops', methods=['GET'])
    def get_all_crops_api():
        """Get list of all crops"""
        try:
            crops = crop_db.get_all_crops()
            detailed_crops = []
            for crop in crops:
                full_crop = crop_db.get_crop(crop['crop_name'])
                if full_crop:
                    detailed_crops.append(full_crop)
            return jsonify({'success': True, 'crops': detailed_crops})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crops/<crop_identifier>', methods=['GET'])
    def get_crop_api(crop_identifier):
        """Get specific crop by name"""
        try:
            crop = crop_db.get_crop(crop_identifier)
            if not crop:
                return jsonify({'success': False, 'error': 'Crop not found'}), 404
            return jsonify(crop)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/crop-master')
    def crop_master_ui():
        """Serve crop master management interface"""
        return render_template('crop_master_ui.html')
    

    # ============================================================
    # CROP MASTER API ENDPOINTS
    # ============================================================
    
        """Serve crop master management interface"""
        return render_template('crop_master_ui.html')
    
    return app

class DryerSimulationManager:
    """Manages dryer simulations - PythonAnywhere compatible"""
    
    def __init__(self, work_dir, exe_dir):
        self.work_dir = Path(work_dir)
        self.exe_dir = Path(exe_dir)
        self.results_db = []
        
        # Dryer configuration
        self.dryer_types = {
            'fixed_bed': {
                'name': 'Fixed Bed Dryer',
                'exe': 'fixed_bed.exe',
                'input': 'FIXED.DAT',
                'output': 'FIXED.OUT',
                'description': 'Batch operation, stationary grain'
            },
            'crossflow': {
                'name': 'Crossflow Dryer',
                'exe': 'crossflow.exe',
                'input': 'CROSSFLOW.DAT',
                'output': 'CROSSFLOW.OUT',
                'description': 'Continuous operation, perpendicular flow'
            },
            'counterflow': {
                'name': 'Counterflow Dryer',
                'exe': 'counterflow.exe',
                'input': 'COUNTER.DAT',
                'output': 'COUNTER.OUT',
                'description': 'Most efficient, opposite flow directions'
            },
            'concurrent': {
                'name': 'Concurrent Dryer',
                'exe': 'concurrent.exe',
                'input': 'CONCURRENT.DAT',
                'output': 'CONCURRENT.OUT',
                'description': 'Simple design, same flow direction'
            }
        }
    
    def create_input_file(self, dryer_type, params):
        """Create input file for simulation"""
        dryer_info = self.dryer_types[dryer_type]
        input_file = self.work_dir / dryer_info['input']
        
        with open(input_file, 'w') as f:
            f.write(f"{params['xmo']}  {params['thin']}  {params['tin']}  "
                   f"{params['hin']}  {params['cfm']}  {params['bph']}\n")
            f.write(f"{params['xleng']}  {params['dbtpr']}\n")
        
        return input_file
    
    def run_simulation(self, dryer_type, params):
        """Run simulation - PythonAnywhere compatible"""
        dryer_info = self.dryer_types[dryer_type]
        
        # Create input file
        input_file = self.create_input_file(dryer_type, params)
        
        # Executable path
        exe_path = self.exe_dir / dryer_type / dryer_info['exe']
        output_file = self.work_dir / dryer_info['output']
        
        # For PythonAnywhere: executables might not work
        # Alternative: Use pre-computed results or Python-based simulation
        
        # Check if we can run executables
        if not exe_path.exists():
            return {
                'success': False, 
                'error': f'Executable not found. Please use Python-based simulation instead.'
            }
        
        try:
            # Copy input to execution directory
            exec_dir = exe_path.parent
            shutil.copy(input_file, exec_dir / dryer_info['input'])
            
            # Run simulation
            result = subprocess.run(
                [str(exe_path)],
                cwd=str(exec_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Copy output back
            out_file = exec_dir / dryer_info['output']
            if out_file.exists():
                shutil.copy(out_file, output_file)
                results = self.parse_output(output_file)
                
                run_info = {
                    'timestamp': datetime.now().isoformat(),
                    'dryer_type': dryer_type,
                    'dryer_name': dryer_info['name'],
                    'parameters': params,
                    'output_file': str(output_file),
                    'results': results
                }
                self.results_db.append(run_info)
                
                return {
                    'success': True,
                    'data': results,
                    'run_id': len(self.results_db) - 1
                }
            else:
                return {'success': False, 'error': 'Output file not created'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def parse_output(self, filename):
        """Parse output file"""
        data = {
            'depth': [], 'time': [], 'air_temp': [], 'abs_hum': [],
            'rel_hum': [], 'prod_temp': [], 'mc_db': [], 'water': []
        }
        
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            data_start = False
            for line in lines:
                if 'DEPTH' in line and 'TIME' in line:
                    data_start = True
                    continue
                
                if data_start:
                    if line.strip() == '' or line.startswith('1') or line.startswith('0'):
                        continue
                    
                    try:
                        parts = line.split()
                        if len(parts) >= 8:
                            data['depth'].append(float(parts[0]))
                            data['time'].append(float(parts[1]))
                            data['air_temp'].append(float(parts[2]))
                            data['abs_hum'].append(float(parts[3]))
                            data['rel_hum'].append(float(parts[4]))
                            data['prod_temp'].append(float(parts[5]))
                            data['mc_db'].append(float(parts[6]))
                            data['water'].append(float(parts[7]))
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            print(f"Error parsing: {e}")
        
        return data
    
    def get_run_history(self):
        """Get simulation history"""
        history = []
        for i, run in enumerate(self.results_db):
            history.append({
                'id': i,
                'timestamp': run['timestamp'],
                'dryer_type': run['dryer_name'],
                'parameters': run['parameters']
            })
        return history

def register_routes(app):
    """Register all routes"""
    
    @app.route('/')
    def index():
        return render_template('dashboard.html', 
                             dryer_types=app.sim_manager.dryer_types)
    
    @app.route('/api/run_simulation', methods=['POST'])
    def run_simulation():
        data = request.json
        dryer_type = data.get('dryer_type')
        params = data.get('parameters')
        
        result = app.sim_manager.run_simulation(dryer_type, params)
        return jsonify(result)
    
    @app.route('/api/get_plot_data/<int:run_id>')
    def get_plot_data(run_id):
        if run_id < len(app.sim_manager.results_db):
            run = app.sim_manager.results_db[run_id]
            
            figures = {}
            
            # Moisture plot
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=run['results']['time'],
                y=[mc * 100 for mc in run['results']['mc_db']],
                mode='lines+markers',
                name='Moisture Content',
                line=dict(color='#1f77b4', width=3)
            ))
            fig1.update_layout(
                title='Moisture Content vs Time',
                xaxis_title='Time (hours)',
                yaxis_title='Moisture Content (% db)',
                template='plotly_white'
            )
            figures['moisture'] = json.loads(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder))
            
            # Temperature plot
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=run['results']['time'],
                y=run['results']['air_temp'],
                mode='lines+markers',
                name='Air Temperature'
            ))
            fig2.add_trace(go.Scatter(
                x=run['results']['time'],
                y=run['results']['prod_temp'],
                mode='lines+markers',
                name='Product Temperature'
            ))
            fig2.update_layout(
                title='Temperature vs Time',
                xaxis_title='Time (hours)',
                yaxis_title='Temperature (°F)',
                template='plotly_white'
            )
            figures['temperature'] = json.loads(json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder))
            
            # Humidity plot
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=run['results']['time'],
                y=run['results']['rel_hum'],
                mode='lines+markers',
                name='Relative Humidity'
            ))
            fig3.update_layout(
                title='Relative Humidity vs Time',
                xaxis_title='Time (hours)',
                yaxis_title='Relative Humidity',
                template='plotly_white'
            )
            figures['humidity'] = json.loads(json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder))
            
            return jsonify({
                'success': True,
                'figures': figures,
                'data': run['results']
            })
        else:
            return jsonify({'success': False, 'error': 'Run not found'})
    
    @app.route('/api/history')
    def get_history():
        return jsonify(app.sim_manager.get_run_history())
    
    @app.route('/api/export/<int:run_id>')
    def export_data(run_id):
        if run_id < len(app.sim_manager.results_db):
            run = app.sim_manager.results_db[run_id]
            df = pd.DataFrame(run['results'])
            
            csv_file = app.config['WORK_DIR'] / f"run_{run_id}.csv"
            df.to_csv(csv_file, index=False)
            
            return send_file(csv_file, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'Run not found'})

# Create application instance
application = create_app()

# For local testing



# For local testing
if __name__ == '__main__':

# For local testing
if __name__ == '__main__':
    print("=" * 70)
    print("  GRAIN DRYER DASHBOARD - PythonAnywhere Version")
    print("=" * 70)
    print("\nStarting local test server...")
    print("Open browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    application.run(debug=True, host='0.0.0.0', port=5000)
