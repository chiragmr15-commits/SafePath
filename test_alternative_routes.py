#!/usr/bin/env python3
"""
Test script to verify alternative routes are being returned and displayed correctly.
Tests the complete flow: API request -> Multiple routes -> Route analysis -> Response
"""

import requests
import json
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://127.0.0.1:8000"

def test_route_finding():
    """Test the route finding API with multiple route alternatives"""
    
    print("\n" + "="*70)
    print("🧪 TESTING ALTERNATIVE ROUTES - MULTIPLE ROUTE FINDING")
    print("="*70)
    
    # Test case 1: New Delhi to Mumbai (long distance - should have multiple alternatives)
    print("\n📍 Test Case 1: New Delhi to Mumbai")
    print("-" * 70)
    
    params = {
        'start_lat': 28.7041,    # Delhi
        'start_lon': 77.1025,
        'end_lat': 19.0760,      # Mumbai
        'end_lon': 72.8777
    }
    
    url = f"{BASE_URL}/api/route-geometry/"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        print(f"✅ API Response Status: {response.status_code}")
        print(f"✅ Response Valid: {data.get('success', False)}")
        
        if data.get('success'):
            routes = data.get('routes', [])
            print(f"\n🛣️  ROUTES RETURNED: {len(routes)}")
            
            if len(routes) < 2:
                print("❌ ERROR: Expected at least 2 routes (alternatives), got {}".format(len(routes)))
                return False
            
            print("✅ Multiple routes found!")
            
            # Analyze each route
            print("\n📊 ROUTE ANALYSIS:")
            print("-" * 70)
            
            for idx, route in enumerate(routes):
                print(f"\n  Route {idx}:")
                print(f"    • ID: {route.get('id')}")
                print(f"    • Distance: {route.get('distance_km')} km")
                print(f"    • Time: {route.get('estimated_time_minutes')} minutes")
                print(f"    • Safety Score: {route.get('safety_score')}%")
                print(f"    • Safety Level: {route.get('safety_level')}")
                print(f"    • Danger Zones: {route.get('total_zones')}")
                print(f"    • Points: {len(route.get('route', []))} coordinates")
            
            # Check recommended route
            recommended_id = data.get('recommended_route_id')
            print(f"\n🎯 RECOMMENDED ROUTE ID: {recommended_id}")
            
            if data.get('safer_alternative_recommended'):
                print(f"⭐ SAFER ALTERNATIVE RECOMMENDED")
                print(f"   Reason: {data.get('safer_recommendation_reason')}")
            
            # Verify all routes have coordinates
            print("\n✅ COORDINATE VERIFICATION:")
            all_valid = True
            for idx, route in enumerate(routes):
                coords = route.get('route', [])
                if len(coords) < 2:
                    print(f"  ❌ Route {idx}: Invalid coordinates ({len(coords)} points)")
                    all_valid = False
                else:
                    print(f"  ✅ Route {idx}: {len(coords)} coordinate pairs")
            
            if not all_valid:
                return False
            
            print("\n" + "="*70)
            print("✅ TEST PASSED: Alternative routes working correctly!")
            print("="*70)
            return True
        else:
            print(f"❌ API Error: {data.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - server may not be running")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not reachable at {}".format(BASE_URL))
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_short_distance():
    """Test with shorter distance (local routes)"""
    
    print("\n" + "="*70)
    print("🧪 TEST CASE 2: Short Distance Routes")
    print("="*70)
    
    # Bangalore local routes
    params = {
        'start_lat': 12.9352,     # Central Bangalore
        'start_lon': 77.6245,
        'end_lat': 12.9716,       # Different part of Bangalore
        'end_lon': 77.5946
    }
    
    url = f"{BASE_URL}/api/route-geometry/"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get('success'):
            routes = data.get('routes', [])
            print(f"✅ Routes found: {len(routes)}")
            
            for idx, route in enumerate(routes):
                print(f"  Route {idx}: {route.get('distance_km')} km, Safety: {route.get('safety_score')}%")
            
            return len(routes) >= 1
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("\n🚀 ALTERNATIVE ROUTES TESTING SUITE")
    print("Testing route finding with multiple alternatives\n")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except:
        print(f"❌ Server not running at {BASE_URL}")
        print("Please start the Django server with: python manage.py runserver")
        sys.exit(1)
    
    # Run tests
    test1_passed = test_route_finding()
    test2_passed = test_short_distance()
    
    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)
    print(f"Long Distance Routes: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Short Distance Routes: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED - Alternative routes are working!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Check the errors above")
        sys.exit(1)
