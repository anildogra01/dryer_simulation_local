"""
Dryer Simulation Flask Backend API - WITH HTML SERVING
=======================================================

Complete Flask backend that serves both API and frontend HTML.
Just run this file and go to http://localhost:5000/

Author: Claude
Date: 2026-01-04
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import math
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)  # Enable CORS for frontend requests

# ============================================================================
# CROP DATA & CONSTANTS
# ============================================================================

CROP_PRESETS = {
    "corn": {
        "name": "Corn (Yellow Dent)",
        "initial_moisture": 25.0,
        "safe_storage_moisture": 15.5,
        "bulk_density": 56.0,  # lb/bu
        "specific_heat": 0.45,  # BTU/lb-°F
        "latent_heat": 1050,  # BTU/lb water
        "max_temp": 130,  # °F max drying temp
        "rewet_factor": 0.85
    },
    "soybeans": {
        "name": "Soybeans",
        "initial_moisture": 18.0,
        "safe_storage_moisture": 13.0,
        "bulk_density": 60.0,
        "specific_heat": 0.46,
        "latent_heat": 1060,
        "max_temp": 110,
        "rewet_factor": 0.88
    },
    "wheat": {
        "name": "Wheat (Hard Red Winter)",
        "initial_moisture": 20.0,
        "safe_storage_moisture": 14.0,
        "bulk_density": 60.0,
        "specific_heat": 0.44,
        "latent_heat": 1055,
        "max_temp": 140,
        "rewet_factor": 0.82
    },
    "rice": {
        "name": "Rice (Long Grain)",
        "initial_moisture": 22.0,
        "safe_storage_moisture": 14.0,
        "bulk_density": 45.0,
        "specific_heat": 0.40,
        "latent_heat": 1040,
        "max_temp": 110,
        "rewet_factor": 0.80
    },
    "barley": {
        "name": "Barley",
        "initial_moisture": 20.0,
        "safe_storage_moisture": 14.5,
        "bulk_density": 48.0,
        "specific_heat": 0.43,
        "latent_heat": 1045,
        "max_temp": 120,
        "rewet_factor": 0.83
    },
    "oats": {
        "name": "Oats",
        "initial_moisture": 18.0,
        "safe_storage_moisture": 14.0,
        "bulk_density": 32.0,
        "specific_heat": 0.42,
        "latent_heat": 1050,
        "max_temp": 110,
        "rewet_factor": 0.84
    }
}

# ============================================================================
# PSYCHROMETRIC CALCULATIONS
# ============================================================================

def calculate_vapor_pressure(temp_f):
    """Calculate saturation vapor pressure at given temperature (psia)"""
    temp_c = (temp_f - 32) * 5/9
    # Antoine equation for water
    pv_mmhg = 10 ** (8.07131 - (1730.63 / (temp_c + 233.426)))
    pv_psia = pv_mmhg * 0.01934  # Convert mmHg to psia
    return pv_psia

def calculate_humidity_ratio(temp_f, rh_percent):
    """Calculate humidity ratio (lb water/lb dry air)"""
    rh = rh_percent / 100.0
    p_sat = calculate_vapor_pressure(temp_f)
    p_vapor = rh * p_sat
    p_atm = 14.696  # psia at sea level
    
    # Humidity ratio
    w = 0.622 * (p_vapor / (p_atm - p_vapor))
    return w

def calculate_wet_bulb_temp(temp_f, rh_percent):
    """Approximate wet bulb temperature using psychrometric relations"""
    w = calculate_humidity_ratio(temp_f, rh_percent)
    p_sat = calculate_vapor_pressure(temp_f)
    
    # Iterative approximation for wet bulb
    twb = temp_f
    for _ in range(10):
        p_sat_wb = calculate_vapor_pressure(twb)
        w_sat = 0.622 * (p_sat_wb / (14.696 - p_sat_wb))
        twb_new = temp_f - (1093 * (w_sat - w)) / (0.24 + 0.45 * w_sat)
        if abs(twb_new - twb) < 0.01:
            break
        twb = twb_new
    
    return twb

def calculate_enthalpy(temp_f, humidity_ratio):
    """Calculate enthalpy of moist air (BTU/lb dry air)"""
    h = 0.24 * temp_f + humidity_ratio * (1061 + 0.444 * temp_f)
    return h

def calculate_specific_volume(temp_f, humidity_ratio):
    """Calculate specific volume (ft³/lb dry air)"""
    temp_r = temp_f + 459.67  # Convert to Rankine
    v = 0.754 * temp_r * (1 + 1.6078 * humidity_ratio) / 14.696
    return v

def calculate_dew_point(temp_f, rh_percent):
    """Calculate dew point temperature"""
    rh = rh_percent / 100.0
    p_vapor = rh * calculate_vapor_pressure(temp_f)
    
    # Inverse Antoine equation
    if p_vapor <= 0:
        return temp_f
    
    temp_c_dp = (1730.63 / (8.07131 - math.log10(p_vapor / 0.01934))) - 233.426
    temp_f_dp = temp_c_dp * 9/5 + 32
    return temp_f_dp

# ============================================================================
# EQUILIBRIUM MOISTURE CONTENT
# ============================================================================

def calculate_equilibrium_moisture(temp_f, rh_percent, crop_type="corn"):
    """
    Calculate equilibrium moisture content using Modified Henderson equation
    EMC = equilibrium moisture content (% dry basis)
    """
    rh = rh_percent / 100.0
    temp_c = (temp_f - 32) * 5/9
    
    # Ensure RH is valid
    rh = max(0.01, min(rh, 0.99))  # Prevent log errors
    
    # Modified Henderson equation constants (vary by crop)
    if crop_type in ["corn", "wheat", "barley"]:
        A = 1e-5
        B = 2.0
        C = 50
    elif crop_type == "soybeans":
        A = 8e-6
        B = 1.9
        C = 52
    else:
        A = 1e-5
        B = 2.0
        C = 50
    
    # Henderson equation: EMC = [ln(1-RH) / (-A * (T + C))]^(1/B)
    try:
        ln_term = -math.log(1 - rh) / (A * (temp_c + C))
        emc = (ln_term ** (1/B))
        
        # Bounds checking
        emc = max(5, min(emc, 25))
    except:
        # Fallback calculation if math error
        emc = 10.0
    
    return emc

# ============================================================================
# DRYING SIMULATION ENGINE
# ============================================================================

def simulate_crossflow_dryer(inputs):
    """
    Main crossflow dryer simulation function
    
    Inputs:
        - crop: dict with crop properties
        - initial_grain_temp: °F
        - inlet_air_temp: °F
        - inlet_air_rh: %
        - target_moisture: % db
        - airflow_cfm: ft³/min
        - grain_flow_bph: bushels/hour
        - width: ft (dryer column width)
        - length: ft (dryer column length)
    
    Returns:
        - dict with simulation results
    """
    
    # Extract inputs
    crop = inputs['crop']
    T_grain_initial = inputs['initial_grain_temp']
    T_air_inlet = inputs['inlet_air_temp']
    RH_air_inlet = inputs['inlet_air_rh']
    MC_target = inputs['target_moisture']
    CFM = inputs['airflow_cfm']
    grain_flow_bph = inputs['grain_flow_bph']
    width = inputs['width']
    length = inputs['length']
    
    # Get crop properties
    bulk_density = crop.get('bulk_density', 56)
    specific_heat = crop.get('specific_heat', 0.45)
    latent_heat = crop.get('latent_heat', 1050)
    MC_initial = crop.get('initial_moisture', 20)
    rewet_factor = crop.get('rewet_factor', 0.85)
    crop_name = crop.get('name', 'Unknown').lower()
    
    # Calculate air properties
    w_inlet = calculate_humidity_ratio(T_air_inlet, RH_air_inlet)
    h_inlet = calculate_enthalpy(T_air_inlet, w_inlet)
    specific_vol = calculate_specific_volume(T_air_inlet, w_inlet)
    
    # Air mass flow rate (lb dry air/hr)
    air_mass_flow = (CFM * 60) / specific_vol
    
    # Grain mass flow rate (lb/hr)
    grain_mass_flow = grain_flow_bph * bulk_density
    
    # Air to grain ratio
    air_grain_ratio = air_mass_flow / grain_mass_flow
    
    # Calculate equilibrium moisture content
    MC_equilibrium = calculate_equilibrium_moisture(T_air_inlet, RH_air_inlet, 
                                                     crop_name.split()[0])
    
    # Drying potential (moisture that can be removed)
    MC_current = MC_initial
    drying_rate_factor = 1.0
    
    # Heat transfer coefficient (empirical)
    # Depends on airflow velocity and grain properties
    air_velocity = CFM / (width * length)  # ft/min
    h_transfer = 2.5 + 0.03 * air_velocity  # BTU/hr-ft²-°F
    
    # Surface area for heat transfer
    surface_area = 2 * width * length  # Simplified, both sides
    
    # Time step simulation (hours)
    dt = 0.1  # 6 minute intervals
    max_time = 24  # Max 24 hours
    time_elapsed = 0
    
    # Energy tracking
    total_energy = 0
    water_removed_total = 0
    
    # Temperature tracking
    T_grain = T_grain_initial
    
    # Simulation loop
    warnings = []
    
    while MC_current > MC_target and time_elapsed < max_time:
        # Check if we can still dry (MC > equilibrium)
        if MC_current <= MC_equilibrium * 1.05:
            warnings.append(f"Approaching equilibrium moisture ({MC_equilibrium:.2f}% db)")
            break
        
        # Temperature difference drives heat transfer
        delta_T = T_air_inlet - T_grain
        
        # Heat transfer to grain
        Q_transfer = h_transfer * surface_area * delta_T * dt
        
        # Grain temperature increase
        mass_grain_section = grain_mass_flow * dt
        dT_grain = Q_transfer / (mass_grain_section * specific_heat)
        T_grain = min(T_grain + dT_grain, T_air_inlet * 0.95)
        
        # Drying rate (empirical Page equation modified)
        k = 0.3 * air_grain_ratio * (1 + 0.01 * delta_T)
        
        # Moisture ratio
        moisture_span = MC_initial - MC_equilibrium
        if moisture_span > 0.01:
            MR = (MC_current - MC_equilibrium) / moisture_span
        else:
            MR = 0
        
        # Page equation: MR = exp(-k*t^n)
        n = 1.2
        if time_elapsed > 0:
            dMR_dt = -k * n * (time_elapsed ** (n-1)) * math.exp(-k * (time_elapsed ** n))
        else:
            dMR_dt = -k
        
        # Change in moisture content
        dMC = dMR_dt * (MC_initial - MC_equilibrium) * dt * drying_rate_factor
        
        # Update moisture content
        MC_current = max(MC_current + dMC, MC_equilibrium)
        
        # Water removed this timestep
        water_removed_dt = -dMC * mass_grain_section / 100
        water_removed_total += water_removed_dt
        
        # Energy consumed this timestep
        energy_dt = water_removed_dt * latent_heat + Q_transfer
        total_energy += energy_dt
        
        # Increment time
        time_elapsed += dt
    
    # Final calculations
    moisture_removed = MC_initial - MC_current
    target_achieved = MC_current <= MC_target
    
    # Exit air properties (approximation)
    if time_elapsed > 0 and air_mass_flow > 0:
        water_added_to_air = water_removed_total / (air_mass_flow * time_elapsed)
    else:
        water_added_to_air = 0
    w_outlet = w_inlet + water_added_to_air
    
    # Outlet temperature (heat loss to grain and evaporation)
    Q_grain = grain_mass_flow * specific_heat * (T_grain - T_grain_initial) * time_elapsed
    Q_evap = water_removed_total * latent_heat
    Q_total_used = Q_grain + Q_evap
    
    if time_elapsed > 0 and air_mass_flow > 0:
        T_air_outlet = T_air_inlet - (Q_total_used / (air_mass_flow * 0.24 * time_elapsed))
    else:
        T_air_outlet = T_air_inlet
    T_air_outlet = max(T_air_outlet, T_grain)
    
    # Calculate outlet RH
    p_sat_outlet = calculate_vapor_pressure(T_air_outlet)
    p_vapor_outlet = w_outlet * 14.696 / (0.622 + w_outlet)
    RH_outlet = min(100, 100 * p_vapor_outlet / p_sat_outlet)
    
    # Additional warnings
    if T_grain > crop.get('max_temp', 140):
        warnings.append(f"Grain temperature ({T_grain:.1f}°F) exceeded safe maximum!")
    
    if air_grain_ratio < 0.5:
        warnings.append("Low air-to-grain ratio may result in slow drying")
    
    if air_grain_ratio > 3.0:
        warnings.append("High air-to-grain ratio may be inefficient")
    
    # Build outputs
    outputs = {
        "final_moisture": round(MC_current, 2),
        "moisture_removed": round(moisture_removed, 2),
        "drying_time": round(time_elapsed, 2),
        "target_achieved": target_achieved,
        "energy_consumed": round(total_energy, 0),
        "air_grain_ratio": round(air_grain_ratio, 3),
        "heat_transfer_coeff": round(h_transfer, 2),
        "equilibrium_moisture": round(MC_equilibrium, 2),
        "air_mass_flow": round(air_mass_flow, 2),
        "grain_mass_flow": round(grain_mass_flow, 2),
        "water_removed": round(water_removed_total / time_elapsed if time_elapsed > 0 else 0, 2),
        "final_grain_temp": round(T_grain, 1),
        "outlet_air_temp": round(T_air_outlet, 1),
        "outlet_air_rh": round(RH_outlet, 1),
        "warnings": warnings
    }
    
    return outputs

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_dryer_parameters(inputs):
    """Validate simulation input parameters"""
    errors = []
    warnings = []
    
    # Temperature validation
    inlet_temp = inputs.get('inlet_air_temp', 0)
    if inlet_temp < 60:
        errors.append("Inlet air temperature must be at least 60°F")
    if inlet_temp > 250:
        errors.append("Inlet air temperature too high (max 250°F)")
    if inlet_temp > 220:
        warnings.append("Very high temperature may damage grain quality")
    
    # RH validation
    inlet_rh = inputs.get('inlet_air_rh', 0)
    if inlet_rh < 0 or inlet_rh > 100:
        errors.append("Relative humidity must be between 0-100%")
    if inlet_rh > 20:
        warnings.append("High inlet RH may reduce drying efficiency")
    
    # Moisture validation
    target_mc = inputs.get('target_moisture', 0)
    if target_mc < 8:
        warnings.append("Target moisture below 8% may cause over-drying and grain damage")
    if target_mc > 20:
        warnings.append("Target moisture above 20% may not be safe for storage")
    
    # Crop validation
    crop = inputs.get('crop', {})
    initial_mc = crop.get('initial_moisture', 0)
    if target_mc >= initial_mc:
        errors.append("Target moisture must be lower than initial moisture")
    
    # Airflow validation
    cfm = inputs.get('airflow_cfm', 0)
    if cfm <= 0:
        errors.append("Airflow must be greater than 0 CFM")
    if cfm < 500:
        warnings.append("Low airflow may result in very slow drying")
    
    # Grain flow validation
    grain_flow = inputs.get('grain_flow_bph', 0)
    if grain_flow <= 0:
        errors.append("Grain flow must be greater than 0 bu/hr")
    
    # Dryer dimensions
    width = inputs.get('width', 0)
    length = inputs.get('length', 0)
    if width <= 0 or length <= 0:
        errors.append("Dryer dimensions must be greater than 0")
    
    # Check air-grain ratio preview
    if cfm > 0 and grain_flow > 0 and crop:
        bulk_density = crop.get('bulk_density', 56)
        specific_vol = calculate_specific_volume(inlet_temp, 
                                                  calculate_humidity_ratio(inlet_temp, inlet_rh))
        air_mass = (cfm * 60) / specific_vol
        grain_mass = grain_flow * bulk_density
        ratio = air_mass / grain_mass if grain_mass > 0 else 0
        
        if ratio < 0.3:
            warnings.append(f"Air-grain ratio ({ratio:.2f}) is very low - drying will be slow")
        if ratio > 4.0:
            warnings.append(f"Air-grain ratio ({ratio:.2f}) is very high - may be inefficient")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the main HTML page"""
    try:
        return send_from_directory(BASE_DIR, 'index.html')
    except:
        return """
        <html>
        <head><title>Dryer Simulation API</title></head>
        <body>
            <h1>Grain Dryer Simulation API</h1>
            <p>Backend is running!</p>
            <p><strong>Note:</strong> index.html not found in current directory.</p>
            <p>Make sure index.html and dryer_frontend.js are in the same folder as this script.</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li>GET /api/health - Health check</li>
                <li>GET /api/crops/presets - Get crop presets</li>
                <li>POST /api/dryer/crossflow - Run crossflow dryer simulation</li>
                <li>POST /api/dryer/psychrometric - Calculate psychrometric properties</li>
                <li>POST /api/dryer/validate - Validate parameters</li>
                <li>POST /api/dryer/estimate-time - Quick drying time estimate</li>
            </ul>
            <p><a href="/debug/routes">View all routes</a></p>
        </body>
        </html>
        """

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (JS, CSS, etc)"""
    return send_from_directory(BASE_DIR, path)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "dryer-simulation-api",
        "version": "1.0.0"
    })

@app.route('/api/crops/presets', methods=['GET'])
def get_crop_presets():
    """Get crop property presets"""
    return jsonify({
        "success": True,
        "crops": CROP_PRESETS,
        "count": len(CROP_PRESETS)
    })

@app.route('/api/dryer/crossflow', methods=['POST'])
def run_crossflow_simulation():
    """Run crossflow dryer simulation"""
    try:
        inputs = request.json
        
        # Validate inputs
        validation = validate_dryer_parameters(inputs)
        if not validation['valid']:
            return jsonify({
                "success": False,
                "error": "Invalid parameters",
                "validation": validation
            }), 400
        
        # Run simulation
        outputs = simulate_crossflow_dryer(inputs)
        
        # Add any validation warnings to output warnings
        if validation['warnings']:
            outputs['warnings'].extend(validation['warnings'])
        
        return jsonify({
            "success": True,
            "outputs": outputs,
            "inputs_used": {
                "crop_name": inputs['crop'].get('name', 'Unknown'),
                "initial_moisture": inputs['crop'].get('initial_moisture'),
                "target_moisture": inputs['target_moisture'],
                "inlet_air_temp": inputs['inlet_air_temp'],
                "inlet_air_rh": inputs['inlet_air_rh']
            }
        })
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dryer/psychrometric', methods=['POST'])
def calculate_psychrometric_properties():
    """Calculate psychrometric properties"""
    try:
        data = request.json
        temp_f = data.get('temp_f')
        rh = data.get('rh')
        
        if temp_f is None or rh is None:
            return jsonify({
                "success": False,
                "error": "Missing temp_f or rh"
            }), 400
        
        # Calculate properties
        w = calculate_humidity_ratio(temp_f, rh)
        h = calculate_enthalpy(temp_f, w)
        v = calculate_specific_volume(temp_f, w)
        twb = calculate_wet_bulb_temp(temp_f, rh)
        tdp = calculate_dew_point(temp_f, rh)
        
        return jsonify({
            "success": True,
            "properties": {
                "dry_bulb_temp": temp_f,
                "relative_humidity": rh,
                "humidity_ratio": round(w, 6),
                "enthalpy": round(h, 2),
                "specific_volume": round(v, 3),
                "wet_bulb_temp": round(twb, 2),
                "dew_point": round(tdp, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Psychrometric calculation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dryer/validate', methods=['POST'])
def validate_parameters():
    """Validate dryer simulation parameters"""
    try:
        inputs = request.json
        validation = validate_dryer_parameters(inputs)
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }), 500

@app.route('/api/dryer/estimate-time', methods=['POST'])
def estimate_drying_time():
    """Quick estimate of drying time"""
    try:
        data = request.json
        
        initial_mc = data.get('initial_moisture')
        target_mc = data.get('target_moisture')
        inlet_temp = data.get('inlet_air_temp')
        inlet_rh = data.get('inlet_air_rh')
        
        if None in [initial_mc, target_mc, inlet_temp, inlet_rh]:
            return jsonify({
                "success": False,
                "error": "Missing required parameters"
            }), 400
        
        # Simple empirical estimate
        moisture_to_remove = initial_mc - target_mc
        
        # Temperature factor (higher temp = faster drying)
        temp_factor = 1.0 + (inlet_temp - 100) / 100
        
        # RH factor (lower RH = faster drying)
        rh_factor = 1.0 / (1.0 - inlet_rh / 100)
        
        # Base drying rate: ~1-2% per hour for moderate conditions
        base_rate = 1.5  # % per hour
        
        effective_rate = base_rate * temp_factor / rh_factor
        estimated_time = moisture_to_remove / effective_rate
        
        # Add buffer for real-world conditions
        estimated_time *= 1.3
        
        return jsonify({
            "success": True,
            "estimated_drying_time_hours": round(estimated_time, 1),
            "moisture_to_remove": round(moisture_to_remove, 2),
            "note": "This is a rough estimate. Run full simulation for accurate results."
        })
        
    except Exception as e:
        logger.error(f"Time estimation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/debug/routes')
def debug_routes():
    """Show all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    
    return jsonify({
        "routes": sorted(routes, key=lambda x: x['path']),
        "count": len(routes)
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "status": 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "status": 500
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("DRYER SIMULATION API SERVER")
    print("=" * 60)
    print("Starting Flask server...")
    print("")
    print("🌐 Main interface: http://localhost:5000/")
    print("🔧 API endpoint: http://localhost:5000/api")
    print("❤️  Health check: http://localhost:5000/api/health")
    print("")
    print("📁 Make sure these files are in the same folder:")
    print("   - dryer_backend.py (this file)")
    print("   - index.html")
    print("   - dryer_frontend.js")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
