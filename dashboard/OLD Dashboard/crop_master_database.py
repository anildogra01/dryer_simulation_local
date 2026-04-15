# Crop Master Database for Dryer Simulation
# Stores crop-specific thermodynamic and physical properties

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class CropMasterDB:
    """Manage crop parameters database for grain dryer simulations"""
    
    def __init__(self, db_path=None):
        """Initialize crop master database
        
        Args:
            db_path: Path to database file. If None, uses database/crop_master.db
        """
        if db_path is None:
            # Use database folder relative to this file
            from pathlib import Path
            db_path = Path(__file__).parent / 'database' / 'crop_master.db'
            # Create database folder if it doesn't exist
            db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = str(db_path)
        self.init_database()
        
    def init_database(self):
        """Initialize database with crop master table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create crops table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crops (
                crop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_name TEXT UNIQUE NOT NULL,
                crop_type TEXT NOT NULL,
                specific_surface_area REAL NOT NULL,
                heat_capacity_air REAL NOT NULL,
                heat_capacity_dry_product REAL NOT NULL,
                heat_capacity_water_vapor REAL NOT NULL,
                dry_bulk_density REAL NOT NULL,
                latent_heat_water REAL NOT NULL,
                atmospheric_pressure REAL NOT NULL,
                max_safe_temp REAL,
                min_safe_temp REAL,
                optimal_drying_temp REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create simulation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_history (
                simulation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                project_name TEXT,
                address TEXT,
                crop_id INTEGER,
                model_type TEXT NOT NULL,
                initial_moisture REAL NOT NULL,
                target_moisture REAL NOT NULL,
                grain_temp REAL NOT NULL,
                air_temp REAL NOT NULL,
                air_rh REAL NOT NULL,
                air_flow_rate REAL NOT NULL,
                grain_flow_rate REAL,
                width REAL,
                length REAL,
                results_json TEXT,
                run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (crop_id) REFERENCES crops(crop_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Add default crops if database is empty
        self._add_default_crops_if_empty()
        
        print("✅ Database initialized")
    
    def _add_default_crops_if_empty(self):
        """Add default crops if database is empty"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if crops table is empty
        cursor.execute('SELECT COUNT(*) FROM crops')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📊 Adding default crops to database...")
            
            # Default crops with standard properties
            default_crops = [
                {
                    'crop_name': 'Corn',
                    'crop_type': 'Grain',
                    'specific_surface_area': 290.0,
                    'heat_capacity_air': 1005.0,
                    'heat_capacity_dry_product': 1465.0,
                    'heat_capacity_water_vapor': 1884.0,
                    'dry_bulk_density': 721.0,
                    'latent_heat_water': 2500000.0,
                    'atmospheric_pressure': 101325.0
                },
                {
                    'crop_name': 'Wheat',
                    'crop_type': 'Grain',
                    'specific_surface_area': 250.0,
                    'heat_capacity_air': 1005.0,
                    'heat_capacity_dry_product': 1500.0,
                    'heat_capacity_water_vapor': 1884.0,
                    'dry_bulk_density': 780.0,
                    'latent_heat_water': 2500000.0,
                    'atmospheric_pressure': 101325.0
                },
                {
                    'crop_name': 'Rice',
                    'crop_type': 'Grain',
                    'specific_surface_area': 220.0,
                    'heat_capacity_air': 1005.0,
                    'heat_capacity_dry_product': 1420.0,
                    'heat_capacity_water_vapor': 1884.0,
                    'dry_bulk_density': 580.0,
                    'latent_heat_water': 2500000.0,
                    'atmospheric_pressure': 101325.0
                },
                {
                    'crop_name': 'Soybeans',
                    'crop_type': 'Grain',
                    'specific_surface_area': 200.0,
                    'heat_capacity_air': 1005.0,
                    'heat_capacity_dry_product': 1680.0,
                    'heat_capacity_water_vapor': 1884.0,
                    'dry_bulk_density': 753.0,
                    'latent_heat_water': 2500000.0,
                    'atmospheric_pressure': 101325.0
                },
                {
                    'crop_name': 'Barley',
                    'crop_type': 'Grain',
                    'specific_surface_area': 260.0,
                    'heat_capacity_air': 1005.0,
                    'heat_capacity_dry_product': 1520.0,
                    'heat_capacity_water_vapor': 1884.0,
                    'dry_bulk_density': 610.0,
                    'latent_heat_water': 2500000.0,
                    'atmospheric_pressure': 101325.0
                }
            ]
            
            for crop in default_crops:
                cursor.execute('''
                    INSERT INTO crops (
                        crop_name, crop_type, specific_surface_area, heat_capacity_air,
                        heat_capacity_dry_product, heat_capacity_water_vapor,
                        dry_bulk_density, latent_heat_water, atmospheric_pressure
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    crop['crop_name'],
                    crop['crop_type'],
                    crop['specific_surface_area'],
                    crop['heat_capacity_air'],
                    crop['heat_capacity_dry_product'],
                    crop['heat_capacity_water_vapor'],
                    crop['dry_bulk_density'],
                    crop['latent_heat_water'],
                    crop['atmospheric_pressure']
                ))
            
            conn.commit()
            print(f"   ✅ Added {len(default_crops)} default crops")
        
        conn.close()
        
    def add_crop(self, crop_data):
        """Add a new crop to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO crops (
                    crop_name, crop_type, specific_surface_area,
                    heat_capacity_air, heat_capacity_dry_product,
                    heat_capacity_water_vapor, dry_bulk_density,
                    latent_heat_water, atmospheric_pressure,
                    max_safe_temp, min_safe_temp, optimal_drying_temp, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                crop_data['crop_name'],
                crop_data['crop_type'],
                crop_data['specific_surface_area'],
                crop_data['heat_capacity_air'],
                crop_data['heat_capacity_dry_product'],
                crop_data['heat_capacity_water_vapor'],
                crop_data['dry_bulk_density'],
                crop_data['latent_heat_water'],
                crop_data['atmospheric_pressure'],
                crop_data.get('max_safe_temp'),
                crop_data.get('min_safe_temp'),
                crop_data.get('optimal_drying_temp'),
                crop_data.get('notes', '')
            ))
            conn.commit()
            print(f"✅ Added crop: {crop_data['crop_name']}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"⚠️  Crop {crop_data['crop_name']} already exists")
            return None
        finally:
            conn.close()
    
    def get_crop(self, crop_name):
        """Retrieve crop parameters by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM crops WHERE crop_name = ?', (crop_name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'crop_id': row[0],
                'crop_name': row[1],
                'crop_type': row[2],
                'specific_surface_area': row[3],
                'heat_capacity_air': row[4],
                'heat_capacity_dry_product': row[5],
                'heat_capacity_water_vapor': row[6],
                'dry_bulk_density': row[7],
                'latent_heat_water': row[8],
                'atmospheric_pressure': row[9],
                'max_safe_temp': row[10],
                'min_safe_temp': row[11],
                'optimal_drying_temp': row[12],
                'notes': row[13]
            }
        return None
    
    def get_all_crops(self):
        """Get list of all crops"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT crop_id, crop_name, crop_type FROM crops ORDER BY crop_name')
        crops = [{'crop_id': row[0], 'crop_name': row[1], 'crop_type': row[2]} 
                 for row in cursor.fetchall()]
        
        conn.close()
        return crops
    
    def save_simulation(self, sim_data):
        """Save simulation run to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO simulation_history (
                user_name, project_name, address, crop_id, model_type,
                initial_moisture, target_moisture, grain_temp, air_temp,
                air_rh, air_flow_rate, grain_flow_rate, width, length,
                results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sim_data['user_name'],
            sim_data['project_name'],
            sim_data['address'],
            sim_data['crop_id'],
            sim_data['model_type'],
            sim_data['initial_moisture'],
            sim_data['target_moisture'],
            sim_data['grain_temp'],
            sim_data['air_temp'],
            sim_data['air_rh'],
            sim_data['air_flow_rate'],
            sim_data.get('grain_flow_rate'),
            sim_data.get('width'),
            sim_data.get('length'),
            json.dumps(sim_data.get('results', {}))
        ))
        
        conn.commit()
        sim_id = cursor.lastrowid
        conn.close()
        return sim_id


# ============================================================
# INITIAL CROP DATA
# ============================================================

INITIAL_CROPS = [
    {
        'crop_name': 'Corn',
        'crop_type': 'Grain',
        'specific_surface_area': 290.0,  # m²/m³
        'heat_capacity_air': 1005.0,  # J/(kg·K)
        'heat_capacity_dry_product': 1465.0,  # J/(kg·K)
        'heat_capacity_water_vapor': 1884.0,  # J/(kg·K)
        'dry_bulk_density': 721.0,  # kg/m³
        'latent_heat_water': 2.5e6,  # J/kg
        'atmospheric_pressure': 101325.0,  # Pa
        'max_safe_temp': 60.0,  # °C
        'min_safe_temp': 20.0,  # °C
        'optimal_drying_temp': 45.0,  # °C
        'notes': 'Yellow dent corn, standard commercial variety'
    },
    {
        'crop_name': 'Wheat',
        'crop_type': 'Grain',
        'specific_surface_area': 350.0,
        'heat_capacity_air': 1005.0,
        'heat_capacity_dry_product': 1420.0,
        'heat_capacity_water_vapor': 1884.0,
        'dry_bulk_density': 780.0,
        'latent_heat_water': 2.5e6,
        'atmospheric_pressure': 101325.0,
        'max_safe_temp': 55.0,
        'min_safe_temp': 20.0,
        'optimal_drying_temp': 40.0,
        'notes': 'Hard red spring wheat'
    },
    {
        'crop_name': 'Rice (Paddy)',
        'crop_type': 'Grain',
        'specific_surface_area': 400.0,
        'heat_capacity_air': 1005.0,
        'heat_capacity_dry_product': 1675.0,
        'heat_capacity_water_vapor': 1884.0,
        'dry_bulk_density': 580.0,
        'latent_heat_water': 2.5e6,
        'atmospheric_pressure': 101325.0,
        'max_safe_temp': 45.0,
        'min_safe_temp': 20.0,
        'optimal_drying_temp': 38.0,
        'notes': 'Rough rice with husk, requires gentle drying'
    },
    {
        'crop_name': 'Soybeans',
        'crop_type': 'Oilseed',
        'specific_surface_area': 320.0,
        'heat_capacity_air': 1005.0,
        'heat_capacity_dry_product': 1820.0,
        'heat_capacity_water_vapor': 1884.0,
        'dry_bulk_density': 750.0,
        'latent_heat_water': 2.5e6,
        'atmospheric_pressure': 101325.0,
        'max_safe_temp': 50.0,
        'min_safe_temp': 20.0,
        'optimal_drying_temp': 38.0,
        'notes': 'Sensitive to high temperatures, can crack'
    },
    {
        'crop_name': 'Barley',
        'crop_type': 'Grain',
        'specific_surface_area': 330.0,
        'heat_capacity_air': 1005.0,
        'heat_capacity_dry_product': 1450.0,
        'heat_capacity_water_vapor': 1884.0,
        'dry_bulk_density': 620.0,
        'latent_heat_water': 2.5e6,
        'atmospheric_pressure': 101325.0,
        'max_safe_temp': 50.0,
        'min_safe_temp': 20.0,
        'optimal_drying_temp': 40.0,
        'notes': 'Malting barley - quality sensitive to drying conditions'
    }
]


def initialize_crop_database():
    """Initialize database with default crops"""
    db = CropMasterDB()
    
    print("\n📊 Initializing Crop Master Database")
    print("=" * 50)
    
    for crop_data in INITIAL_CROPS:
        db.add_crop(crop_data)
    
    print("\n✅ Crop database initialized with", len(INITIAL_CROPS), "crops")
    print("\nAvailable crops:")
    for crop in db.get_all_crops():
        print(f"  - {crop['crop_name']} ({crop['crop_type']})")
    
    return db


if __name__ == '__main__':
    # Initialize database with default crops
    db = initialize_crop_database()
    
    # Example: Get corn parameters
    print("\n" + "=" * 50)
    print("Example: Corn Parameters")
    print("=" * 50)
    corn = db.get_crop('Corn')
    if corn:
        for key, value in corn.items():
            if key not in ['crop_id', 'notes']:
                print(f"{key:30s}: {value}")
