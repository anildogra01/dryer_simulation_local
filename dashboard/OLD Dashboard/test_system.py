"""
Diagnostic Script - Test Flask Routes and Database
Run this to check if everything is working
"""

import sys
from pathlib import Path

print("="*70)
print("DIAGNOSTIC SCRIPT - GRAIN DRYER SYSTEM")
print("="*70)

# Check Python path
dashboard_dir = Path(r"C:\dryer_simulation_local\dashboard")
if not dashboard_dir.exists():
    print(f"\n❌ Dashboard directory not found: {dashboard_dir}")
    sys.exit(1)

sys.path.insert(0, str(dashboard_dir))
print(f"\n✅ Dashboard directory: {dashboard_dir}")

# Test 1: Import crop database
print("\n" + "="*70)
print("TEST 1: Crop Master Database")
print("="*70)
try:
    from crop_master_database import CropMasterDB
    crop_db = CropMasterDB()
    crops = crop_db.get_all_crops()
    print(f"✅ CropMasterDB imported successfully")
    print(f"✅ Found {len(crops)} crops:")
    for crop in crops[:5]:
        print(f"   - {crop['crop_name']}")
except Exception as e:
    print(f"❌ CropMasterDB failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Import transaction database
print("\n" + "="*70)
print("TEST 2: Transaction Database")
print("="*70)
try:
    from simulation_transaction_db import SimulationTransactionDB
    trans_db = SimulationTransactionDB()
    print(f"✅ SimulationTransactionDB imported successfully")
    recent = trans_db.get_recent_simulations(limit=3)
    print(f"✅ Found {len(recent)} recent simulations")
except Exception as e:
    print(f"❌ SimulationTransactionDB failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Import enhanced fortran interface
print("\n" + "="*70)
print("TEST 3: Enhanced Fortran Interface")
print("="*70)
try:
    from enhanced_fortran_interface import EnhancedFortranDryerInterface
    fortran = EnhancedFortranDryerInterface()
    print(f"✅ EnhancedFortranDryerInterface imported successfully")
except Exception as e:
    print(f"❌ EnhancedFortranDryerInterface failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Import parser
print("\n" + "="*70)
print("TEST 4: FIXED.OUT Parser")
print("="*70)
try:
    from fixed_out_parser import FixedOutParser
    print(f"✅ FixedOutParser imported successfully")
except Exception as e:
    print(f"❌ FixedOutParser failed: {e}")
    print(f"   Make sure fixed_out_parser.py is in: {dashboard_dir}")

# Test 5: Import PDF generator
print("\n" + "="*70)
print("TEST 5: PDF Generator")
print("="*70)
try:
    from dryer_pdf_generator import DryerReportGenerator
    print(f"✅ DryerReportGenerator imported successfully")
except Exception as e:
    print(f"❌ DryerReportGenerator failed: {e}")
    print(f"   Make sure dryer_pdf_generator.py is in: {dashboard_dir}")

# Test 6: Check Flask templates
print("\n" + "="*70)
print("TEST 6: Flask Templates")
print("="*70)
templates_dir = dashboard_dir / "templates"
required_templates = [
    "dashboard_with_monitoring.html",
    "crop_master_ui.html",
    "results.html",
    "simulation_history.html"
]

for template in required_templates:
    template_path = templates_dir / template
    if template_path.exists():
        print(f"✅ {template}")
    else:
        print(f"❌ {template} - NOT FOUND")

# Test 7: Import Flask app
print("\n" + "="*70)
print("TEST 7: Flask App")
print("="*70)
try:
    from app import app
    print(f"✅ Flask app imported successfully")
    print(f"\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.methods} {rule.rule}")
except Exception as e:
    print(f"❌ Flask app failed: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Test crop database query
print("\n" + "="*70)
print("TEST 8: Test Database Query")
print("="*70)
try:
    from crop_master_database import CropMasterDB
    db = CropMasterDB()
    
    # Get a specific crop
    corn = db.get_crop('Corn')
    if corn:
        print(f"✅ Successfully retrieved 'Corn' crop")
        print(f"   ID: {corn['crop_id']}")
        print(f"   Surface Area: {corn['specific_surface_area']}")
    else:
        print(f"❌ Could not retrieve 'Corn' crop")
except Exception as e:
    print(f"❌ Query failed: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nIf all tests passed, run: python app.py")
print("Then open: http://127.0.0.1:5000/")
print("="*70)
