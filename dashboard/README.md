# Flask Dashboard - Local Setup

A simple and elegant analytics dashboard built with Flask and vanilla JavaScript.

## 📋 Features

- **Real-time Metrics**: Display key performance indicators
- **Interactive Charts**: Visual representation of data using Chart.js
- **Activity Feed**: Live feed of recent user activities
- **Auto-refresh**: Automatic data updates every 30 seconds
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: Clean API endpoints for data management

## 🚀 Quick Start

### Method 1: Using run_local.py (Recommended)

Simply run the automated setup script:

```bash
python run_local.py
```

This will:
- Check and install all dependencies
- Verify all required files exist
- Start the Flask development server

### Method 2: Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Application**
```bash
python app.py
```

3. **Open Your Browser**
Navigate to: `http://localhost:5000`

## 📁 Project Structure

```
.
├── app.py                  # Main Flask application
├── run_local.py           # Automated setup and run script
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Dashboard UI
└── README.md             # This file
```

## 🔌 API Endpoints

### GET Endpoints

- `GET /` - Dashboard homepage
- `GET /api/metrics` - Get current metrics
- `GET /api/activities` - Get recent activities
- `GET /api/chart-data` - Get chart data

### POST Endpoints

- `POST /api/update-metric` - Update a metric
  ```json
  {
    "name": "total_users",
    "value": 1500
  }
  ```

- `POST /api/add-activity` - Add new activity
  ```json
  {
    "user": "John Doe",
    "action": "Login",
    "status": "success"
  }
  ```

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

## 🛠️ Customization

### Changing the Port

Edit `app.py` or `run_local.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Modifying Metrics

Edit the `data_store` dictionary in `app.py`:
```python
data_store = {
    'metrics': {
        'your_metric': value,
        # Add more metrics
    }
}
```

### Styling

The dashboard uses inline CSS in `dashboard.html`. Modify the `<style>` section to customize:
- Colors
- Layout
- Fonts
- Animations

## 🔒 Security Notes

This is a **development server** for local use. For production:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Add authentication and authorization
3. Use a real database (PostgreSQL, MongoDB)
4. Enable HTTPS
5. Add rate limiting
6. Implement proper error handling
7. Add input validation and sanitization

## 📊 Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **CORS**: Flask-CORS

## 🐛 Troubleshooting

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
