"""
WSGI Configuration for PythonAnywhere

This file configures how to mount multiple Flask applications.
Place this content in your PythonAnywhere WSGI configuration file.

Instructions:
1. Go to PythonAnywhere Web tab
2. Click on WSGI configuration file link
3. Add the dryer dashboard configuration below your existing app
"""

import sys
from pathlib import Path

# ============================================================================
# EXISTING APPLICATION (Your current Flask app)
# ============================================================================
# Keep your existing configuration here
# Example:
# path = '/home/YOUR_USERNAME/mysite'
# if path not in sys.path:
#     sys.path.insert(0, path)
# 
# from flask_app import app as existing_application

# ============================================================================
# DRYER SIMULATION DASHBOARD (New application)
# ============================================================================

# Add dryer simulation path
dryer_path = '/home/YOUR_USERNAME/dryer_simulation'
if dryer_path not in sys.path:
    sys.path.insert(0, dryer_path)

# Import dryer dashboard
from dryer_dashboard_pythonanywhere import application as dryer_application

# ============================================================================
# MOUNT MULTIPLE APPLICATIONS
# ============================================================================

from werkzeug.middleware.dispatcher import DispatcherMiddleware

# If you have an existing application, mount both:
# application = DispatcherMiddleware(existing_application, {
#     '/dryer': dryer_application
# })

# If this is your only application:
application = dryer_application

# ============================================================================
# URL ROUTING
# ============================================================================
# 
# Option 1: Separate subdomain
#   - existing_app.pythonanywhere.com → Your existing app
#   - dryer.pythonanywhere.com → Dryer dashboard
#   (Requires separate PythonAnywhere web app)
#
# Option 2: Sub-path (recommended for single app)
#   - yourusername.pythonanywhere.com → Your existing app
#   - yourusername.pythonanywhere.com/dryer → Dryer dashboard
#   (Use DispatcherMiddleware as shown above)
#
# Option 3: Replace existing (if no other app)
#   - yourusername.pythonanywhere.com → Dryer dashboard only
#   (Use application = dryer_application)
#
# ============================================================================

# Example: Mount dryer dashboard at /dryer path
# Uncomment and modify this section if you have an existing Flask app

"""
# Import your existing app
from your_existing_app import app as main_app

# Mount both applications
application = DispatcherMiddleware(main_app, {
    '/dryer': dryer_application
})

# Now accessible at:
# - yourusername.pythonanywhere.com → main_app
# - yourusername.pythonanywhere.com/dryer → dryer_application
"""
