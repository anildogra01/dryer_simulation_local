# Grain Dryer Simulation System 🌾

A complete web-based grain dryer simulation system with Flask backend and JavaScript frontend.

## 🎯 Overview

This system simulates crossflow grain dryer performance, calculating:
- Drying time and moisture removal
- Energy consumption
- Air and grain flow dynamics
- Psychrometric properties
- Equilibrium moisture content

## 📁 Files Included

```
.
├── dryer_backend.py        # Flask API server
├── dryer_frontend.js       # JavaScript client library
├── index.html              # Demo web interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Or install manually:
pip install Flask flask-cors
```

### 2. Start the Backend

```bash
python dryer_backend.py
```

The API will be available at: `http://localhost:5000/api`

You should see:
```
============================================================
DRYER SIMULATION API SERVER
============================================================
Starting Flask server...
API will be available at: http://localhost:5000/api
Main page: http://localhost:5000/
Health check: http://localhost:5000/api/health
============================================================
```

### 3. Open the Frontend

**Option A: Simple test page**
Open `index.html` in your browser (works with the standalone HTML file)

**Option B: Integrate into your existing app**
1. Copy `dryer_frontend.js` to your project
2. Include it in your HTML: `<script src="dryer_frontend.js"></script>`
3. Use the API client as shown in the examples below

## 📡 API Endpoints

### Health Check
```
GET /api/health
```
Returns server health status.

### Get Crop Presets
```
GET /api/crops/presets
```
Returns available crop types with default properties.

**Response:**
```json
{
  "success": true,
  "crops": {
    "corn": {
      "name": "Corn (Yellow Dent)",
      "initial_moisture": 25.0,
      "safe_storage_moisture": 15.5,
      "bulk_density": 56.0,
      ...
    },
    ...
  }
}
```

### Run Simulation
```
POST /api/dryer/crossflow
```

**Request Body:**
```json
{
  "crop": { ... },
  "initial_grain_temp": 60,
  "inlet_air_temp": 180,
  "inlet_air_rh": 5,
  "target_moisture": 15,
  "airflow_cfm": 1000,
  "grain_flow_bph": 100,
  "width": 2.0,
  "length": 10.0
}
```

**Response:**
```json
{
  "success": true,
  "outputs": {
    "final_moisture": 15.2,
    "drying_time": 4.5,
    "energy_consumed": 125000,
    "target_achieved": true,
    ...
  }
}
```

### Validate Parameters
```
POST /api/dryer/validate
```
Validates simulation parameters before running.

### Calculate Psychrometric Properties
```
POST /api/dryer/psychrometric
```

**Request:**
```json
{
  "temp_f": 180,
  "rh": 5
}
```

### Estimate Drying Time
```
POST /api/dryer/estimate-time
```

**Request:**
```json
{
  "initial_moisture": 25,
  "target_moisture": 15,
  "inlet_air_temp": 180,
  "inlet_air_rh": 5
}
```

## 💻 JavaScript Usage Examples

### Basic Usage

```javascript
// Initialize client
const apiClient = new DryerSimulationClient('http://localhost:5000/api');
const ui = new DryerSimulationUI(apiClient);

// Load crops into dropdown
await ui.populateCropDropdown('cropSelect');

// Run simulation
const result = await ui.runSimulationFromForm('dryerForm');
```

### Advanced Usage

```javascript
// Get crop presets
const crops = await apiClient.getCropPresets();

// Build custom inputs
const inputs = {
  crop: crops.crops.corn,
  initial_grain_temp: 60,
  inlet_air_temp: 180,
  inlet_air_rh: 5,
  target_moisture: 15,
  airflow_cfm: 1000,
  grain_flow_bph: 100,
  width: 2.0,
  length: 10.0
};

// Validate first
const validation = await apiClient.validateParameters(inputs);
if (validation.valid) {
  // Run simulation
  const result = await apiClient.runCrossflowSimulation(inputs);
  console.log(result.outputs);
}

// Quick time estimate
const estimate = await apiClient.estimateDryingTime({
  initial_moisture: 25,
  target_moisture: 15,
  inlet_air_temp: 180,
  inlet_air_rh: 5
});
console.log(`Estimated time: ${estimate.estimated_drying_time_hours} hours`);
```

## 🌾 Available Crops

The system includes presets for:
- **Corn** (Yellow Dent)
- **Soybeans**
- **Wheat** (Hard Red Winter)
- **Rice** (Long Grain)
- **Barley**
- **Oats**

Each crop has specific properties:
- Initial moisture content
- Safe storage moisture
- Bulk density
- Specific heat
- Latent heat of vaporization
- Maximum safe drying temperature
- Rewetting factor

## 📊 Simulation Outputs

The simulation provides:

**Drying Performance:**
- Final moisture content (% db)
- Moisture removed (points)
- Drying time (hours)
- Target achieved (boolean)

**Energy & Efficiency:**
- Energy consumed (BTU)
- Air-to-grain ratio
- Heat transfer coefficient
- Equilibrium moisture content

**Mass Flows:**
- Air mass flow (lb/hr)
- Grain mass flow (lb/hr)
- Water removed (lb/hr)

**Temperatures:**
- Final grain temperature (°F)
- Outlet air temperature (°F)
- Outlet air relative humidity (%)

**Warnings:**
- Array of any warnings or recommendations

## 🔧 Integration Guide

### Into Existing Flask App

```python
# Add to your existing Flask app
from dryer_backend import (
    get_crop_presets,
    run_crossflow_simulation,
    validate_parameters,
    calculate_psychrometric_properties,
    estimate_drying_time
)

# Register routes
app.route('/api/crops/presets', methods=['GET'])(get_crop_presets)
app.route('/api/dryer/crossflow', methods=['POST'])(run_crossflow_simulation)
# ... etc
```

### Into Existing HTML/JS App

```html
<!-- Include the frontend library -->
<script src="dryer_frontend.js"></script>

<script>
  // Initialize
  const api = new DryerSimulationClient('http://your-backend-url/api');
  const ui = new DryerSimulationUI(api);
  
  // Use in your app
  await ui.populateCropDropdown('yourDropdownId');
</script>
```

## 🔬 Technical Details

### Psychrometric Calculations
- Humidity ratio calculation using vapor pressure
- Enthalpy calculation for moist air
- Wet bulb temperature approximation
- Dew point calculation
- Specific volume calculation

### Equilibrium Moisture
Uses Modified Henderson equation with crop-specific constants:
```
EMC = f(Temperature, Relative Humidity, Crop Type)
```

### Drying Simulation
Based on:
- Heat and mass transfer principles
- Page drying equation (empirical)
- Energy balance equations
- Grain properties and airflow dynamics

### Validation
Automatic parameter validation includes:
- Temperature ranges (60-250°F)
- Relative humidity (0-100%)
- Moisture content ranges
- Airflow and grain flow rates
- Air-to-grain ratio checks

## ⚙️ Configuration

### Change API URL

In your HTML/JavaScript:
```javascript
const apiClient = new DryerSimulationClient('http://your-server:5000/api');
```

### Change Server Port

In `dryer_backend.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Change port here
```

### Enable/Disable CORS

In `dryer_backend.py`:
```python
from flask_cors import CORS
CORS(app)  # Allow all origins

# Or restrict origins:
CORS(app, origins=['http://localhost:3000', 'https://yourdomain.com'])
```

## 🐛 Troubleshooting

### "Failed to load crops" Error

**Problem:** Frontend can't connect to backend
**Solutions:**
1. Check backend is running: `python dryer_backend.py`
2. Verify URL in frontend matches backend
3. Check browser console for CORS errors
4. Ensure port 5000 is not blocked by firewall

### "Unexpected token '<'" Error

**Problem:** Frontend receiving HTML instead of JSON (404 error)
**Solutions:**
1. Verify all API endpoints are registered
2. Check URL paths match exactly
3. Look at `/debug/routes` endpoint to see registered routes
4. Ensure you're using POST for simulation endpoints

### Validation Errors

**Problem:** Parameters not passing validation
**Solutions:**
1. Check temperature ranges (60-250°F)
2. Verify moisture content: target < initial
3. Ensure positive values for airflow and grain flow
4. Check dryer dimensions are > 0

### Simulation Not Converging

**Problem:** Simulation runs too long or doesn't reach target
**Solutions:**
1. Check inlet air conditions (temp too low, RH too high)
2. Verify air-to-grain ratio is reasonable (0.5 - 3.0)
3. Ensure target moisture is above equilibrium moisture
4. Try adjusting airflow or temperature

## 📈 Example Scenarios

### High-Temperature Corn Drying
```javascript
{
  crop: "corn",
  initial_grain_temp: 60,
  inlet_air_temp: 220,
  inlet_air_rh: 3,
  target_moisture: 15.5,
  airflow_cfm: 1500,
  grain_flow_bph: 120
}
```

### Gentle Soybean Drying
```javascript
{
  crop: "soybeans",
  initial_grain_temp: 65,
  inlet_air_temp: 110,
  inlet_air_rh: 8,
  target_moisture: 13,
  airflow_cfm: 800,
  grain_flow_bph: 80
}
```

## 📝 License

This code is provided as-is for educational and commercial use.

## 🤝 Support

For issues or questions:
1. Check this README
2. Examine the example code in `index.html`
3. Review the API documentation above
4. Check browser console for errors
5. Verify backend logs for error messages

## 🔄 Version History

**v1.0.0** (2026-01-04)
- Initial release
- Complete Flask backend
- JavaScript frontend library
- Example HTML interface
- Six crop presets
- Full psychrometric calculations
- Crossflow dryer simulation
- Parameter validation
- Time estimation

---

**Created by:** Claude  
**Date:** January 4, 2026  
**Technology Stack:** Python Flask, JavaScript, HTML5, CSS3
