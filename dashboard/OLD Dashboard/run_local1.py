"""
Dryer Dashboard - Local Development Version
Simple wrapper to run locally with your existing files
"""

from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
import sys
import os

# Get the directory where this file is located
BASE_DIR = Path(__file__).parent.absolute()

# Add to Python path
sys.path.insert(0, str(BASE_DIR))

# Import your existing files
from crop_master_database import CropMasterDB
import sqlite3

# Initialize Flask app
app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))

app.config['SECRET_KEY'] = 'local-dev-secret-key'

# Initialize database with LOCAL path
crop_db = CropMasterDB(db_path=str(BASE_DIR / 'crop_master.db'))

print(f"✅ Database initialized at: {BASE_DIR / 'crop_master.db'}")

# ============================================================
# MAIN ROUTES
# ============================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/crop-master')
def crop_master_ui():
    """Crop master management interface"""
    return render_template('crop_master_ui.html')

@app.route('/history')
def history_page():
    """Simulation history page"""
    return render_template('simulation_history.html')

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
        print(f"❌ Error in get_all_crops_api: {e}")
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
        print(f"❌ Error in get_crop_api: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crops', methods=['POST'])
def add_crop_api():
    """Add new crop"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'crop_name', 'crop_type', 'specific_surface_area',
            'heat_capacity_air', 'heat_capacity_dry_product',
            'heat_capacity_water_vapor', 'dry_bulk_density',
            'latent_heat_water', 'atmospheric_pressure'
        ]
        
        for field in required_fields:
            if field not in data or data[field] == '':
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Convert numeric fields
        numeric_fields = [
            'specific_surface_area', 'heat_capacity_air',
            'heat_capacity_dry_product', 'heat_capacity_water_vapor',
            'dry_bulk_density', 'latent_heat_water',
            'atmospheric_pressure', 'max_safe_temp',
            'min_safe_temp', 'optimal_drying_temp'
        ]
        
        for field in numeric_fields:
            if field in data and data[field] != '':
                try:
                    data[field] = float(data[field])
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid numeric value for {field}'
                    }), 400
        
        crop_id = crop_db.add_crop(data)
        
        if crop_id:
            return jsonify({
                'success': True,
                'crop_id': crop_id,
                'message': f'Crop "{data["crop_name"]}" added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Crop "{data["crop_name"]}" already exists'
            }), 409
            
    except Exception as e:
        print(f"❌ Error in add_crop_api: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crops/<int:crop_id>', methods=['PUT'])
def update_crop_api(crop_id):
    """Update existing crop"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(crop_db.db_path)
        cursor = conn.cursor()
        
        # Check if crop exists
        cursor.execute('SELECT crop_name FROM crops WHERE crop_id = ?', (crop_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Crop not found'}), 404
        
        # Build update query
        update_fields = []
        update_values = []
        
        allowed_fields = [
            'crop_name', 'crop_type', 'specific_surface_area',
            'heat_capacity_air', 'heat_capacity_dry_product',
            'heat_capacity_water_vapor', 'dry_bulk_density',
            'latent_heat_water', 'atmospheric_pressure',
            'max_safe_temp', 'min_safe_temp', 'optimal_drying_temp', 'notes'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                update_values.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        query = f"UPDATE crops SET {', '.join(update_fields)} WHERE crop_id = ?"
        update_values.append(crop_id)
        
        cursor.execute(query, update_values)
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Crop updated successfully'})
        
    except Exception as e:
        print(f"❌ Error in update_crop_api: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crops/<int:crop_id>', methods=['DELETE'])
def delete_crop_api(crop_id):
    """Delete crop"""
    try:
        conn = sqlite3.connect(crop_db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT crop_name FROM crops WHERE crop_id = ?', (crop_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Crop not found'}), 404
        
        crop_name = row[0]
        
        # Check if used in simulations
        cursor.execute('SELECT COUNT(*) FROM simulation_history WHERE crop_id = ?', (crop_id,))
        sim_count = cursor.fetchone()[0]
        
        if sim_count > 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete. Used in {sim_count} simulation(s).'
            }), 409
        
        cursor.execute('DELETE FROM crops WHERE crop_id = ?', (crop_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Crop "{crop_name}" deleted successfully'
        })
        
    except Exception as e:
        print(f"❌ Error in delete_crop_api: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# SIMULATION API (Placeholder for now)
# ============================================================

@app.route('/api/simulate', methods=['POST'])
def run_simulation_api():
    """Run simulation - placeholder until Fortran is ready"""
    try:
        data = request.get_json()
        
        return jsonify({
            'success': False,
            'error': 'Fortran executables not configured yet. UI testing only.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulation-history')
def get_simulation_history():
    """Get simulation history"""
    try:
        conn = sqlite3.connect(crop_db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.simulation_id,
                s.user_name,
                s.project_name,
                s.model_type,
                c.crop_name,
                s.initial_moisture,
                s.target_moisture,
                s.run_date
            FROM simulation_history s
            JOIN crops c ON s.crop_id = c.crop_id
            ORDER BY s.run_date DESC
            LIMIT 50
        ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'simulation_id': row[0],
                'user_name': row[1],
                'project_name': row[2],
                'model_type': row[3],
                'crop_name': row[4],
                'initial_moisture': row[5],
                'target_moisture': row[6],
                'run_date': row[7],
                'has_results': True
            })
        
        conn.close()
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        print(f"❌ Error in get_simulation_history: {e}")
        return jsonify({'success': True, 'history': []})  # Return empty list if no history

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  🌾 GRAIN DRYER DASHBOARD - Local Development")
    print("=" * 70)
    print()
    print("📂 Working Directory:", BASE_DIR)
    print("💾 Database:", BASE_DIR / 'crop_master.db')
    print()
    print("🌐 Starting development server...")
    print("📍 Open browser to: http://localhost:5000")
    print()
    print("📋 Available routes:")
    print("   - Main Dashboard:    http://localhost:5000/")
    print("   - Crop Master:       http://localhost:5000/crop-master")
    print("   - History:           http://localhost:5000/history")
    print("   - API Crops:         http://localhost:5000/api/crops")
    print()
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5000)
