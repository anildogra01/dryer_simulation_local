"""
Simulation Transaction Database Module
Stores and manages simulation runs and results
"""

import sqlite3
import json
from datetime import datetime
import os

class SimulationTransactionDB:
    """Database for storing simulation transactions"""
    
    def __init__(self, db_path='database/simulations.db'):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simulations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                crop_name TEXT NOT NULL,
                drying_method TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                air_velocity REAL NOT NULL,
                initial_moisture REAL NOT NULL,
                final_moisture REAL NOT NULL,
                drying_time REAL NOT NULL,
                energy_consumption REAL NOT NULL,
                efficiency REAL,
                parameters TEXT,
                results TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_simulation(self, simulation_data):
        """
        Add a new simulation to database
        
        Args:
            simulation_data: dict with simulation parameters and results
        
        Returns:
            int: ID of inserted simulation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO simulations (
                timestamp, crop_name, drying_method, temperature, humidity,
                air_velocity, initial_moisture, final_moisture, drying_time,
                energy_consumption, efficiency, parameters, results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            simulation_data.get('crop_name', ''),
            simulation_data.get('drying_method', ''),
            simulation_data.get('temperature', 0),
            simulation_data.get('humidity', 0),
            simulation_data.get('air_velocity', 0),
            simulation_data.get('initial_moisture', 0),
            simulation_data.get('final_moisture', 0),
            simulation_data.get('drying_time', 0),
            simulation_data.get('energy_consumption', 0),
            simulation_data.get('efficiency', 0),
            json.dumps(simulation_data.get('parameters', {})),
            json.dumps(simulation_data.get('results', {}))
        ))
        
        sim_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return sim_id
    
    def get_simulation(self, sim_id):
        """Get simulation by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulations WHERE id = ?', (sim_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_simulations(self, limit=100):
        """Get all simulations"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM simulations ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_simulations_by_crop(self, crop_name, limit=50):
        """Get simulations for specific crop"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM simulations WHERE crop_name = ? ORDER BY timestamp DESC LIMIT ?',
            (crop_name, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total simulations
        cursor.execute('SELECT COUNT(*) FROM simulations')
        total = cursor.fetchone()[0]
        
        # By crop
        cursor.execute('''
            SELECT crop_name, COUNT(*) as count 
            FROM simulations 
            GROUP BY crop_name 
            ORDER BY count DESC
        ''')
        by_crop = dict(cursor.fetchall())
        
        # By method
        cursor.execute('''
            SELECT drying_method, COUNT(*) as count 
            FROM simulations 
            GROUP BY drying_method 
            ORDER BY count DESC
        ''')
        by_method = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_simulations': total,
            'by_crop': by_crop,
            'by_method': by_method
        }

# Create global instance
simulation_db = SimulationTransactionDB()