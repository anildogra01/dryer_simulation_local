# MULTI-SITE GRAIN MONITORING SYSTEM
## Complete Architecture & Implementation Plan

---

## 🌍 SYSTEM OVERVIEW

**Distributed IoT Grain Monitoring Network**
- Multiple physical locations (farms, silos, depots)
- Multiple bins per location
- ESP32 C3 Super Mini in each bin
- Centralized cloud monitoring
- Single web dashboard for all sites

---

## 🏗️ ARCHITECTURE LAYERS

### **Layer 1: HARDWARE (In-Bin Sensors)**
```
ESP32 C3 Super Mini per Bin
├── SHT31 (pins 5,6) - Temperature & Humidity
├── DHT11 (pin 0) - Backup temp/humidity  
├── Moisture Sensor (pin 7) - Grain moisture
├── Airflow Sensor (pin 8) - CFM measurement
├── Temperature Probes (pins 9,10) - Top/bottom
├── CO2 Sensor (pin 3) - Grain respiration
├── Weight Sensor (pin 4) - Load cells
└── Relay Control (pins 1,2) - Fan/heater control
```

### **Layer 2: CONNECTIVITY**
```
WiFi Connection per Location
├── ESP32 → Local WiFi Router
├── Router → Internet
├── MQTT Broker (optional) or Direct HTTP
├── Fallback: SD Card logging
└── Retry logic with exponential backoff
```

### **Layer 3: CLOUD SERVER**
```
Flask Web Application (VPS or Cloud)
├── REST API endpoints for ESP32
├── WebSocket for real-time updates
├── PostgreSQL/MySQL database
├── User authentication & authorization
├── Multi-tenant architecture
└── Admin dashboard
```

### **Layer 4: USER INTERFACE**
```
Responsive Web Dashboard
├── Location overview map
├── Per-bin live monitoring
├── Predictive analytics
├── Alert management
├── Historical reports
└── Mobile responsive
```

---

## 📊 DATABASE SCHEMA (UPDATED)

### **New Tables Added:**

#### **1. locations**
```sql
- id (PK)
- user_id (FK to users)
- name (Farm A, Silo B, etc.)
- address, city, state, country, zip
- latitude, longitude (for map)
- contact_person, phone, email
- is_active
- created_at, updated_at
```

#### **2. bins**
```sql
- id (PK)
- location_id (FK to locations)
- name (Bin 1A, South Bin, etc.)
- bin_number (physical label)
- device_id (ESP32 MAC address - UNIQUE)
- device_api_key (for authentication)
- capacity_bushels
- diameter_ft, height_ft
- bin_type (flat, hopper, etc.)
- is_online (true/false)
- last_seen (last data timestamp)
- current_crop_id (FK to crops)
- has_sht31, has_dht11, has_moisture_sensor, etc.
- alert_high_temp, alert_high_humidity
- alert_target_moisture
- created_at, updated_at
```

#### **3. sensor_readings**
```sql
- id (PK)
- bin_id (FK to bins) - INDEXED
- timestamp - INDEXED
- temp_sht31, temp_dht11, temp_avg
- humidity_sht31, humidity_dht11, humidity_avg
- grain_moisture
- airflow_cfm
- co2_ppm
- dew_point, heat_index
- esp32_uptime_sec
- wifi_rssi
- battery_voltage
```

### **Existing Tables (Modified):**
- **users** - Multi-location owners
- **simulations** - Now linked to specific bins
- **crops** - Shared across all locations
- **comments** - Can reference bins

---

## 🔌 API ENDPOINTS

### **ESP32 → Server (Data Upload)**

#### **POST /api/sensor/data**
```json
{
  "device_id": "A0:B1:C2:D3:E4:F5",
  "api_key": "bin-secret-key-xyz",
  "timestamp": "2026-01-11T12:00:00Z",
  "temp_sht31": 72.5,
  "temp_dht11": 73.0,
  "humidity_sht31": 45.2,
  "humidity_dht11": 46.0,
  "grain_moisture": 18.5,
  "airflow_cfm": 250,
  "wifi_rssi": -65,
  "uptime": 86400
}
```

**Response:**
```json
{
  "success": true,
  "bin_id": 5,
  "alerts": [
    {
      "type": "high_humidity",
      "message": "Humidity above threshold",
      "threshold": 70.0,
      "current": 46.0
    }
  ],
  "commands": {
    "fan_on": false,
    "heater_on": false,
    "interval_sec": 300
  }
}
```

#### **GET /api/sensor/config**
```
?device_id=A0:B1:C2:D3:E4:F5
```

**Response:**
```json
{
  "bin_id": 5,
  "bin_name": "Bin 1A",
  "location": "Farm A",
  "update_interval_sec": 300,
  "alert_thresholds": {
    "high_temp": 80.0,
    "high_humidity": 70.0,
    "target_moisture": 15.0
  },
  "sensors_enabled": {
    "sht31": true,
    "dht11": true,
    "moisture": true,
    "airflow": true
  }
}
```

### **Web Dashboard → Server**

#### **GET /api/locations**
```json
[
  {
    "id": 1,
    "name": "Farm A",
    "city": "Iowa City",
    "bin_count": 3,
    "online_bins": 2,
    "latitude": 41.6611,
    "longitude": -91.5302
  }
]
```

#### **GET /api/location/{id}/bins**
```json
[
  {
    "id": 1,
    "name": "Bin 1A",
    "is_online": true,
    "last_seen": "2026-01-11T12:05:00Z",
    "current_temp": 72.5,
    "current_humidity": 45.2,
    "current_moisture": 18.5,
    "current_crop": "Corn"
  }
]
```

#### **GET /api/bin/{id}/readings**
```
?start=2026-01-11T00:00:00Z&end=2026-01-11T23:59:59Z
```

**Response:** Array of sensor_readings

---

## 🖥️ WEB DASHBOARD FEATURES

### **1. Multi-Location Map View**
```
┌──────────────────────────────────────┐
│  🗺️  All Locations Map               │
│                                       │
│  📍 Farm A (3 bins, 2 online)        │
│  📍 Farm B (2 bins, 2 online)        │
│  📍 Silo C (5 bins, 4 online)        │
│                                       │
│  Total: 10 bins, 8 online            │
└──────────────────────────────────────┘
```

### **2. Location Dashboard**
```
┌──────────────────────────────────────┐
│  Farm A - Iowa City, IA              │
│                                       │
│  ┌─────┐  ┌─────┐  ┌─────┐          │
│  │Bin1A│  │Bin1B│  │Bin1C│          │
│  │ 🟢  │  │ 🟢  │  │ 🔴  │          │
│  │72°F │  │75°F │  │OFF  │          │
│  │45%RH│  │48%RH│  │---  │          │
│  │18%MC│  │16%MC│  │---  │          │
│  └─────┘  └─────┘  └─────┘          │
└──────────────────────────────────────┘
```

### **3. Individual Bin View**
```
┌──────────────────────────────────────┐
│  Bin 1A - Farm A                     │
│  🟢 Online - Last seen: 2 min ago    │
│                                       │
│  Current Readings:                   │
│  Temperature:  72.5°F                │
│  Humidity:     45.2%                 │
│  Moisture:     18.5%                 │
│  Airflow:      250 CFM               │
│                                       │
│  📈 Live Graph (24hr)                │
│  [Temperature/Humidity/Moisture]     │
│                                       │
│  ⚠️  Alerts:                         │
│  • Target moisture approaching       │
│  • Estimated 36 hours to 15%         │
└──────────────────────────────────────┘
```

### **4. Predictive Analytics**
```
┌──────────────────────────────────────┐
│  Bin 1A - Drying Prediction          │
│                                       │
│  Current: 18.5% moisture             │
│  Target:  15.0% moisture             │
│  Model:   Thompson (auto-calibrated) │
│                                       │
│  📊 Prediction:                      │
│  Time to target: 36 hours           │
│  Completion:     Jan 13, 2026 12:00  │
│  Energy cost:    $45 (estimated)     │
│                                       │
│  Confidence: 87% (based on 15 days)  │
└──────────────────────────────────────┘
```

---

## 📱 MOBILE NOTIFICATIONS

### **Alert Types:**
1. **Critical:**
   - Bin offline > 1 hour
   - Temperature > 100°F
   - Humidity > 80%
   - Sensor malfunction

2. **Important:**
   - Target moisture reached
   - Moisture not decreasing (stalled)
   - WiFi signal weak
   - Battery low

3. **Info:**
   - Daily summary
   - Weekly report
   - Maintenance reminder

### **Notification Channels:**
- Email
- SMS (Twilio)
- Push notifications (mobile app)
- In-app alerts

---

## 🔐 SECURITY

### **ESP32 Device Security:**
- Unique API key per bin
- HTTPS communication (TLS 1.2+)
- Certificate pinning
- Rate limiting (1 request/5 min max)

### **User Authentication:**
- Session-based login
- 10-minute inactivity timeout
- Password hashing (bcrypt)
- Multi-factor authentication (future)

### **Data Access Control:**
- Users see only their locations
- Admin sees all locations
- Location managers (future role)
- API key rotation

---

## 📈 IMPLEMENTATION PHASES

### **Phase 1: Foundation (Week 1-2)**
✅ Web app with user authentication
✅ Database schema for multi-site
□ ESP32 code for SHT31 + DHT11
□ Basic WiFi connectivity
□ POST sensor data to server

### **Phase 2: Core Integration (Week 3-4)**
□ Real-time dashboard for single bin
□ Location and bin management UI
□ Live sensor graphs
□ Basic alerts (email)
□ ESP32 OTA updates

### **Phase 3: Multi-Site (Week 5-6)**
□ Multiple locations support
□ Map view of all sites
□ Bulk bin registration
□ Advanced filtering/search
□ Comparative analytics

### **Phase 4: Intelligence (Week 7-8)**
□ Predictive model integration
□ Auto-calibration from real data
□ Machine learning improvements
□ Optimal stopping predictions
□ Cost optimization

### **Phase 5: Advanced Features (Week 9-10)**
□ Mobile app (React Native)
□ Automated control (fan/heater)
□ Multi-sensor fusion
□ Historical trend analysis
□ Export reports (PDF/Excel)

### **Phase 6: Scale & Polish (Week 11-12)**
□ Performance optimization
□ Database indexing
□ Caching layer (Redis)
□ Load balancing
□ Production deployment

---

## 💰 COST ESTIMATE

### **Hardware (Per Bin):**
- ESP32 C3 Super Mini: $3
- SHT31 sensor: $8
- DHT11 sensor: $2
- Moisture sensor: $15
- Enclosure + cables: $10
- **Total per bin: ~$40**

### **Hosting (Annual):**
- VPS (4GB RAM, 2 CPU): $60/year
- Domain name: $15/year
- SSL certificate: Free (Let's Encrypt)
- Database backup: $20/year
- **Total: ~$100/year**

### **For 20 Bins Across 4 Locations:**
- Hardware: 20 × $40 = $800
- Hosting: $100/year
- **Initial: $900, Annual: $100**

---

## 🚀 NEXT STEPS

### **What I need from you:**

1. **ESP8266 Code** - Share your existing code to port
2. **WiFi Details** - How will ESP32s connect? Same network? Different locations?
3. **Sensor Priorities** - Which sensors first? (SHT31 + DHT11 working, what next?)
4. **Hosting Preference** - Local server? Cloud (AWS, DigitalOcean, Heroku)?
5. **Number of Sites** - How many locations to start?

### **What I'll do next:**

1. Port your ESP8266 code to ESP32 C3
2. Add Location/Bin/SensorReading models to database
3. Create API endpoints for sensor data
4. Build location management UI
5. Create real-time monitoring dashboard

---

## 🎯 IMMEDIATE ACTION PLAN

**Today:**
1. You share ESP8266 code
2. I port to ESP32 C3 with SHT31 + DHT11
3. Test WiFi connection and data posting

**Tomorrow:**
4. Add sensor data API to web app
5. Create bin registration system
6. Test end-to-end data flow

**This Week:**
7. Build location management UI
8. Real-time dashboard for one bin
9. Basic alert system
10. Deploy to test server

---

**Ready to build this multi-site monitoring empire? Share your ESP8266 code and let's get started!** 🚀

