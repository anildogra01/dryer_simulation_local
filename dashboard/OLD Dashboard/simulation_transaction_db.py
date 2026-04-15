"""
Simulation Transaction Database
Stores all simulation runs with inputs and results
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class SimulationTransactionDB:
    """Lightweight transaction database for simulation history"""
    
    def __init__(self, db_path=None):
        """Initialize transaction database
        
        Args:
            db_path: Path to database file. If None, uses database/simulation_transactions.db
        """
        if db_path is None:
            db_path = Path(__file__).parent / 'database' / 'simulation_transactions.db'
            # Create database folder if it doesn't exist
            db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = str(db_path)
        self.init_database()
    
    def init_database(self):
        """Create transactions table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_runs (
                sim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                
                -- User Information
                user_name TEXT,
                project_name TEXT,
                address TEXT,
                
                -- Simulation Setup
                crop_id INTEGER NOT NULL,
                crop_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                
                -- Process Parameters (User Inputs)
                initial_moisture REAL NOT NULL,
                target_moisture REAL NOT NULL,
                grain_temp_f REAL NOT NULL,
                air_temp_f REAL NOT NULL,
                air_rh REAL NOT NULL,
                air_flow_cfm REAL NOT NULL,
                grain_flow_rate REAL,
                width_m REAL,
                length_m REAL,
                
                -- Execution Info
                execution_time_sec REAL,
                status TEXT,  -- 'success', 'failed', 'timeout'
                error_message TEXT,
                
                -- Results Summary (for quick display)
                final_moisture REAL,
                drying_time_hours REAL,
                energy_used REAL,
                
                -- Full Results (JSON)
                results_json TEXT,
                
                -- File Paths
                output_directory TEXT,
                pdf_report_path TEXT
            )
        ''')
        
        # Index for fast queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON simulation_runs(run_timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user 
            ON simulation_runs(user_name, run_timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_crop 
            ON simulation_runs(crop_name, run_timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Transaction database initialized: {self.db_path}")
    
    def save_simulation(self, sim_data):
        """
        Save simulation run to transaction database
        
        Args:
            sim_data: Dict with all simulation parameters and results
        
        Returns:
            sim_id: ID of saved record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO simulation_runs (
                run_timestamp, user_name, project_name, address,
                crop_id, crop_name, model_type,
                initial_moisture, target_moisture,
                grain_temp_f, air_temp_f, air_rh, air_flow_cfm,
                grain_flow_rate, width_m, length_m,
                execution_time_sec, status, error_message,
                final_moisture, drying_time_hours, energy_used,
                results_json, output_directory, pdf_report_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sim_data.get('run_timestamp', datetime.now().isoformat()),
            sim_data.get('user_name'),
            sim_data.get('project_name'),
            sim_data.get('address'),
            sim_data.get('crop_id'),
            sim_data.get('crop_name'),
            sim_data.get('model_type'),
            sim_data.get('initial_moisture'),
            sim_data.get('target_moisture'),
            sim_data.get('grain_temp_f'),
            sim_data.get('air_temp_f'),
            sim_data.get('air_rh'),
            sim_data.get('air_flow_cfm'),
            sim_data.get('grain_flow_rate'),
            sim_data.get('width_m'),
            sim_data.get('length_m'),
            sim_data.get('execution_time_sec'),
            sim_data.get('status', 'success'),
            sim_data.get('error_message'),
            sim_data.get('final_moisture'),
            sim_data.get('drying_time_hours'),
            sim_data.get('energy_used'),
            json.dumps(sim_data.get('results', {})),
            sim_data.get('output_directory'),
            sim_data.get('pdf_report_path')
        ))
        
        sim_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return sim_id
    
    def get_recent_simulations(self, limit=50):
        """Get recent simulations for history page"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                sim_id, run_timestamp, user_name, project_name,
                crop_name, model_type,
                initial_moisture, target_moisture, final_moisture,
                drying_time_hours, status,
                pdf_report_path
            FROM simulation_runs
            ORDER BY run_timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_simulation_by_id(self, sim_id):
        """Get full simulation details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM simulation_runs WHERE sim_id = ?
        ''', (sim_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            sim = dict(row)
            # Parse JSON results
            if sim['results_json']:
                sim['results'] = json.loads(sim['results_json'])
            return sim
        return None
    
    def get_user_statistics(self, user_name):
        """Get statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                AVG(drying_time_hours) as avg_time,
                AVG(energy_used) as avg_energy,
                MIN(run_timestamp) as first_run,
                MAX(run_timestamp) as last_run
            FROM simulation_runs
            WHERE user_name = ? AND status = 'success'
        ''', (user_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_runs': row[0] or 0,
            'avg_time': row[1],
            'avg_energy': row[2],
            'first_run': row[3],
            'last_run': row[4]
        }
    
    def get_crop_statistics(self, crop_name):
        """Get statistics for a crop"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                AVG(drying_time_hours) as avg_time,
                MIN(drying_time_hours) as min_time,
                MAX(drying_time_hours) as max_time
            FROM simulation_runs
            WHERE crop_name = ? AND status = 'success'
        ''', (crop_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_runs': row[0] or 0,
            'avg_time': row[1],
            'min_time': row[2],
            'max_time': row[3]
        }
    
    def search_simulations(self, filters):
        """
        Search simulations with filters
        
        Args:
            filters: Dict with optional keys: user_name, crop_name, model_type, 
                    date_from, date_to, status
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM simulation_runs WHERE 1=1'
        params = []
        
        if filters.get('user_name'):
            query += ' AND user_name = ?'
            params.append(filters['user_name'])
        
        if filters.get('crop_name'):
            query += ' AND crop_name = ?'
            params.append(filters['crop_name'])
        
        if filters.get('model_type'):
            query += ' AND model_type = ?'
            params.append(filters['model_type'])
        
        if filters.get('date_from'):
            query += ' AND run_timestamp >= ?'
            params.append(filters['date_from'])
        
        if filters.get('date_to'):
            query += ' AND run_timestamp <= ?'
            params.append(filters['date_to'])
        
        if filters.get('status'):
            query += ' AND status = ?'
            params.append(filters['status'])
        
        query += ' ORDER BY run_timestamp DESC LIMIT 100'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


if __name__ == '__main__':
    # Test
    db = SimulationTransactionDB()
    print("✅ Transaction database ready")
    
    # Test save
    test_data = {
        'user_name': 'Test User',
        'project_name': 'Test Project',
        'crop_id': 1,
        'crop_name': 'Corn',
        'model_type': 'fixed_bed',
        'initial_moisture': 25.0,
        'target_moisture': 14.0,
        'grain_temp_f': 70.0,
        'air_temp_f': 110.0,
        'air_rh': 30.0,
        'air_flow_cfm': 500.0,
        'execution_time_sec': 45.2,
        'final_moisture': 14.1,
        'drying_time_hours': 8.5
    }
    
    sim_id = db.save_simulation(test_data)
    print(f"✅ Test simulation saved with ID: {sim_id}")
    
    # Test retrieve
    recent = db.get_recent_simulations(5)
    print(f"✅ Found {len(recent)} recent simulations")
