# Flask Dashboard - Local Setup with Database

A modular, component-based analytics dashboard built with Flask, SQLite, and vanilla JavaScript.

## 🌟 Features

- **SQLite Database**: Persistent data storage with SQLAlchemy ORM
- **Modular Components**: Reusable HTML/CSS/JS components
- **Real-time Metrics**: Display key performance indicators
- **Interactive Charts**: Visual representation using Chart.js
- **Activity Feed**: Live feed of user activities
- **Auto-refresh**: Automatic data updates every 30 seconds
- **Responsive Design**: Works on desktop and mobile
- **RESTful API**: Clean API endpoints for data management
- **Database Manager**: CLI tool for database operations

## 📁 Project Structure

```
.
├── app.py                      # Main Flask application
├── database.py                 # Database models and configuration
├── db_manager.py              # Database management utility
├── run_local.py               # Automated setup and run script
├── requirements.txt           # Python dependencies
├── templates/
│   ├── dashboard.html         # Main dashboard (uses components)
│   └── components/            # Modular components
│       ├── header.html        # Header component
│       ├── metrics.html       # Metrics grid component
│       ├── chart.html         # Chart component
│       ├── activity_feed.html # Activity feed component
│       ├── styles.css         # Shared styles
│       └── scripts.js         # Shared JavaScript
├── dashboard.db               # SQLite database (created on first run)
└── README.md                  # This file
```

## 🚀 Quick Start

### Method 1: Using run_local.py (Recommended)

Simply run the automated setup script:

```bash
python run_local.py
```

This will:
- Check and install all dependencies
- Initialize the database
- Seed with sample data
- Start the Flask development server

### Method 2: Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Initialize Database**
```bash
python db_manager.py init
python db_manager.py seed
```

3. **Run the Application**
```bash
python app.py
```

4. **Open Your Browser**
Navigate to: `http://localhost:5000`

## 🗄️ Database Management

The `db_manager.py` utility provides easy database management:

```bash
# Initialize database tables
python db_manager.py init

# Seed with sample data
python db_manager.py seed

# Show database information
python db_manager.py info

# Clear all data
python db_manager.py clear

# Backup database
python db_manager.py backup

# Export data to JSON
python db_manager.py export

# Show help
python db_manager.py help
```

## 🧩 Component Architecture

The dashboard uses a modular component system:

### Components

1. **header.html** - Dashboard header and title
2. **metrics.html** - Metrics cards grid
3. **chart.html** - Performance chart container
4. **activity_feed.html** - Recent activity list
5. **styles.css** - Shared CSS styles
6. **scripts.js** - Shared JavaScript functions

### How It Works

The main `dashboard.html` includes components using Jinja2 templating:

```html
{% include 'components/header.html' %}
{% include 'components/metrics.html' %}
```

This makes the code:
- **Maintainable**: Edit components independently
- **Reusable**: Use components across multiple pages
- **Organized**: Clear separation of concerns

## 🔌 API Endpoints

### GET Endpoints

- `GET /` - Dashboard homepage
- `GET /api/metrics` - Get current metrics from database
- `GET /api/activities` - Get recent activities from database
- `GET /api/chart-data` - Get chart data from database

### POST Endpoints

- `POST /api/update-metric` - Update a metric in database
  ```json
  {
    "name": "total_users",
    "value": 1500
  }
  ```

- `POST /api/add-activity` - Add new activity to database
  ```json
  {
    "user": "John Doe",
    "action": "Login",
    "status": "success"
  }
  ```

## 💾 Database Schema

### Tables

**Metric** - Dashboard metrics
- id (Integer, Primary Key)
- name (String, Unique)
- value (Float)
- unit (String)
- updated_at (DateTime)

**Activity** - User activities
- id (Integer, Primary Key)
- user (String)
- action (String)
- status (String)
- timestamp (DateTime)
- metadata (JSON Text)

**ChartData** - Chart data points
- id (Integer, Primary Key)
- label (String)
- users (Integer)
- revenue (Float)
- date (Date)

**User** - User information
- id (Integer, Primary Key)
- username (String, Unique)
- email (String, Unique)
- created_at (DateTime)
- last_login (DateTime)
- is_active (Boolean)

## 💡 Usage Examples

### Testing the API with curl

**Get Metrics:**
```bash
curl http://localhost:5000/api/metrics
```

**Update a Metric:**
```bash
curl -X POST http://localhost:5000/api/update-metric \
  -H "Content-Type: application/json" \
  -d '{"name": "total_users", "value": 2000}'
```

**Add Activity:**
```bash
curl -X POST http://localhost:5000/api/add-activity \
  -H "Content-Type: application/json" \
  -d '{"user": "Alice", "action": "Purchase", "status": "success"}'
```

### Python Examples

```python
import requests

# Get metrics
response = requests.get('http://localhost:5000/api/metrics')
metrics = response.json()

# Update metric
requests.post('http://localhost:5000/api/update-metric', 
              json={'name': 'revenue', 'value': 20000})

# Add activity
requests.post('http://localhost:5000/api/add-activity',
              json={'user': 'Bob', 'action': 'Login', 'status': 'success'})
```

## 🛠️ Customization

### Adding New Components

1. Create a new HTML file in `templates/components/`
2. Include it in `dashboard.html`:
   ```html
   {% include 'components/your_component.html' %}
   ```

### Adding New Database Models

1. Define model in `database.py`:
   ```python
   class YourModel(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       # Add fields...
   ```

2. Create migration:
   ```bash
   python db_manager.py init
   ```

### Modifying Styles

Edit `templates/components/styles.css` to change:
- Colors
- Layout
- Fonts
- Animations

All pages using the component will update automatically!

## 🔒 Security Notes

This is a **development server** for local use. For production:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Change SECRET_KEY in app.py
3. Add authentication and authorization
4. Use PostgreSQL/MySQL instead of SQLite
5. Enable HTTPS
6. Add rate limiting
7. Implement proper error handling
8. Add input validation and sanitization
9. Use environment variables for configuration

## 📊 Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **CORS**: Flask-CORS
- **Templating**: Jinja2

## 🐛 Troubleshooting

**Database errors:**
```bash
# Reset database
python db_manager.py clear
python db_manager.py seed
```

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
```

**Dependencies not installing:**
```bash
# Upgrade pip
pip install --upgrade pip
# Install with verbose output
pip install -r requirements.txt -v
```

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to fork, modify, and enhance this dashboard for your needs!
