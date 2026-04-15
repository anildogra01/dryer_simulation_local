"""
Fortran Dryer Simulation Interface
Bridges database crop parameters with Fortran simulation programs
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime
from crop_master_database import CropMasterDB

class FortranDryerInterface:
    """Interface between database and Fortran dryer simulations"""
    
    def __init__(self, base_dir='/home/akdsmartgrow/dryer_simulation'):
        self.base_dir = Path(base_dir)
        self.crop_db = CropMasterDB()
        
        # Model directories
        self.models = {
            'fixed_bed': self.base_dir / 'fixed_bed',
            'crossflow': self.base_dir / 'crossflow',
            'counterflow': self.base_dir / 'counterflow',
            'concurrent': self.base_dir / 'concurrent'
        }
        
        # Simulation output directory
        self.output_dir = self.base_dir / 'simulation_runs'
        self.output_dir.mkdir(exist_ok=True)
    
    def create_input_file(self, model_type, crop_name, process_params, user_info, input_filename='input.dat'):
        """
        Create input.dat file for Fortran program
        
        Args:
            model_type: 'fixed_bed', 'crossflow', 'counterflow', or 'concurrent'
            crop_name: Name of crop from database
            process_params: Dict with process parameters
            user_info: Dict with user_name, project_name, address
            input_filename: Name of input file to create
        
        Returns:
            Path to created input file
        """
        # Get crop parameters from database
        crop = self.crop_db.get_crop(crop_name)
        if not crop:
            raise ValueError(f"Crop '{crop_name}' not found in database")
        
        # Get model directory
        model_dir = self.models.get(model_type)
        if not model_dir:
            raise ValueError(f"Unknown model type: {model_type}")
        
        input_path = model_dir / input_filename
        
        # Write input file
        with open(input_path, 'w') as f:
            # Header with user credentials
            f.write("!" + "="*70 + "\n")
            f.write("! GRAIN DRYER SIMULATION INPUT FILE\n")
            f.write("!" + "="*70 + "\n")
            f.write(f"! Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"! User: {user_info.get('user_name', 'N/A')}\n")
            f.write(f"! Project: {user_info.get('project_name', 'N/A')}\n")
            f.write(f"! Address: {user_info.get('address', 'N/A')}\n")
            f.write("!" + "-"*70 + "\n")
            f.write(f"! Model Type: {model_type.upper()}\n")
            f.write(f"! Crop: {crop_name} ({crop['crop_type']})\n")
            f.write("!" + "="*70 + "\n")
            f.write("!\n")
            
            # Crop-specific parameters (from database)
            f.write("! === CROP PARAMETERS (from database) ===\n")
            f.write(f"{crop['specific_surface_area']:<15.4f}  ! sa - Specific surface area (m2/m3)\n")
            f.write(f"{crop['heat_capacity_air']:<15.4f}  ! ca - Heat capacity of air (J/kg.K)\n")
            f.write(f"{crop['heat_capacity_dry_product']:<15.4f}  ! cp - Heat capacity of dry product (J/kg.K)\n")
            f.write(f"{crop['heat_capacity_water_vapor']:<15.4f}  ! cv - Heat capacity of water vapor (J/kg.K)\n")
            f.write(f"{crop['dry_bulk_density']:<15.4f}  ! rhop - Dry bulk density (kg/m3)\n")
            f.write(f"{crop['latent_heat_water']:<15.4e}  ! hfg - Latent heat of water (J/kg)\n")
            f.write(f"{crop['atmospheric_pressure']:<15.4f}  ! patm - Atmospheric pressure (Pa)\n")
            f.write("!\n")
            
            # Process parameters (from web form)
            f.write("! === PROCESS PARAMETERS (from user input) ===\n")
            f.write(f"{process_params['initial_moisture']:<15.4f}  ! Mi - Initial moisture content (%)\n")
            f.write(f"{process_params['target_moisture']:<15.4f}  ! Mf - Target moisture content (%)\n")
            
            # Convert Fahrenheit to Celsius
            grain_temp_c = (process_params['grain_temp'] - 32) * 5/9
            air_temp_c = (process_params['air_temp'] - 32) * 5/9
            
            f.write(f"{grain_temp_c:<15.4f}  ! Tg - Initial grain temperature (C)\n")
            f.write(f"{air_temp_c:<15.4f}  ! Ta - Air temperature (C)\n")
            f.write(f"{process_params['air_rh']:<15.4f}  ! RH - Relative humidity (%)\n")
            
            # Convert CFM to m3/s (1 CFM = 0.000471947 m3/s)
            air_flow_m3s = process_params['air_flow_rate'] * 0.000471947
            f.write(f"{air_flow_m3s:<15.4e}  ! Q - Air flow rate (m3/s)\n")
            
            # Model-specific parameters
            if model_type in ['crossflow', 'counterflow', 'concurrent']:
                f.write(f"{process_params['grain_flow_rate']:<15.4f}  ! Fg - Grain flow rate (kg/hr)\n")
            
            if model_type in ['fixed_bed', 'crossflow']:
                f.write(f"{process_params['width']:<15.4f}  ! W - Width (m)\n")
                f.write(f"{process_params['length']:<15.4f}  ! L - Length (m)\n")
        
        return input_path
    
    def run_simulation(self, model_type, crop_name, process_params, user_info):
        """
        Run Fortran simulation
        
        Args:
            model_type: 'fixed_bed', 'crossflow', 'counterflow', or 'concurrent'
            crop_name: Name of crop
            process_params: Dict with process parameters
            user_info: Dict with user_name, project_name, address
        
        Returns:
            Dict with simulation results
        """
        # Create input file
        input_file = self.create_input_file(model_type, crop_name, process_params, user_info)
        
        # Get model directory and executable
        model_dir = self.models[model_type]
        executable = model_dir / 'dryer'  # Adjust if executable has different name
        
        if not executable.exists():
            raise FileNotFoundError(f"Executable not found: {executable}")
        
        # Create unique output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = self.output_dir / f"{model_type}_{crop_name}_{timestamp}"
        run_dir.mkdir(exist_ok=True)
        
        # Run Fortran program
        try:
            result = subprocess.run(
                [str(executable)],
                cwd=model_dir,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Simulation failed: {result.stderr}")
            
            # Parse output files
            output_data = self.parse_output(model_dir, model_type)
            
            # Copy output files to run directory
            self.save_outputs(model_dir, run_dir)
            
            # Create summary report with user credentials
            self.create_report(run_dir, model_type, crop_name, user_info, process_params, output_data)
            
            # Add metadata
            output_data['model_type'] = model_type
            output_data['crop_name'] = crop_name
            output_data['timestamp'] = timestamp
            output_data['run_directory'] = str(run_dir)
            output_data['user_info'] = user_info
            
            return {
                'success': True,
                'results': output_data,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Simulation timeout (exceeded 60 seconds)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_output(self, model_dir, model_type):
        """
        Parse Fortran output files
        
        Args:
            model_dir: Directory containing output files
            model_type: Type of model
        
        Returns:
            Dict with parsed results
        """
        results = {}
        
        # Common output files
        output_files = {
            'moisture_profile.dat': 'moisture_vs_time',
            'temperature_profile.dat': 'temperature_vs_time',
            'summary.dat': 'summary'
        }
        
        for filename, key in output_files.items():
            filepath = model_dir / filename
            if filepath.exists():
                results[key] = self.read_output_file(filepath)
        
        return results
    
    def read_output_file(self, filepath):
        """Read output data file"""
        data = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('!') and not line.startswith('#'):
                    values = [float(x) for x in line.split()]
                    data.append(values)
        return data
    
    def save_outputs(self, source_dir, dest_dir):
        """Copy output files to simulation run directory"""
        import shutil
        
        output_patterns = ['*.dat', '*.txt', '*.out']
        
        for pattern in output_patterns:
            for filepath in source_dir.glob(pattern):
                if filepath.is_file():
                    shutil.copy2(filepath, dest_dir)
    
    def create_report(self, run_dir, model_type, crop_name, user_info, process_params, results):
        """
        Create a summary report file with user credentials and results
        
        Args:
            run_dir: Directory to save report
            model_type: Type of dryer model
            crop_name: Name of crop
            user_info: Dict with user credentials
            process_params: Dict with process parameters
            results: Dict with simulation results
        """
        report_path = run_dir / 'SIMULATION_REPORT.txt'
        
        with open(report_path, 'w') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GRAIN DRYER SIMULATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # User Information
            f.write("USER INFORMATION:\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Name:          {user_info.get('user_name', 'N/A')}\n")
            f.write(f"  Project:       {user_info.get('project_name', 'N/A')}\n")
            f.write(f"  Address:       {user_info.get('address', 'N/A')}\n")
            f.write(f"  Date:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Simulation Details
            f.write("SIMULATION DETAILS:\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Model Type:    {model_type.upper()}\n")
            f.write(f"  Crop:          {crop_name}\n\n")
            
            # Process Parameters
            f.write("PROCESS PARAMETERS:\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Initial Moisture:     {process_params['initial_moisture']:.2f} %\n")
            f.write(f"  Target Moisture:      {process_params['target_moisture']:.2f} %\n")
            f.write(f"  Grain Temperature:    {process_params['grain_temp']:.2f} °F\n")
            f.write(f"  Air Temperature:      {process_params['air_temp']:.2f} °F\n")
            f.write(f"  Air RH:               {process_params['air_rh']:.2f} %\n")
            f.write(f"  Air Flow Rate:        {process_params['air_flow_rate']:.2f} CFM\n")
            
            if 'grain_flow_rate' in process_params:
                f.write(f"  Grain Flow Rate:      {process_params['grain_flow_rate']:.2f} kg/hr\n")
            if 'width' in process_params and 'length' in process_params:
                f.write(f"  Dimensions:           {process_params['width']:.2f} m × {process_params['length']:.2f} m\n")
            
            f.write("\n")
            
            # Results
            if results:
                f.write("SIMULATION RESULTS:\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Output files saved in: {run_dir}\n")
                f.write(f"  Available data files:\n")
                for key in results.keys():
                    if key not in ['model_type', 'crop_name', 'timestamp', 'run_directory']:
                        f.write(f"    - {key}\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        return report_path


# ============================================================
# USAGE EXAMPLE
# ============================================================

def example_usage():
    """Example of how to use the interface"""
    
    interface = FortranDryerInterface()
    
    # User credentials
    user_info = {
        'user_name': 'John Doe',
        'project_name': 'Farm Dryer 2026',
        'address': '123 Farm Road, Henrietta, NY'
    }
    
    # Process parameters from web form
    process_params = {
        'initial_moisture': 25.0,      # %
        'target_moisture': 14.0,       # %
        'grain_temp': 70.0,            # F
        'air_temp': 110.0,             # F
        'air_rh': 30.0,                # %
        'air_flow_rate': 500.0,        # CFM
        'grain_flow_rate': 1000.0,     # kg/hr
        'width': 3.0,                  # m
        'length': 5.0                  # m
    }
    
    # Run simulation
    result = interface.run_simulation(
        model_type='fixed_bed',
        crop_name='Corn',
        process_params=process_params,
        user_info=user_info
    )
    
    if result['success']:
        print("Simulation completed successfully!")
        print(f"Results: {result['results']}")
    else:
        print(f"Simulation failed: {result['error']}")


if __name__ == '__main__':
    example_usage()
