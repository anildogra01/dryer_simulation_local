#!/usr/bin/env python3
"""
Simple standalone Flask app for testing
No database, no components - just works!
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Simple in-memory data
data = {
    'metrics': {
        'total_users': 1250,
        'active_sessions': 42,
        'revenue': 15420.50,
        'conversion_rate': 3.2
    },
    'activities': [
        {'time': '10:30 AM', 'user': 'John Doe', 'action': 'Login', 'status': 'success'},
        {'time': '10:25 AM', 'user': 'Jane Smith', 'action': 'Purchase', 'status': 'success'},
        {'time': '10:20 AM', 'user': 'Bob Wilson', 'action': 'Signup', 'status': 'success'},
    ],
    'chart': {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'users': [120, 190, 150, 220, 180, 230, 200],
        'revenue': [1200, 1900, 1500, 2200, 1800, 2300, 2000]
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Dashboard</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .value { font-size: 32px; font-weight: bold; color: #667eea; }
        .label { color: #666; font-size: 14px; text-transform: uppercase; }
        .activity { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .activity-item { padding: 10px; border-left: 3px solid #667eea; margin: 10px 0; background: #f9f9f9; }
        button { background: #667eea; color: white; border: none; padding: 10px 20px; 
                border-radius: 5px; cursor: pointer; margin: 10px 0; }
        button:hover { background: #5568d3; }
        .status { padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px; }
        .success { background: #d1fae5; color: #065f46; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Simple Dashboard Test</h1>
        
        <div class="metrics">
            <div class="card">
                <div class="label">Total Users</div>
                <div class="value" id="totalUsers">-</div>
            </div>
            <div class="card">
                <div class="label">Active Sessions</div>
                <div class="value" id="activeSessions">-</div>
            </div>
            <div class="card">
                <div class="label">Revenue</div>
                <div class="value" id="revenue">-</div>
            </div>
            <div class="card">
                <div class="label">Conversion Rate</div>
                <div class="value" id="conversionRate">-</div>
            </div>
        </div>
        
        <button onclick="loadData()">🔄 Refresh Data</button>
        
        <div class="activity">
            <h2>Recent Activity</h2>
            <div id="activityList">Loading...</div>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                // Load metrics
                const metricsRes = await fetch('/api/metrics');
                const metrics = await metricsRes.json();
                
                document.getElementById('totalUsers').textContent = metrics.total_users;
                document.getElementById('activeSessions').textContent = metrics.active_sessions;
                document.getElementById('revenue').textContent = '$' + metrics.revenue;
                document.getElementById('conversionRate').textContent = metrics.conversion_rate + '%';
                
                // Load activities
                const activitiesRes = await fetch('/api/activities');
                const activities = await activitiesRes.json();
                
                document.getElementById('activityList').innerHTML = activities.map(a => 
                    `<div class="activity-item">
                        <strong>${a.user}</strong> - ${a.action} 
                        <span class="status success">${a.status}</span>
                        <small style="float:right">${a.time}</small>
                    </div>`
                ).join('');
                
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to load data: ' + error.message);
            }
        }
        
        // Load data on page load
        window.onload = loadData;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/metrics')
def get_metrics():
    return jsonify(data['metrics'])

@app.route('/api/activities')
def get_activities():
    return jsonify(data['activities'])

@app.route('/api/chart-data')
def get_chart_data():
    return jsonify(data['chart'])

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SIMPLE TEST SERVER STARTING")
    print("=" * 60)
    print()
    print("📍 Server: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000")
    print("🔌 Health Check: http://localhost:5000/health")
    print("📈 API Metrics: http://localhost:5000/api/metrics")
    print()
    print("Press CTRL+C to stop")
    print("=" * 60)
    print()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
