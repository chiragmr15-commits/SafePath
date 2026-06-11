import urllib.request
import json

url = 'https://router.project-osrm.org/route/v1/driving/77.5946,12.9716;77.6340,12.9923?overview=full&geometries=geojson&alternatives=true'

try:
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Code: {data.get('code')}")
        print(f"Routes returned: {len(data.get('routes', []))}")
        if data.get('routes'):
            for i, route in enumerate(data['routes']):
                print(f"  Route {i}: distance={route.get('distance')}m, duration={route.get('duration')}s")
except Exception as e:
    print(f"Error: {e}")
