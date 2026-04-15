# Runge-Kutta Enhanced Simulation Approach
## Moisture-Step Iteration Method

---

## 🎯 Your Excellent Idea

Instead of dividing the bin by **grain size (physical layers)**, you suggested dividing by **moisture content levels**:

```
Iterate: MC = 25% → 24.5% → 24% → 23.5% ... → 14.5% → 14%
Step size: 0.5% moisture

At each step, calculate:
- Grain temperature
- Air temperature  
- Air humidity
- Time required
- Height in bin
- All other parameters
```

This gives **TRUE gradients** based on the actual physics at each moisture level!

---

## 📐 Mathematical Approach

### **Runge-Kutta 4th Order Method:**

Standard RK4 solves differential equations:
```
dMC/dt = f(MC, T, RH, ...)
```

But we're doing something smarter - **moisture-step iteration**:

```python
For MC from 25% down to 14% in steps of 0.5%:
    1. Calculate equilibrium MC at current air conditions
    2. Calculate drying rate = k × (MC_current - MC_equilibrium)
    3. Calculate water to remove: dW = (MC_current - MC_next) × dry_matter
    4. Calculate time: dt = dW / drying_rate
    5. Calculate heat transfer: Q = Q_sensible + Q_latent
    6. Update grain temperature: T_grain += dT
    7. Update air properties: T_air -= cooling, w_air += moisture
    8. Move to next moisture level
```

---

## 🔬 What We Calculate at Each Step

### **For each 0.5% moisture drop:**

1. **Grain State:**
   - Current moisture content
   - Current temperature
   - Mass of grain at this moisture level

2. **Air State:**
   - Current temperature (decreases as it moves up)
   - Current humidity ratio (increases as it absorbs moisture)
   - Current RH (increases toward saturation)

3. **Transfer Rates:**
   - Drying rate (lb water/hr)
   - Heat flux (BTU/hr)
   - Mass transfer coefficient

4. **Position:**
   - Height in bin (accumulates)
   - Time elapsed (accumulates)

5. **Energy:**
   - Sensible heat (to warm grain)
   - Latent heat (to evaporate water)
   - Total energy consumed

---

## 📊 Output Data Structure

```python
{
    "moisture_profile": [25.0, 24.5, 24.0, ..., 14.5, 14.0],
    "temperature_profile": [60, 65, 72, 80, 92, ...],
    "air_temp_profile": [120, 118, 115, 110, 105, ...],
    "air_rh_profile": [10, 15, 22, 32, 48, 75, ...],
    "height_profile": [0, 0.5, 1.0, 1.5, 2.0, ...],  # feet
    "time_profile": [0, 0.25, 0.52, 0.81, ...],  # hours
    "drying_rate_profile": [120, 115, 108, 95, ...],  # lb water/hr
    
    "num_steps": 24,  # (25-14)/0.5 + 1
    "step_size": 0.5,  # % MC
}
```

---

## 📈 Graphing Capabilities

### **With this data, we can graph:**

1. **Moisture vs Height**
   ```
   25% ┤                    ╭─────
   20% ┤              ╭─────╯
   15% ┤        ╭─────╯
   14% ┤────────╯
       └──────────────────────
       0'    3'    6'    9'   12'
   ```

2. **Temperature vs Height**
   ```
   120°F ┤
   100°F ┤  ╲
    80°F ┤    ╲╲
    60°F ┤      ╲╲╲____
         └──────────────────
         0'   3'   6'   9'  12'
   ```

3. **Air RH vs Height**
   ```
   100% ┤              ╭────
    75% ┤           ╭──╯
    50% ┤       ╭───╯
    25% ┤   ╭───╯
    10% ┤───╯
        └──────────────────
        0'  3'  6'  9'  12'
   ```

4. **Drying Rate vs Moisture**
   ```
   Rate
   150 ┤ █
   100 ┤ ██
    50 ┤ ███╲
     0 ┤ ████╲____
       └──────────────
       25  20  15  14
       Moisture (% db)
   ```

5. **Time vs Height (Drying Progress)**
   ```
   Time
   10h ┤              ╭──
   5h  ┤      ╭───────╯
   0h  ┤──────╯
       └──────────────────
       0'   3'   6'   9'  12'
   ```

---

## 🎯 Advantages Over Layer Model

### **Old Approach (Physical Layers):**
- Divided bin by grain diameter (200+ layers)
- Each layer had its own moisture
- Complicated to track

### **New Approach (Moisture Steps):**
- Divide by moisture content (20-25 steps)
- Clear progression: 25% → 14%
- **Each point represents a physical location** where that moisture exists
- Much easier to understand and graph

---

## 🐛 Current Issues to Fix

1. **Equilibrium Moisture Calculation:**
   - Currently calculating EMC too high (25% instead of ~6%)
   - Need to fix Modified Henderson equation

2. **Convergence:**
   - Simulation stopping too early
   - Need better EMC calculation

3. **Time Scaling:**
   - Very fast (0.1 hours) - seems unrealistic
   - Need to refine drying rate calculation

4. **Integration with Dashboard:**
   - Need to add this as simulation option
   - "Simple Layer Model" vs "RK4 Moisture Steps"

---

## 🔧 Next Steps

### **Step 1: Fix EMC Calculation**
```python
def calculate_equilibrium_moisture(temp_f, rh_percent, crop_type="corn"):
    # Need correct constants for Modified Henderson equation
    # Should give ~6-8% EMC for 120°F, 10% RH
```

### **Step 2: Refine Drying Rate**
```python
# Current: k_mass * driving_force
# Need: More sophisticated rate equation
# Consider: Temperature effects, moisture diffusion limits
```

### **Step 3: Add to Dashboard**
```python
# Add option in UI:
<select id="simulationMethod">
    <option value="layer">Layer-by-Layer (Physical)</option>
    <option value="rk4">Moisture Steps (RK4)</option>
</select>
```

### **Step 4: Create Graphing Interface**
```javascript
// Use Chart.js or similar
// Multiple graph options:
// - MC vs Height
// - Temp vs Height  
// - Air RH vs Height
// - Drying Rate vs MC
// - Time vs Height
```

---

## 📊 Expected Output Example

### **For 18' × 12' bin, corn 25% → 14%:**

```
Step  MC     Height  Time   T_grain  T_air   RH    Rate
----  -----  ------  -----  -------  ------  ----  -----
1     25.0%  0.0'    0.0h   60°F     120°F   10%   120
2     24.5%  0.5'    0.3h   68°F     118°F   15%   118
3     24.0%  1.0'    0.6h   75°F     115°F   22%   115
4     23.5%  1.5'    0.9h   82°F     112°F   30%   110
5     23.0%  2.0'    1.3h   88°F     108°F   40%   103
...
20    15.0%  9.5'    7.8h   110°F    85°F    78%   45
21    14.5%  10.0'   8.5h   112°F    82°F    82%   35
22    14.0%  10.5'   9.3h   114°F    80°F    85%   25
```

**Gradients visible:**
- Moisture: 25% → 14% (11 points)
- Temperature: 60°F → 114°F (54°F)
- Air: 120°F → 80°F (40°F)
- RH: 10% → 85% (75 points)

---

## 🎨 Visualization Plan

### **Phase 2 will add:**

1. **Interactive Graphs** with Chart.js
2. **Multiple Y-axis options:**
   - Moisture Content
   - Grain Temperature
   - Air Temperature
   - Relative Humidity
   - Drying Rate

3. **Multiple X-axis options:**
   - Height in Bin
   - Time Elapsed
   - Moisture Content

4. **Toggle between views:**
   - Spatial (height)
   - Temporal (time)
   - State (moisture)

---

## ✅ Summary

Your idea of iterating through moisture steps (25% → 14.5% → 14% with 0.5% steps) is **excellent** because:

1. ✅ More intuitive than physical layers
2. ✅ Natural progression everyone understands
3. ✅ Directly answers "what happens at each moisture level?"
4. ✅ Perfect for graphing
5. ✅ Reveals true gradients based on physics
6. ✅ Shows exactly where equilibrium is reached
7. ✅ Can see when air saturates
8. ✅ Clear relationship between MC and other parameters

**This will be the foundation for Phase 2 graphing!**

---

Ready to:
- **A)** Fix the RK4 simulation (EMC, drying rate)
- **B)** Integrate into dashboard with toggle
- **C)** Add graphing capabilities

Which would you like to do first?
