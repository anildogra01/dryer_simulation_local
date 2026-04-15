# Get line count
lines=$(wc -l < dryer_dashboard_pythonanywhere.py)
# Remove last 9 lines (the broken section)
head -n -9 dryer_dashboard_pythonanywhere.py > temp.py
# Add correct ending
cat >> temp.py << 'ENDFILE'

# For local testing
if __name__ == '__main__':
    print("=" * 70)
    print("  GRAIN DRYER DASHBOARD - PythonAnywhere Version")
    print("=" * 70)
    print("\nStarting local test server...")
    print("Open browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    application.run(debug=True, host='0.0.0.0', port=5000)
ENDFILE
# Replace original
mv temp.py dryer_dashboard_pythonanywhere.py
echo "✅ Fixed!"
