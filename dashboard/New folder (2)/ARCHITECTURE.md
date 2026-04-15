# 🏗️ Dashboard Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                     http://localhost:5000                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP Requests
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FLASK APPLICATION                       │
│                         (app.py)                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    ROUTES                             │  │
│  │  GET  /                    → dashboard.html          │  │
│  │  GET  /api/metrics         → JSON response           │  │
│  │  GET  /api/activities      → JSON response           │  │
│  │  GET  /api/chart-data      → JSON response           │  │
│  │  POST /api/update-metric   → Update DB               │  │
│  │  POST /api/add-activity    → Insert DB               │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ▲                               │
│                              │ SQLAlchemy ORM               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  DATABASE LAYER                       │  │
│  │                   (database.py)                       │  │
│  │                                                       │  │
│  │   Models:                                            │  │
│  │   • Metric       → Stores dashboard metrics          │  │
│  │   • Activity     → Stores user activities            │  │
│  │   • ChartData    → Stores chart data points          │  │
│  │   • User         → Stores user information           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ SQLite
                              ▼
                    ┌─────────────────┐
                    │  dashboard.db   │
                    │  (SQLite File)  │
                    └─────────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DASHBOARD.HTML                          │
│                      (Main Template)                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  {% include 'components/header.html' %}                │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  📊 Analytics Dashboard                          │  │ │
│  │  │  Real-time monitoring and insights               │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  {% include 'components/metrics.html' %}               │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │ │
│  │  │ Users  │ │Sessions│ │Revenue │ │Convert │          │ │
│  │  │  1,250 │ │   42   │ │$15,420 │ │  3.2%  │          │ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │ {% include           │  │ {% include                   │ │
│  │ 'components/         │  │ 'components/                 │ │
│  │ chart.html' %}       │  │ activity_feed.html' %}       │ │
│  │                      │  │                              │ │
│  │ ┌──────────────────┐ │  │ ┌──────────────────────────┐ │ │
│  │ │  Weekly Chart    │ │  │ │  Recent Activities       │ │ │
│  │ │  [Line Graph]    │ │  │ │  • John Doe - Login      │ │ │
│  │ │                  │ │  │ │  • Jane Smith - Purchase │ │ │
│  │ └──────────────────┘ │  │ │  • Bob Wilson - Signup   │ │ │
│  └──────────────────────┘  │ └──────────────────────────┘ │ │
│                            └──────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  <style>                                               │ │
│  │  {% include 'components/styles.css' %}                 │ │
│  │  </style>                                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  <script>                                              │ │
│  │  {% include 'components/scripts.js' %}                 │ │
│  │  </script>                                             │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Loading Dashboard

```
User Browser
    │
    ├─→ GET /
    │      │
    │      ▼
    │   Flask renders dashboard.html
    │      │
    │      ├─→ Includes header.html
    │      ├─→ Includes metrics.html
    │      ├─→ Includes chart.html
    │      ├─→ Includes activity_feed.html
    │      ├─→ Includes styles.css
    │      └─→ Includes scripts.js
    │      │
    │      ▼
    │   Returns complete HTML
    │      │
    ◄──────┘
    │
    ├─→ JavaScript loads (scripts.js)
    │      │
    │      ├─→ GET /api/metrics
    │      │      │
    │      │      ▼
    │      │   Query Metric table
    │      │      │
    │      ◄──────┘ Return JSON
    │      │
    │      ├─→ GET /api/activities
    │      │      │
    │      │      ▼
    │      │   Query Activity table
    │      │      │
    │      ◄──────┘ Return JSON
    │      │
    │      └─→ GET /api/chart-data
    │             │
    │             ▼
    │          Query ChartData table
    │             │
    ◄─────────────┘ Return JSON
    │
    └─→ Render data in browser
```

### 2. Updating Data

```
User clicks "Refresh"
    │
    └─→ JavaScript: refreshData()
           │
           ├─→ GET /api/metrics
           │      │
           │      ▼
           │   database.py: Metric.query.all()
           │      │
           │      ▼
           │   dashboard.db: SELECT * FROM metrics
           │      │
           ◄──────┘ JSON Response
           │
           ├─→ GET /api/activities
           │      │
           │      ▼
           │   database.py: Activity.query.order_by()
           │      │
           │      ▼
           │   dashboard.db: SELECT * FROM activities
           │      │
           ◄──────┘ JSON Response
           │
           └─→ Update DOM with new data
```

### 3. Adding Activity

```
API Call: POST /api/add-activity
    │
    ├─→ app.py receives request
    │      │
    │      ▼
    │   Create Activity object
    │      │
    │      ▼
    │   database.py: db.session.add()
    │      │
    │      ▼
    │   database.py: db.session.commit()
    │      │
    │      ▼
    │   dashboard.db: INSERT INTO activities
    │      │
    │      ▼
    │   Return success JSON
    │      │
    ◄──────┘
```

## File Dependencies

```
run_local.py
    ├─→ Imports app.py
    └─→ Checks requirements.txt

app.py
    ├─→ Imports database.py
    ├─→ Imports Flask, flask_cors
    └─→ Uses templates/dashboard.html

database.py
    ├─→ Imports Flask-SQLAlchemy
    └─→ Creates dashboard.db

dashboard.html
    ├─→ Includes components/header.html
    ├─→ Includes components/metrics.html
    ├─→ Includes components/chart.html
    ├─→ Includes components/activity_feed.html
    ├─→ Includes components/styles.css
    └─→ Includes components/scripts.js

db_manager.py
    ├─→ Imports app.py
    └─→ Imports database.py
```

## Key Benefits of This Architecture

1. **Modularity**: Components are separated and reusable
2. **Maintainability**: Easy to update individual parts
3. **Scalability**: Can add new components without touching core
4. **Testability**: Each layer can be tested independently
5. **Clarity**: Clear separation of concerns (MVC pattern)

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Chart.js
- **Backend**: Flask (Python), SQLAlchemy
- **Database**: SQLite
- **Template Engine**: Jinja2
- **API**: RESTful JSON endpoints
