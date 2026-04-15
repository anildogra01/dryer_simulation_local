"""
Enhanced Fortran Dryer Simulation Interface - FIXED for dryer.exe format
Matches the exact input format expected by your Fortran program
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime
from crop_master_database import CropMasterDB
from simulation_transaction_db import SimulationTransactionDB
from fixed_out_parser import FixedOutParser
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import json

class EnhancedFortranDryerInterface:
    """Interface matching dryer.exe input/output format"""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        else:
            base_dir = Path(base_dir)
            
        self.base_dir = base_dir
        
        # Create database directory if it doesn't exist
        db_dir = Path(__file__).parent / 'database'
        db_dir.mkdir(exist_ok=True)
        
        # Initialize both databases in database folder
        self.crop_db = CropMasterDB(db_path=str(db_dir / 'crop_master.db'))
        self.transaction_db = SimulationTransactionDB(db_path=str(db_dir / 'simulation_transactions.db'))
        
        self.models = {
            'fixed_bed': self.base_dir / 'fixed_bed',
            'crossflow': self.base_dir / 'crossflow',
            'counterflow': self.base_dir / 'counterflow',
            'concurrent': self.base_dir / 'concurrent'
        }
        
        self.output_dir = self.base_dir / 'simulation_runs'
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✅ Fortran Interface Initialized")
        print(f"   Base Dir: {self.base_dir}")
        print(f"   Output Dir: {self.output_dir}")
    
    def run_simulation(self, model_type, crop_name, process_params, user_info):
        """Run simulation matching dryer.exe format"""
        print("\n" + "="*70)
        print(f"🚀 STARTING SIMULATION")
        print("="*70)
        print(f"Model Type: {model_type.upper()}")
        print(f"Crop: {crop_name}")
        print(f"User: {user_info.get('user_name', 'N/A')}")
        print(f"Project: {user_info.get('project_name', 'N/A')}")
        print("="*70)
        
        # Create input file
        print("\n📝 Creating input file...")
        try:
            input_file = self.create_input_file(model_type, crop_name, process_params, user_info)
            print(f"   ✅ Input file created: {input_file}")
        except Exception as e:
            print(f"   ❌ Failed to create input file: {e}")
            return {'success': False, 'error': f'Failed to create input file: {e}'}
        
        # Get model directory and executable
        model_dir = self.models[model_type]
        executable = model_dir / 'dryer.exe'
        
        if not executable.exists():
            executable = model_dir / 'dryer'
            if not executable.exists():
                error_msg = f"Executable not found in {model_dir}"
                print(f"   ❌ {error_msg}")
                return {'success': False, 'error': error_msg}
        
        print(f"   ✅ Executable found: {executable}")
        
        # Create unique output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = self.output_dir / f"{model_type}_{crop_name}_{timestamp}"
        run_dir.mkdir(exist_ok=True)
        print(f"   ✅ Output directory: {run_dir}")
        
        # Run Fortran program (it reads from FIXED.DAT file)
        print(f"\n⚙️  Running Fortran simulation...")
        print(f"   Working directory: {model_dir}")
        print(f"   Command: {executable.name}")
        print(f"   Input: {model_dir / 'FIXED.DAT'}")
        print(f"\n{'='*70}")
        print(f"📊 LIVE SIMULATION OUTPUT")
        print(f"{'='*70}\n")
        
        import time
        start_time = time.time()
        
        try:
            # Run with real-time output streaming using Popen
            process = subprocess.Popen(
                [str(executable)],
                cwd=model_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Stream output in real-time
            output_lines = []
            time_points = []
            moisture_points = []
            
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                # Print line immediately
                print(line.rstrip())
                output_lines.append(line)
                
                # Extract key data points for live monitoring
                if "Time =" in line:
                    try:
                        import re
                        time_match = re.search(r'Time =\s+([\d.]+)', line)
                        mc_match = re.search(r'Avg MC =\s+([\d.]+)', line)
                        if time_match and mc_match:
                            t = float(time_match.group(1))
                            mc = float(mc_match.group(1)) * 100
                            time_points.append(t)
                            moisture_points.append(mc)
                            print(f"  ⏱️  Time: {t:.2f} hr | 💧 Moisture: {mc:.2f}%")
                    except:
                        pass
            
            # Wait for process to complete
            return_code = process.wait(timeout=300)
            
            execution_time = time.time() - start_time
            
            print(f"\n{'='*70}")
            print(f"✅ Simulation completed!")
            print(f"⏱️  Execution time: {execution_time:.2f} seconds")
            print(f"📊 Return code: {return_code}")
            print(f"{'='*70}\n")
            
            if return_code != 0:
                print(f"\n   ⚠️  Warning: Non-zero return code")
                return {'success': False, 'error': f"Simulation returned code {return_code}"}
            
            # Show summary of progress
            if time_points:
                print(f"📈 Drying Progress Summary:")
                print(f"   Start: {moisture_points[0]:.2f}% @ {time_points[0]:.2f} hr")
                print(f"   End:   {moisture_points[-1]:.2f}% @ {time_points[-1]:.2f} hr")
                print(f"   Total moisture removed: {moisture_points[0] - moisture_points[-1]:.2f}%\n")
            
            # Parse output file (fixed.out)
            print(f"\n📄 Parsing output files...")
            output_data = self.parse_output(model_dir, model_type)
            
            # Display parsed data in terminal
            if output_data:
                self.display_results_terminal(output_data, process_params)
            else:
                print(f"   ⚠️  No output data found - check {model_dir}/fixed.out")
            
            # Copy output files to run directory
            print(f"\n💾 Saving output files to: {run_dir}")
            self.save_outputs(model_dir, run_dir)
            
            # Generate PDF report
            print(f"\n📈 Generating PDF report...")
            try:
                # Check if we have parsed data
                if 'parsed' in output_data:
                    print(f"   ✓ Parsed data available")
                    print(f"   ✓ Success: {output_data['parsed'].get('success', False)}")
                    print(f"   ✓ Time series points: {len(output_data['parsed'].get('time_series', []))}")
                else:
                    print(f"   ⚠️  No parsed data in output_data")
                    print(f"   Available keys: {list(output_data.keys())}")
                
                pdf_path = self.generate_pdf_report(
                    run_dir, model_type, crop_name, user_info, 
                    process_params, output_data
                )
                
                if pdf_path:
                    print(f"   ✅ PDF report created: {pdf_path}")
                else:
                    print(f"   ⚠️  PDF path is None")
                    
            except Exception as e:
                print(f"   ❌ PDF generation failed: {e}")
                import traceback
                traceback.print_exc()
                pdf_path = None
            
            # Save to database
            print(f"\n💾 Saving to database...")
            try:
                sim_id = self.save_to_database(
                    crop_name, model_type, user_info, 
                    process_params, output_data, run_dir, execution_time
                )
                print(f"   ✅ Saved to database with ID: {sim_id}")
            except Exception as e:
                print(f"   ⚠️  Database save failed: {e}")
                sim_id = None
            
            print("\n" + "="*70)
            print("✅ SIMULATION COMPLETE!")
            print("="*70 + "\n")
            
            return {
                'success': True,
                'simulation_id': sim_id,
                'results': output_data,
                'pdf_path': str(pdf_path) if pdf_path else None,
                'run_directory': str(run_dir),
                'stdout': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            error_msg = 'Simulation timeout (exceeded 5 minutes)'
            print(f"\n   ❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            print(f"\n   ❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def create_input_file(self, model_type, crop_name, process_params, user_info):
        """
        Create FIXED.DAT matching the WORKING Fortran format
        4 lines only, numeric values, no headers
        """
        crop = self.crop_db.get_crop(crop_name)
        if not crop:
            raise ValueError(f"Crop '{crop_name}' not found")
        
        model_dir = self.models.get(model_type)
        input_path = model_dir / 'FIXED.DAT'
        
        # Fortran parameters - matching working format EXACTLY
        xmo = process_params['initial_moisture'] / 100.0  # Convert % to decimal (e.g., 25% → 0.25)
        thin = process_params['grain_temp']  # Fahrenheit (e.g., 90.0)
        tin = process_params['air_temp']     # Fahrenheit (e.g., 160.0)
        
        # Approximate absolute humidity from RH (Fortran will recalculate properly)
        # Working example uses 0.008 for ~3.8% RH at 160°F
        hin = process_params['air_rh'] / 100.0 * 0.02  # Rough approximation
        
        cfm = process_params['air_flow_rate']  # CFM (e.g., 2000.0)
        depth = process_params.get('length', 15.0)  # Bed depth in feet
        indpr_real = 10.0   # Print interval
        nlpf_real = 8.0     # Number of layers per foot
        tt = 12.0           # Time step in hours
        tbtpr = 2.0         # Time between prints
        xmend = process_params['target_moisture'] / 100.0  # Convert % to decimal (e.g., 12% → 0.12)
        
        # Write EXACTLY 4 lines matching working FIXED.DAT
        with open(input_path, 'w') as f:
            # Line 1: xmo, thin, tin, hin, cfm
            f.write(f"{xmo}  {thin}  {tin}  {hin}  {cfm}\n")
            # Line 2: depth, indpr_real
            f.write(f"{depth}  {indpr_real}\n")
            # Line 3: nlpf_real, tt
            f.write(f"{nlpf_real}  {tt}\n")
            # Line 4: tbtpr, xmend
            f.write(f"{tbtpr}  {xmend}\n")
        
        # Create separate info file for user documentation
        info_path = model_dir / 'simulation_info.txt'
        with open(info_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("GRAIN DRYER SIMULATION\n")
            f.write("="*70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User: {user_info.get('user_name', 'N/A')}\n")
            f.write(f"Project: {user_info.get('project_name', 'N/A')}\n")
            f.write(f"Address: {user_info.get('address', 'N/A')}\n")
            f.write(f"Crop: {crop_name}\n")
            f.write("="*70 + "\n")
            f.write("\nINPUT PARAMETERS:\n")
            f.write(f"  Initial Moisture: {process_params['initial_moisture']}%\n")
            f.write(f"  Target Moisture: {process_params['target_moisture']}%\n")
            f.write(f"  Grain Temp: {process_params['grain_temp']}°F\n")
            f.write(f"  Air Temp: {process_params['air_temp']}°F\n")
            f.write(f"  Air RH: {process_params['air_rh']}%\n")
            f.write(f"  Air Flow: {process_params['air_flow_rate']} CFM\n")
            f.write(f"  Bed Depth: {depth} ft\n")
        
        print(f"   ✅ Input file created: {input_path}")
        print(f"   📄 Info file created: {info_path}")
        print(f"   📊 Format: 4 lines, working version")
        return input_path
    
    def parse_output(self, model_dir, model_type):
        """Parse FIXED.OUT file using dedicated parser"""
        from fixed_out_parser import FixedOutParser
        
        results = {}
        
        # Check for FIXED.OUT
        output_file = model_dir / 'FIXED.OUT'
        
        if not output_file.exists():
            print(f"   ⚠️  Output file not found: {output_file}")
            return results
        
        # Parse with dedicated parser
        try:
            parser = FixedOutParser(str(output_file))
            parsed_data = parser.parse()
            
            if parsed_data['success']:
                print(f"   ✅ Output parsed successfully")
                print(f"   📊 Time series points: {len(parsed_data['time_series'])}")
                print(f"   📈 Final moisture: {parsed_data['summary'].get('final_moisture_pct', 'N/A')}%")
                print(f"   ⏱️  Total time: {parsed_data['summary'].get('total_time_hr', 'N/A')} hours")
                
                # Store both raw and parsed data
                with open(output_file, 'r') as f:
                    results['raw_output'] = f.read()
                
                results['parsed'] = parsed_data
                results['success'] = True
            else:
                print(f"   ⚠️  Parsing failed")
                results['success'] = False
        
        except Exception as e:
            print(f"   ⚠️  Error parsing output: {e}")
            # Fall back to raw output
            with open(output_file, 'r') as f:
                results['raw_output'] = f.read()
            results['success'] = False
        
        return results
    
    def display_results_terminal(self, output_data, process_params):
        """Display results in terminal"""
        print("\n" + "="*70)
        print("📊 SIMULATION RESULTS")
        print("="*70)
        
        if 'raw_output' in output_data:
            print("\n📄 Output file content (first 1000 chars):")
            print("-" * 70)
            print(output_data['raw_output'][:1000])
            print("-" * 70)
        
        print("="*70)
    
    def save_outputs(self, source_dir, dest_dir):
        """Copy output files"""
        import shutil
        
        # Copy FIXED.OUT
        output_file = source_dir / 'FIXED.OUT'
        if output_file.exists():
            shutil.copy2(output_file, dest_dir)
        
        # Copy FIXED.DAT for reference
        input_file = source_dir / 'FIXED.DAT'
        if input_file.exists():
            shutil.copy2(input_file, dest_dir)
    
    def generate_pdf_report(self, run_dir, model_type, crop_name, user_info, process_params, output_data):
        """Generate comprehensive PDF report with user header, tables, and graphs"""
        from dryer_pdf_generator import DryerReportGenerator
        
        pdf_path = run_dir / 'SIMULATION_REPORT.pdf'
        
        try:
            # Check if we have parsed data
            if 'parsed' in output_data and output_data['parsed'].get('success'):
                parsed_data = output_data['parsed']
                
                # Generate PDF
                generator = DryerReportGenerator(str(pdf_path))
                generator.generate(user_info, crop_name, parsed_data)
                
                print(f"   ✅ PDF report created: {pdf_path}")
                return pdf_path
            else:
                print(f"   ⚠️  No parsed data available, creating basic PDF")
                # Create basic PDF with matplotlib
                with PdfPages(pdf_path) as pdf:
                    fig = plt.figure(figsize=(8.5, 11))
                    fig.suptitle('GRAIN DRYER SIMULATION REPORT', fontsize=20, fontweight='bold')
                    
                    ax = fig.add_subplot(111)
                    ax.axis('off')
                    
                    y_pos = 0.9
                    ax.text(0.1, y_pos, f"User: {user_info.get('user_name', 'N/A')}", fontsize=12)
                    y_pos -= 0.05
                    ax.text(0.1, y_pos, f"Project: {user_info.get('project_name', 'N/A')}", fontsize=12)
                    y_pos -= 0.05
                    ax.text(0.1, y_pos, f"Address: {user_info.get('address', 'N/A')}", fontsize=12)
                    y_pos -= 0.05
                    ax.text(0.1, y_pos, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=12)
                    y_pos -= 0.08
                    ax.text(0.1, y_pos, f"Model: {model_type.upper()}", fontsize=12, fontweight='bold')
                    y_pos -= 0.05
                    ax.text(0.1, y_pos, f"Crop: {crop_name}", fontsize=12)
                    
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close()
                
                return pdf_path
                
        except Exception as e:
            print(f"   ⚠️  PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_to_database(self, crop_name, model_type, user_info, process_params, output_data, run_dir, execution_time=None):
        """Save to transaction database"""
        crop = self.crop_db.get_crop(crop_name)
        
        sim_data = {
            'run_timestamp': datetime.now().isoformat(),
            'user_name': user_info.get('user_name'),
            'project_name': user_info.get('project_name'),
            'address': user_info.get('address'),
            'crop_id': crop['crop_id'],
            'crop_name': crop_name,
            'model_type': model_type,
            'initial_moisture': process_params['initial_moisture'],
            'target_moisture': process_params['target_moisture'],
            'grain_temp_f': process_params['grain_temp'],
            'air_temp_f': process_params['air_temp'],
            'air_rh': process_params['air_rh'],
            'air_flow_cfm': process_params['air_flow_rate'],
            'grain_flow_rate': process_params.get('grain_flow_rate'),
            'width_m': process_params.get('width'),
            'length_m': process_params.get('length'),
            'execution_time_sec': execution_time,
            'status': 'success',
            'final_moisture': process_params.get('target_moisture'),  # TODO: Parse from output
            'drying_time_hours': 0.0,  # TODO: Parse from output
            'results': output_data,
            'output_directory': str(run_dir),
            'pdf_report_path': str(run_dir / 'SIMULATION_REPORT.pdf')
        }
        
        return self.transaction_db.save_simulation(sim_data)
    
    def get_simulation_history(self, limit=50):
        """Get simulation history from transaction DB"""
        return self.transaction_db.get_recent_simulations(limit)


if __name__ == '__main__':
    interface = EnhancedFortranDryerInterface()
    print("✅ Enhanced interface initialized successfully")
