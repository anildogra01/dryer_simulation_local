"""
Crop Master Management Dashboard
=================================

Integrated Flask application with:
- Main dashboard
- Grain dryer simulator
- History tracking
- Multiple pages

Author: Claude
Date: 2026-01-04
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import math
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

# Store simulation history
simulation_history = []

# ============================================================================
# CROP DATA & CONSTANTS (Same as before)
# ============================================================================

CROP_PRESETS = {
    "corn": {
        "name": "Corn (Yellow Dent)",
        "initial_moisture": 25.0,
        "safe_storage_moisture": 15.5,
        "bulk_density": 56.0,
        "specific_heat": 0.45,
        "latent_heat": 1050,
        "max_temp": 130,
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
# PSYCHROMETRIC & CALCULATION FUNCTIONS (Same as before)
# ============================================================================

def calculate_vapor_pressure(temp_f):
    temp_c = (temp_f - 32) * 5/9
    pv_mmhg = 10 ** (8.07131 - (1730.63 / (temp_c + 233.426)))
    pv_psia = pv_mmhg * 0.01934
    return pv_psia

def calculate_humidity_ratio(temp_f, rh_percent):
    rh = rh_percent / 100.0
    p_sat = calculate_vapor_pressure(temp_f)
    p_vapor = rh * p_sat
    p_atm = 14.696
    w = 0.622 * (p_vapor / (p_atm - p_vapor))
    return w

def calculate_wet_bulb_temp(temp_f, rh_percent):
    w = calculate_humidity_ratio(temp_f, rh_percent)
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
    h = 0.24 * temp_f + humidity_ratio * (1061 + 0.444 * temp_f)
    return h

def calculate_specific_volume(temp_f, humidity_ratio):
    temp_r = temp_f + 459.67
    v = 0.754 * temp_r * (1 + 1.6078 * humidity_ratio) / 14.696
    return v

def calculate_dew_point(temp_f, rh_percent):
    rh = rh_percent / 100.0
    p_vapor = rh * calculate_vapor_pressure(temp_f)
    if p_vapor <= 0:
        return temp_f
    temp_c_dp = (1730.63 / (8.07131 - math.log10(p_vapor / 0.01934))) - 233.426
    temp_f_dp = temp_c_dp * 9/5 + 32
    return temp_f_dp

def calculate_equilibrium_moisture(temp_f, rh_percent, crop_type="corn"):
    rh = rh_percent / 100.0
    temp_c = (temp_f - 32) * 5/9
    rh = max(0.01, min(rh, 0.99))
    
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
    
    try:
        ln_term = -math.log(1 - rh) / (A * (temp_c + C))
        emc = (ln_term ** (1/B))
        emc = max(5, min(emc, 25))
    except:
        emc = 10.0
    
    return emc

def simulate_crossflow_dryer(inputs):
    """Main simulation function - same as before"""
    crop = inputs['crop']
    T_grain_initial = inputs['initial_grain_temp']
    T_air_inlet = inputs['inlet_air_temp']
    RH_air_inlet = inputs['inlet_air_rh']
    MC_target = inputs['target_moisture']
    CFM = inputs['airflow_cfm']
    grain_flow_bph = inputs['grain_flow_bph']
    width = inputs['width']
    length = inputs['length']
    
    bulk_density = crop.get('bulk_density', 56)
    specific_heat = crop.get('specific_heat', 0.45)
    latent_heat = crop.get('latent_heat', 1050)
    MC_initial = crop.get('initial_moisture', 20)
    rewet_factor = crop.get('rewet_factor', 0.85)
    crop_name = crop.get('name', 'Unknown').lower()
    
    w_inlet = calculate_humidity_ratio(T_air_inlet, RH_air_inlet)
    h_inlet = calculate_enthalpy(T_air_inlet, w_inlet)
    specific_vol = calculate_specific_volume(T_air_inlet, w_inlet)
    
    air_mass_flow = (CFM * 60) / specific_vol
    grain_mass_flow = grain_flow_bph * bulk_density
    air_grain_ratio = air_mass_flow / grain_mass_flow
    
    MC_equilibrium = calculate_equilibrium_moisture(T_air_inlet, RH_air_inlet, crop_name.split()[0])
    MC_current = MC_initial
    drying_rate_factor = 1.0
    
    air_velocity = CFM / (width * length)
    h_transfer = 2.5 + 0.03 * air_velocity
    surface_area = 2 * width * length
    
    dt = 0.1
    max_time = 24
    time_elapsed = 0
    
    total_energy = 0
    water_removed_total = 0
    T_grain = T_grain_initial
    warnings = []
    
    while MC_current > MC_target and time_elapsed < max_time:
        if MC_current <= MC_equilibrium * 1.05:
            warnings.append(f"Approaching equilibrium moisture ({MC_equilibrium:.2f}% db)")
            break
        
        delta_T = T_air_inlet - T_grain
        Q_transfer = h_transfer * surface_area * delta_T * dt
        
        mass_grain_section = grain_mass_flow * dt
        dT_grain = Q_transfer / (mass_grain_section * specific_heat)
        T_grain = min(T_grain + dT_grain, T_air_inlet * 0.95)
        
        k = 0.3 * air_grain_ratio * (1 + 0.01 * delta_T)
        
        moisture_span = MC_initial - MC_equilibrium
        if moisture_span > 0.01:
            MR = (MC_current - MC_equilibrium) / moisture_span
        else:
            MR = 0
        
        n = 1.2
        if time_elapsed > 0:
            dMR_dt = -k * n * (time_elapsed ** (n-1)) * math.exp(-k * (time_elapsed ** n))
        else:
            dMR_dt = -k
        
        dMC = dMR_dt * (MC_initial - MC_equilibrium) * dt * drying_rate_factor
        MC_current = max(MC_current + dMC, MC_equilibrium)
        
        water_removed_dt = -dMC * mass_grain_section / 100
        water_removed_total += water_removed_dt
        
        energy_dt = water_removed_dt * latent_heat + Q_transfer
        total_energy += energy_dt
        
        time_elapsed += dt
    
    moisture_removed = MC_initial - MC_current
    target_achieved = MC_current <= MC_target
    
    if time_elapsed > 0 and air_mass_flow > 0:
        water_added_to_air = water_removed_total / (air_mass_flow * time_elapsed)
    else:
        water_added_to_air = 0
    w_outlet = w_inlet + water_added_to_air
    
    Q_grain = grain_mass_flow * specific_heat * (T_grain - T_grain_initial) * time_elapsed
    Q_evap = water_removed_total * latent_heat
    Q_total_used = Q_grain + Q_evap
    
    if time_elapsed > 0 and air_mass_flow > 0:
        T_air_outlet = T_air_inlet - (Q_total_used / (air_mass_flow * 0.24 * time_elapsed))
    else:
        T_air_outlet = T_air_inlet
    T_air_outlet = max(T_air_outlet, T_grain)
    
    p_sat_outlet = calculate_vapor_pressure(T_air_outlet)
    p_vapor_outlet = w_outlet * 14.696 / (0.622 + w_outlet)
    RH_outlet = min(100, 100 * p_vapor_outlet / p_sat_outlet)
    
    if T_grain > crop.get('max_temp', 140):
        warnings.append(f"Grain temperature ({T_grain:.1f}°F) exceeded safe maximum!")
    
    if air_grain_ratio < 0.5:
        warnings.append("Low air-to-grain ratio may result in slow drying")
    
    if air_grain_ratio > 3.0:
        warnings.append("High air-to-grain ratio may be inefficient")
    
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

def validate_dryer_parameters(inputs):
    """Validate simulation input parameters"""
    errors = []
    warnings = []
    
    inlet_temp = inputs.get('inlet_air_temp', 0)
    if inlet_temp < 60:
        errors.append("Inlet air temperature must be at least 60°F")
    if inlet_temp > 250:
        errors.append("Inlet air temperature too high (max 250°F)")
    if inlet_temp > 220:
        warnings.append("Very high temperature may damage grain quality")
    
    inlet_rh = inputs.get('inlet_air_rh', 0)
    if inlet_rh < 0 or inlet_rh > 100:
        errors.append("Relative humidity must be between 0-100%")
    if inlet_rh > 20:
        warnings.append("High inlet RH may reduce drying efficiency")
    
    target_mc = inputs.get('target_moisture', 0)
    if target_mc < 8:
        warnings.append("Target moisture below 8% may cause over-drying and grain damage")
    if target_mc > 20:
        warnings.append("Target moisture above 20% may not be safe for storage")
    
    crop = inputs.get('crop', {})
    initial_mc = crop.get('initial_moisture', 0)
    if target_mc >= initial_mc:
        errors.append("Target moisture must be lower than initial moisture")
    
    cfm = inputs.get('airflow_cfm', 0)
    if cfm <= 0:
        errors.append("Airflow must be greater than 0 CFM")
    if cfm < 500:
        warnings.append("Low airflow may result in very slow drying")
    
    grain_flow = inputs.get('grain_flow_bph', 0)
    if grain_flow <= 0:
        errors.append("Grain flow must be greater than 0 bu/hr")
    
    width = inputs.get('width', 0)
    length = inputs.get('length', 0)
    if width <= 0 or length <= 0:
        errors.append("Dryer dimensions must be greater than 0")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# ============================================================================
# HTML TEMPLATES
# ============================================================================

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crop Master Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
        }
        
        .navbar {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            padding: 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            padding: 0 20px;
        }
        
        .nav-brand {
            color: white;
            font-size: 1.5em;
            font-weight: bold;
            padding: 20px 0;
            margin-right: 40px;
        }
        
        .nav-brand span {
            color: #f39c12;
        }
        
        .nav-links {
            display: flex;
            list-style: none;
            flex: 1;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 20px 25px;
            display: block;
            transition: background 0.3s;
            border-bottom: 3px solid transparent;
        }
        
        .nav-links a:hover {
            background: rgba(255,255,255,0.1);
            border-bottom-color: #f39c12;
        }
        
        .nav-links a.active {
            background: rgba(255,255,255,0.15);
            border-bottom-color: #f39c12;
        }
        
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .welcome-section {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .welcome-section h1 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .welcome-section p {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .card-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .card p {
            color: #7f8c8d;
            line-height: 1.6;
        }
        
        .card-link {
            display: inline-block;
            margin-top: 15px;
            color: #3498db;
            text-decoration: none;
            font-weight: 600;
        }
        
        .card-link:hover {
            color: #2980b9;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-brand">
                🌾 Crop <span>Master</span>
            </div>
            <ul class="nav-links">
                <li><a href="/" class="active">Dashboard</a></li>
                <li><a href="/crop_master">Dryer Simulator</a></li>
                <li><a href="/history">History</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="welcome-section">
            <h1>Welcome to Crop Master Management</h1>
            <p>Your comprehensive grain management and drying simulation platform</p>
        </div>
        
        <div class="cards-grid">
            <div class="card" onclick="window.location.href='/crop_master'">
                <div class="card-icon">🌡️</div>
                <h3>Dryer Simulator</h3>
                <p>Simulate crossflow grain dryer performance with detailed analysis of drying time, energy consumption, and efficiency.</p>
                <a href="/crop_master" class="card-link">Open Simulator →</a>
            </div>
            
            <div class="card" onclick="window.location.href='/history'">
                <div class="card-icon">📊</div>
                <h3>Simulation History</h3>
                <p>View and analyze past simulation runs to track performance and optimize drying parameters.</p>
                <a href="/history" class="card-link">View History →</a>
            </div>
            
            <div class="card">
                <div class="card-icon">📈</div>
                <h3>Analytics</h3>
                <p>Coming soon: Advanced analytics and reporting for your grain drying operations.</p>
                <span class="card-link" style="opacity: 0.5; cursor: not-allowed;">Coming Soon</span>
            </div>
            
            <div class="card">
                <div class="card-icon">⚙️</div>
                <h3>Settings</h3>
                <p>Coming soon: Configure crop presets, default parameters, and system preferences.</p>
                <span class="card-link" style="opacity: 0.5; cursor: not-allowed;">Coming Soon</span>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Import the dryer simulator HTML (we'll use the all-in-one version)
# For now, I'll create a simple reference that loads it

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/crop_master')
def crop_master():
    """Dryer simulator page - fully embedded"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grain Dryer Simulation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .nav-link { position: absolute; top: 20px; left: 20px; }
        .nav-link a { color: white; text-decoration: none; padding: 10px 20px; background: rgba(255,255,255,0.2); border-radius: 5px; transition: background 0.3s; }
        .nav-link a:hover { background: rgba(255,255,255,0.3); }
        .content { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; padding: 30px; }
        @media (max-width: 768px) { .content { grid-template-columns: 1fr; } }
        .section { background: #f8f9fa; padding: 25px; border-radius: 8px; border: 1px solid #dee2e6; }
        .section h2 { color: #2c3e50; margin-bottom: 20px; font-size: 1.5em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: 600; color: #34495e; margin-bottom: 8px; font-size: 0.95em; }
        input[type="number"], select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 1em; transition: border-color 0.3s; }
        input[type="number"]:focus, select:focus { outline: none; border-color: #3498db; }
        .button-group { display: flex; gap: 10px; margin-top: 20px; }
        button { flex: 1; padding: 15px 25px; border: none; border-radius: 6px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s; }
        .btn-primary { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4); }
        .btn-secondary { background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%); color: white; }
        .btn-secondary:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(127, 140, 141, 0.4); }
        #simulationResults { grid-column: 1 / -1; }
        .results-container { background: white; }
        .results-container h3 { color: #27ae60; font-size: 1.8em; margin-bottom: 25px; text-align: center; }
        .result-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #3498db; }
        .result-section h4 { color: #2c3e50; margin-bottom: 15px; font-size: 1.2em; }
        .result-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ecf0f1; }
        .result-row:last-child { border-bottom: none; }
        .label { font-weight: 600; color: #34495e; }
        .value { font-weight: 700; color: #2c3e50; }
        .value.success { color: #27ae60; }
        .value.warning { color: #e67e22; }
        .warnings { background: #fff3cd; border-left-color: #f39c12; }
        .warning-item { padding: 8px; background: white; margin: 5px 0; border-radius: 4px; border-left: 3px solid #f39c12; }
        #loadingIndicator { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 9999; text-align: center; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .info-box { background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="nav-link"><a href="/">← Back to Dashboard</a></div>
            <h1>🌾 Grain Dryer Simulator</h1>
            <p>Crossflow Dryer Performance Analysis</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>Crop Selection</h2>
                <div class="info-box">Select a crop to load preset properties and customize parameters below.</div>
                <div class="form-group">
                    <label for="cropSelect">Crop Type:</label>
                    <select name="crop" id="cropSelect" required><option value="">Loading crops...</option></select>
                </div>
                <div class="form-group">
                    <label for="target_moisture">Target Moisture (% db):</label>
                    <input type="number" name="target_moisture" id="target_moisture" value="15" step="0.1" min="8" max="20" required>
                </div>
            </div>
            <div class="section">
                <h2>Air Conditions</h2>
                <div class="form-group">
                    <label for="inlet_air_temp">Inlet Air Temperature (°F):</label>
                    <input type="number" name="inlet_air_temp" id="inlet_air_temp" value="180" step="1" min="60" max="250" required>
                </div>
                <div class="form-group">
                    <label for="inlet_air_rh">Inlet Air RH (%):</label>
                    <input type="number" name="inlet_air_rh" id="inlet_air_rh" value="5" step="0.1" min="0" max="100" required>
                </div>
                <div class="form-group">
                    <label for="airflow_cfm">Airflow (CFM):</label>
                    <input type="number" name="airflow_cfm" id="airflow_cfm" value="1000" step="10" min="100" required>
                </div>
            </div>
            <div class="section">
                <h2>Grain Conditions</h2>
                <div class="form-group">
                    <label for="initial_grain_temp">Initial Grain Temperature (°F):</label>
                    <input type="number" name="initial_grain_temp" id="initial_grain_temp" value="60" step="1" min="32" max="120" required>
                </div>
                <div class="form-group">
                    <label for="grain_flow_bph">Grain Flow (bu/hr):</label>
                    <input type="number" name="grain_flow_bph" id="grain_flow_bph" value="100" step="1" min="1" required>
                </div>
            </div>
            <div class="section">
                <h2>Dryer Dimensions</h2>
                <div class="form-group">
                    <label for="width">Width (ft):</label>
                    <input type="number" name="width" id="width" value="2.0" step="0.1" min="0.1" required>
                </div>
                <div class="form-group">
                    <label for="length">Length (ft):</label>
                    <input type="number" name="length" id="length" value="10.0" step="0.1" min="0.1" required>
                </div>
                <div class="button-group">
                    <button type="button" id="estimateTimeButton" class="btn-secondary">⚡ Quick Estimate</button>
                    <button type="button" id="runSimulationButton" class="btn-primary">▶ Run Simulation</button>
                </div>
            </div>
            <div id="simulationResults" class="section" style="display: none;"></div>
        </div>
    </div>
    <div id="loadingIndicator" style="display: none;">
        <div class="spinner"></div>
        <div id="loadingText">Running simulation...</div>
    </div>
    <script>
        class DryerSimulationClient { constructor(apiBaseUrl='http://localhost:5000/api'){this.apiBaseUrl=apiBaseUrl} async makeRequest(endpoint,method='GET',data=null){const url=`${this.apiBaseUrl}${endpoint}`;const options={method:method,headers:{'Content-Type':'application/json'}};if(data&&method!=='GET'){options.body=JSON.stringify(data)}const response=await fetch(url,options);const result=await response.json();if(!response.ok){throw new Error(result.error||'API request failed')}return result} async getCropPresets(){return await this.makeRequest('/crops/presets','GET')} async runCrossflowSimulation(inputs){return await this.makeRequest('/dryer/crossflow','POST',inputs)} async validateParameters(inputs){return await this.makeRequest('/dryer/validate','POST',inputs)} async estimateDryingTime(params){return await this.makeRequest('/dryer/estimate-time','POST',params)} }
        function showLoading(message='Loading...'){const loadingDiv=document.getElementById('loadingIndicator');document.getElementById('loadingText').textContent=message;loadingDiv.style.display='block'}
        function hideLoading(){document.getElementById('loadingIndicator').style.display='none'}
        function displayResults(outputs){const resultsDiv=document.getElementById('simulationResults');const html=`<div class="results-container"><h3>Simulation Results</h3><div class="result-section"><h4>Drying Performance</h4><div class="result-row"><span class="label">Final Moisture:</span><span class="value">${outputs.final_moisture.toFixed(2)}% db</span></div><div class="result-row"><span class="label">Moisture Removed:</span><span class="value">${outputs.moisture_removed.toFixed(2)} points</span></div><div class="result-row"><span class="label">Drying Time:</span><span class="value">${outputs.drying_time.toFixed(2)} hours</span></div><div class="result-row"><span class="label">Target Achieved:</span><span class="value ${outputs.target_achieved?'success':'warning'}">${outputs.target_achieved?'✓ Yes':'✗ No'}</span></div></div><div class="result-section"><h4>Energy & Efficiency</h4><div class="result-row"><span class="label">Energy Consumed:</span><span class="value">${outputs.energy_consumed.toFixed(0)} BTU</span></div><div class="result-row"><span class="label">Air/Grain Ratio:</span><span class="value">${outputs.air_grain_ratio.toFixed(3)}</span></div><div class="result-row"><span class="label">Heat Transfer Coef:</span><span class="value">${outputs.heat_transfer_coeff.toFixed(2)} BTU/hr-ft²-°F</span></div><div class="result-row"><span class="label">Equilibrium MC:</span><span class="value">${outputs.equilibrium_moisture.toFixed(2)}% db</span></div></div><div class="result-section"><h4>Mass Flows</h4><div class="result-row"><span class="label">Air Mass Flow:</span><span class="value">${outputs.air_mass_flow.toFixed(2)} lb/hr</span></div><div class="result-row"><span class="label">Grain Mass Flow:</span><span class="value">${outputs.grain_mass_flow.toFixed(2)} lb/hr</span></div><div class="result-row"><span class="label">Water Removed:</span><span class="value">${outputs.water_removed.toFixed(2)} lb/hr</span></div></div>${outputs.warnings&&outputs.warnings.length>0?`<div class="result-section warnings"><h4>⚠ Warnings</h4>${outputs.warnings.map(w=>`<div class="warning-item">${w}</div>`).join('')}</div>`:''}</div>`;resultsDiv.innerHTML=html;resultsDiv.style.display='block'}
        const apiClient=new DryerSimulationClient('http://localhost:5000/api');
        document.addEventListener('DOMContentLoaded',async function(){console.log('Page loaded, initializing...');try{const result=await apiClient.getCropPresets();const selectElement=document.getElementById('cropSelect');selectElement.innerHTML='<option value="">Select crop...</option>';for(const[cropName,cropData]of Object.entries(result.crops)){const option=document.createElement('option');option.value=cropName;option.textContent=cropData.name;option.dataset.cropData=JSON.stringify(cropData);selectElement.appendChild(option)}console.log('Crops loaded successfully')}catch(error){console.error('Failed to load crops:',error);document.getElementById('cropSelect').innerHTML='<option value="">❌ Failed to load crops - Check backend</option>'}
        document.getElementById('runSimulationButton').addEventListener('click',async function(){const cropSelect=document.getElementById('cropSelect');const selectedOption=cropSelect.options[cropSelect.selectedIndex];if(!selectedOption||!selectedOption.dataset.cropData){alert('Please select a crop first');return}const cropData=JSON.parse(selectedOption.dataset.cropData);try{showLoading('Running simulation...');const inputs={crop:cropData,initial_grain_temp:parseFloat(document.getElementById('initial_grain_temp').value),inlet_air_temp:parseFloat(document.getElementById('inlet_air_temp').value),inlet_air_rh:parseFloat(document.getElementById('inlet_air_rh').value),target_moisture:parseFloat(document.getElementById('target_moisture').value),airflow_cfm:parseFloat(document.getElementById('airflow_cfm').value),grain_flow_bph:parseFloat(document.getElementById('grain_flow_bph').value),width:parseFloat(document.getElementById('width').value),length:parseFloat(document.getElementById('length').value)};const validation=await apiClient.validateParameters(inputs);if(!validation.valid){hideLoading();let message='❌ Validation Failed\\n\\n';if(validation.errors.length>0){message+='Errors:\\n'+validation.errors.join('\\n')+'\\n\\n'}if(validation.warnings.length>0){message+='Warnings:\\n'+validation.warnings.join('\\n')}alert(message);return}const result=await apiClient.runCrossflowSimulation(inputs);hideLoading();if(result.success){displayResults(result.outputs);document.getElementById('simulationResults').scrollIntoView({behavior:'smooth',block:'nearest'})}else{throw new Error(result.error||'Simulation failed')}}catch(error){hideLoading();alert('❌ Simulation Error\\n\\n'+error.message);console.error('Simulation error:',error)}});
        document.getElementById('estimateTimeButton').addEventListener('click',async function(){const cropSelect=document.getElementById('cropSelect');const selectedOption=cropSelect.options[cropSelect.selectedIndex];if(!selectedOption||!selectedOption.dataset.cropData){alert('Please select a crop first');return}const cropData=JSON.parse(selectedOption.dataset.cropData);const initialMC=cropData.initial_moisture;const targetMC=parseFloat(document.getElementById('target_moisture').value);const airTemp=parseFloat(document.getElementById('inlet_air_temp').value);const airRH=parseFloat(document.getElementById('inlet_air_rh').value);try{showLoading('Estimating drying time...');const result=await apiClient.estimateDryingTime({initial_moisture:initialMC,target_moisture:targetMC,inlet_air_temp:airTemp,inlet_air_rh:airRH});hideLoading();if(result.success){alert(`⏱️ Estimated Drying Time\\n\\n${result.estimated_drying_time_hours} hours\\n\\nMoisture to remove: ${result.moisture_to_remove}%\\n\\n${result.note}`)}}catch(error){hideLoading();alert('❌ Failed to estimate drying time\\n\\n'+error.message)}})});
    </script>
</body>
</html>''')

@app.route('/history')
def history():
    """Simulation history page"""
    history_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simulation History</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
            .navbar {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                padding: 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .nav-container {
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                padding: 0 20px;
            }
            .nav-brand {
                color: white;
                font-size: 1.5em;
                font-weight: bold;
                padding: 20px 0;
                margin-right: 40px;
            }
            .nav-brand span { color: #f39c12; }
            .nav-links {
                display: flex;
                list-style: none;
                flex: 1;
            }
            .nav-links a {
                color: white;
                text-decoration: none;
                padding: 20px 25px;
                display: block;
                transition: background 0.3s;
                border-bottom: 3px solid transparent;
            }
            .nav-links a:hover {
                background: rgba(255,255,255,0.1);
                border-bottom-color: #f39c12;
            }
            .nav-links a.active {
                background: rgba(255,255,255,0.15);
                border-bottom-color: #f39c12;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                padding: 0 20px;
            }
            .content-box {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #2c3e50; margin-bottom: 20px; }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ecf0f1;
            }
            th {
                background: #f8f9fa;
                font-weight: 600;
                color: #2c3e50;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #7f8c8d;
            }
            .empty-state-icon {
                font-size: 4em;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <div class="nav-brand">
                    🌾 Crop <span>Master</span>
                </div>
                <ul class="nav-links">
                    <li><a href="/">Dashboard</a></li>
                    <li><a href="/crop_master">Dryer Simulator</a></li>
                    <li><a href="/history" class="active">History</a></li>
                </ul>
            </div>
        </nav>
        
        <div class="container">
            <div class="content-box">
                <h1>Simulation History</h1>
                <div id="historyContent"></div>
            </div>
        </div>
        
        <script>
            fetch('/api/history')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('historyContent');
                    if (data.history.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-state-icon">📭</div>
                                <h3>No simulations yet</h3>
                                <p>Run your first simulation to see it here!</p>
                            </div>
                        `;
                    } else {
                        let html = `
                            <table>
                                <thead>
                                    <tr>
                                        <th>Date/Time</th>
                                        <th>Crop</th>
                                        <th>Initial MC</th>
                                        <th>Final MC</th>
                                        <th>Drying Time</th>
                                        <th>Energy (BTU)</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        data.history.forEach(sim => {
                            html += `
                                <tr>
                                    <td>${sim.timestamp}</td>
                                    <td>${sim.crop_name}</td>
                                    <td>${sim.initial_moisture}%</td>
                                    <td>${sim.final_moisture}%</td>
                                    <td>${sim.drying_time} hrs</td>
                                    <td>${sim.energy_consumed}</td>
                                </tr>
                            `;
                        });
                        html += '</tbody></table>';
                        container.innerHTML = html;
                    }
                });
        </script>
    </body>
    </html>
    '''
    return history_html

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "service": "crop-master-dashboard", "version": "1.0.0"})

@app.route('/api/crops/presets', methods=['GET'])
def get_crop_presets():
    return jsonify({"success": True, "crops": CROP_PRESETS, "count": len(CROP_PRESETS)})

@app.route('/api/dryer/crossflow', methods=['POST'])
def run_crossflow_simulation():
    try:
        inputs = request.json
        validation = validate_dryer_parameters(inputs)
        
        if not validation['valid']:
            return jsonify({
                "success": False,
                "error": "Invalid parameters",
                "validation": validation
            }), 400
        
        outputs = simulate_crossflow_dryer(inputs)
        
        if validation['warnings']:
            outputs['warnings'].extend(validation['warnings'])
        
        # Save to history
        simulation_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "crop_name": inputs['crop'].get('name', 'Unknown'),
            "initial_moisture": inputs['crop'].get('initial_moisture'),
            "final_moisture": outputs['final_moisture'],
            "drying_time": outputs['drying_time'],
            "energy_consumed": outputs['energy_consumed'],
            "inputs": inputs,
            "outputs": outputs
        })
        
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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dryer/psychrometric', methods=['POST'])
def calculate_psychrometric_properties():
    try:
        data = request.json
        temp_f = data.get('temp_f')
        rh = data.get('rh')
        
        if temp_f is None or rh is None:
            return jsonify({"success": False, "error": "Missing temp_f or rh"}), 400
        
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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dryer/validate', methods=['POST'])
def validate_parameters():
    try:
        inputs = request.json
        validation = validate_dryer_parameters(inputs)
        return jsonify(validation)
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"valid": False, "errors": [str(e)], "warnings": []}), 500

@app.route('/api/dryer/estimate-time', methods=['POST'])
def estimate_drying_time():
    try:
        data = request.json
        initial_mc = data.get('initial_moisture')
        target_mc = data.get('target_moisture')
        inlet_temp = data.get('inlet_air_temp')
        inlet_rh = data.get('inlet_air_rh')
        
        if None in [initial_mc, target_mc, inlet_temp, inlet_rh]:
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
        
        moisture_to_remove = initial_mc - target_mc
        temp_factor = 1.0 + (inlet_temp - 100) / 100
        rh_factor = 1.0 / (1.0 - inlet_rh / 100)
        base_rate = 1.5
        effective_rate = base_rate * temp_factor / rh_factor
        estimated_time = moisture_to_remove / effective_rate
        estimated_time *= 1.3
        
        return jsonify({
            "success": True,
            "estimated_drying_time_hours": round(estimated_time, 1),
            "moisture_to_remove": round(moisture_to_remove, 2),
            "note": "This is a rough estimate. Run full simulation for accurate results."
        })
    except Exception as e:
        logger.error(f"Time estimation error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get simulation history"""
    return jsonify({
        "success": True,
        "history": simulation_history,
        "count": len(simulation_history)
    })

@app.route('/debug/routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    return jsonify({"routes": sorted(routes, key=lambda x: x['path']), "count": len(routes)})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found", "status": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error", "status": 500}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("CROP MASTER MANAGEMENT DASHBOARD")
    print("=" * 70)
    print("Starting integrated Flask server...")
    print("")
    print("🏠 Main Dashboard: http://localhost:5000/")
    print("🌡️  Dryer Simulator: http://localhost:5000/crop_master")
    print("📊 History: http://localhost:5000/history")
    print("🔧 API Endpoints: http://localhost:5000/api")
    print("")
    print("📁 Make sure 'dryer_simulator_all_in_one.html' is in this folder")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
