"""
Direct Python-Fortran Interface (No Files!)
Uses compiled Fortran module to call simulation directly
"""

import numpy as np
from pathlib import Path
from datetime import datetime

class DirectFortranInterface:
    """
    Direct interface to Fortran simulation
    No file I/O - all data passed in memory
    """
    
    def __init__(self):
        """Initialize - requires compiled Fortran module"""
        try:
            # Import the compiled Fortran module
            import dryer_module
            self.fortran = dryer_module
            self.available = True
            print("✅ Direct Fortran interface loaded")
        except ImportError:
            self.available = False
            print("⚠️  Fortran module not compiled - use file-based interface")
            print("   To compile: f2py -c dryer_wrapper.f90 PsyFun.f90 emc_grain.f90 -m dryer_module")
    
    def run_simulation(self, user_info, crop_name, crop_properties, process_params):
        """
        Run simulation by calling Fortran directly
        
        Args:
            user_info: Dict with user_name, project_name, address
            crop_name: Name of crop
            crop_properties: Dict with sa, ca, cp, cv, rhop, hfg
            process_params: Dict with all process parameters
            
        Returns:
            Dict with results
        """
        if not self.available:
            return {'success': False, 'error': 'Fortran module not available'}
        
        print("\n" + "="*70)
        print("🚀 CALLING FORTRAN DIRECTLY (No Files!)")
        print("="*70)
        print(f"Crop: {crop_name}")
        print(f"User: {user_info.get('user_name', 'N/A')}")
        print("="*70)
        
        # Prepare parameters
        user_name = user_info.get('user_name', 'N/A')[:100]
        project_name = user_info.get('project_name', 'N/A')[:100]
        address = user_info.get('address', 'N/A')[:200]
        simulation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')[:50]
        
        # Process parameters
        xmo = process_params['initial_moisture']
        thin = (process_params['grain_temp'] - 32) * 5/9  # F to C
        tin = (process_params['air_temp'] - 32) * 5/9
        hin = process_params['air_rh']
        cfm = process_params['air_flow_rate']
        depth = process_params.get('length', 3.0)
        indpr_real = 1.0
        nlpf_real = 10.0
        tt = 0.1
        tbtpr = 1.0
        xmend = process_params['target_moisture']
        
        # Crop properties (convert SI to Imperial)
        sa = crop_properties['specific_surface_area']
        ca = crop_properties['heat_capacity_air'] / 1000.0  # J/kg.K to BTU/lb.F
        cp = crop_properties['heat_capacity_dry_product'] / 1000.0
        cv = crop_properties['heat_capacity_water_vapor'] / 1000.0
        rhop = crop_properties['dry_bulk_density'] / 16.018  # kg/m3 to lb/ft3
        hfg = crop_properties['latent_heat_water'] / 2326.0  # J/kg to BTU/lb
        
        try:
            import time
            start_time = time.time()
            
            # Call Fortran subroutine directly
            result = self.fortran.run_dryer_simulation(
                user_name, project_name, address, crop_name, simulation_date,
                xmo, thin, tin, hin, cfm,
                depth, indpr_real, nlpf_real, tt, tbtpr, xmend,
                sa, ca, cp, cv, rhop, hfg
            )
            
            execution_time = time.time() - start_time
            
            # Unpack results
            moisture_out, temp_out, time_out, n_points, final_moisture, drying_time, success = result
            
            if success == 1:
                print(f"\n✅ Fortran calculation completed!")
                print(f"   ⏱️  Execution time: {execution_time:.3f} seconds")
                print(f"   📊 Final moisture: {final_moisture:.2f}%")
                print(f"   ⏰ Drying time: {drying_time:.2f} hours")
                print(f"   📈 Data points: {n_points}")
                
                # Format results
                results = {
                    'success': True,
                    'execution_time': execution_time,
                    'final_moisture': float(final_moisture),
                    'drying_time': float(drying_time),
                    'n_points': int(n_points),
                    'moisture_vs_time': [
                        [float(time_out[i]), float(moisture_out[i])]
                        for i in range(n_points)
                    ],
                    'temperature_vs_time': [
                        [float(time_out[i]), float(temp_out[i])]
                        for i in range(n_points)
                    ]
                }
                
                return results
            else:
                return {'success': False, 'error': 'Fortran simulation failed'}
                
        except Exception as e:
            print(f"\n❌ Error calling Fortran: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


# Compilation instructions
COMPILE_INSTRUCTIONS = """
================================================================================
TO COMPILE FORTRAN MODULE FOR PYTHON:
================================================================================

1. Make sure you have numpy and a Fortran compiler installed:
   pip install numpy
   
2. Compile with f2py:
   
   Windows (gfortran):
   f2py -c dryer_wrapper.f90 PsyFun.f90 emc_grain.f90 -m dryer_module
   
   Linux/Mac:
   f2py3 -c dryer_wrapper.f90 PsyFun.f90 emc_grain.f90 -m dryer_module

3. This creates dryer_module.pyd (Windows) or dryer_module.so (Linux)

4. Place the .pyd/.so file in the dashboard/ folder

5. Done! Python can now call Fortran directly without files!

================================================================================
BENEFITS:
- No file I/O overhead
- 10-100x faster
- Type safety
- Direct memory access
- Professional architecture
================================================================================
"""

if __name__ == '__main__':
    print(COMPILE_INSTRUCTIONS)
    
    # Test if module is available
    interface = DirectFortranInterface()
    
    if interface.available:
        print("\n✅ Fortran module is compiled and ready!")
        print("   You can now run simulations without file I/O")
    else:
        print("\n⚠️  Fortran module not found")
        print("   Follow the instructions above to compile it")
