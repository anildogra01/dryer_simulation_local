"""
Minimal test - Does crop_master route work at all?
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Home works!</h1><a href='/crop_master'>Go to Crop Master</a>"

@app.route('/crop_master')
def crop_master():
    return "<h1>Crop Master works!</h1><a href='/'>Go Home</a>"

if __name__ == '__main__':
    print("="*70)
    print("MINIMAL TEST APP")
    print("="*70)
    print("Routes registered:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule}")
    print("="*70)
    print("Open: http://127.0.0.1:5001/")
    print("Test: http://127.0.0.1:5001/crop_master")
    print("="*70)
    app.run(debug=True, port=5001)
