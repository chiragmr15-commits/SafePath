import urllib.request
import json

# Bengaluru Airport to Mysore Palace
url = 'http://127.0.0.1:8000/api/route-geometry/?start_lat=13.1939&start_lon=77.7064&end_lat=12.2958&end_lon=76.8394'

try:
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Success: {data.get('success')}")
        print(f"Routes returned: {len(data.get('routes', []))}")
        if data.get('routes'):
            for i, route in enumerate(data['routes']):
                print(f"  Route {i}: id={route.get('id')}, distance={route.get('distance_km')}km, safety={route.get('safety_score')}, zones={route.get('total_zones')}")
        print(f"Recommended: {data.get('recommended_route_id')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
