"""
Quick diagnostic - tests if the server is returning JSON properly
"""

import requests
import sys

print("=" * 60)
print("GRAIN DRYER API DIAGNOSTICS")
print("=" * 60)

# Test 1: Server running?
print("\n1. Testing if server is running...")
try:
    response = requests.get('http://localhost:5000/', timeout=5)
    print("   ✅ Server is running")
except Exception as e:
    print(f"   ❌ Server not running: {e}")
    print("\n   Please start the server with: python run_local.py")
    sys.exit(1)

# Test 2: API test endpoint
print("\n2. Testing API test endpoint...")
try:
    response = requests.get('http://localhost:5000/api/test', timeout=5)
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API working: {data.get('message')}")
    else:
        print(f"   ❌ Unexpected status code")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get crops
print("\n3. Testing crops endpoint...")
try:
    response = requests.get('http://localhost:5000/api/crops', timeout=5)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        crops = response.json()
        print(f"   ✅ Got {len(crops)} crops")
        if crops:
            print(f"   Example: {crops[0]['name']}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Simulate with minimal data
print("\n4. Testing simulation endpoint...")
try:
    test_data = {
        'crop_id': '1',
        'model_type': 'exponential',
        'processing_method': 'regular',
        'initial_moisture': '25',
        'target_moisture': '15',
        'grain_temp': '70',
        'air_temp': '110',
        'air_rh': '30',
        'air_flow_rate': '500',
        'dryer_width': '10',
        'dryer_length': '20',
        'bed_depth': '2'
    }
    
    print("   Sending simulation request...")
    response = requests.post(
        'http://localhost:5000/api/simulate',
        json=test_data,
        timeout=30
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    
    # Check if it's JSON
    content_type = response.headers.get('content-type', '')
    if 'application/json' in content_type:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ Simulation successful!")
            print(f"   Simulation ID: {result.get('simulation_id')}")
        else:
            print(f"   ❌ Simulation failed")
            print(f"   Error: {result.get('error')}")
            if 'validation_errors' in result:
                print(f"   Validation errors:")
                for err in result['validation_errors']:
                    print(f"      - {err}")
    else:
        print(f"   ❌ Server returned HTML instead of JSON")
        print(f"\n   Response preview:")
        print(f"   {response.text[:500]}")
        print("\n   Check Python terminal for error details!")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTICS COMPLETE")
print("=" * 60)
