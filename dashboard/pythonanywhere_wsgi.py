import sys
import os

# Path to your project on PythonAnywhere
path = '/home/akdsmartgrow/dryer_simulation_local/dashboard'
if path not in sys.path:
    sys.path.insert(0, path)

# Set working directory
os.chdir(path)

from app import app as application
