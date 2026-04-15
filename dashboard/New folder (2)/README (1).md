# 🌾 Grain Dryer Simulation Dashboard

A complete web-based grain dryer simulation system with real-time monitoring, database storage, and interactive visualizations.

## 🚀 Quick Start

```bash
python run_local.py
```

Then open: **http://localhost:5000**

## 🎯 What You Can Do

1. **Select Grain Type** - Choose from Corn, Wheat, Soybeans, Rice, or Barley
2. **Set Parameters** - Configure moisture levels, temperature, airflow
3. **Run Simulation** - Watch real-time drying progress
4. **View Results** - See graphs, statistics, and iteration data
5. **Save to Database** - All simulations are automatically saved

## 📊 Features

✅ **Real-Time Monitoring** - Live graphs showing moisture decrease over time  
✅ **Database Storage** - SQLite stores all simulations and iterations  
✅ **Multiple Grain Types** - Pre-loaded with 5 common grains  
✅ **Interactive Dashboard** - Modern UI with Plotly graphs  
✅ **Simulation History** - Review past runs  
✅ **Export Data** - Save results to JSON/CSV  

## 📁 Files

- **app.py** - Flask backend with simulation logic
- **database.py** - Database models (Crops, Simulations, Iterations)
- **templates/dashboard.html** - Web interface
- **run_local.py** - Easy startup script
- **db_manager.py** - Database tools

## 🛠️ Database Commands

```bash
python db_manager.py info      # View database stats
python db_manager.py backup    # Backup database
python db_manager.py export    # Export to JSON
```

## 🔧 Customization

### Add Your Own Drying Model

Edit the `simulate_drying()` function in `app.py` to use your actual drying equations (Thompson model, thin-layer, deep-bed, etc.)

### Add New Grains

```python
curl -X POST http://localhost:5000/api/crops \
  -H "Content-Type: application/json" \
  -d '{"name": "Oats", "initial_moisture": 20.0, "target_moisture": 12.0}'
```

## 📈 Simulation Model

Current implementation: **Simplified Exponential Drying Model**
- Moisture decreases exponentially over time
- Affected by air temperature and relative humidity
- Tracks energy consumption (BTU) and water removal (lb)

**Note**: This is a basic model for demonstration. Replace with your actual grain drying equations for accurate results!

## 🐛 Troubleshooting

**Error: Port 5000 in use**
```bash
# Find and kill process
lsof -i :5000
kill -9 <PID>
```

**Error: metadata reserved word**
```bash
python fix_metadata.py
```

**Reset database**
```bash
rm grain_dryer.db
python run_local.py
```

---

🌾 Happy Grain Drying!
