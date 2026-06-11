import json
import math
import re
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from .models import UnsafeZone, CommunityReport, EmergencyContact, SOSAlert, SOSDeliveryLog, RouteHistory, UserPreferences

DEFAULT_ZONES = [
    {
        'name': 'Downtown Red Zone',
        'latitude': 12.9716,
        'longitude': 77.5946,
        'radius': 500,
    },
    {
        'name': 'Neighborhood Danger',
        'latitude': 12.9352,
        'longitude': 77.6245,
        'radius': 450,
    },
    {
        'name': 'Market Unsafe Zone',
        'latitude': 12.9923,
        'longitude': 77.6340,
        'radius': 420,
    },
]


def home(request):
    return render(request, 'index.html')

def navigation(request):
    return render(request, 'navigation.html')

def safety_zones(request):
    return render(request, 'safety_zones.html')

def guardian(request):
    return render(request, 'guardian.html')

def reports(request):
    return render(request, 'reports.html')


@login_required(login_url='login')
def emergency_contacts(request):
    """Emergency Contacts management page"""
    return render(request, 'emergency_contacts.html')


def ensure_default_zones():
    if UnsafeZone.objects.exists():
        return

    for zone_data in DEFAULT_ZONES:
        UnsafeZone.objects.create(**zone_data)


@require_http_methods(['GET'])
def api_zones(request):
    ensure_default_zones()
    zones = list(
        UnsafeZone.objects.values('id', 'name', 'latitude', 'longitude', 'radius')
    )
    return JsonResponse({'zones': zones})


@csrf_exempt
@require_http_methods(['POST'])
def api_report(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        latitude = float(body.get('latitude'))
        longitude = float(body.get('longitude'))
        radius = int(body.get('radius', 450))
        name = body.get('name', 'Reported Unsafe Zone')
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest('Invalid JSON payload')

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and radius > 0):
        return HttpResponseBadRequest('Invalid location or radius values')

    zone = UnsafeZone.objects.create(
        name=name,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
    )
    return JsonResponse(
        {
            'id': zone.id,
            'name': zone.name,
            'latitude': zone.latitude,
            'longitude': zone.longitude,
            'radius': zone.radius,
        }
    )


# ================ COMMUNITY REPORTS API ================

@require_http_methods(['GET', 'POST'])
@csrf_exempt
def api_community_reports(request):
    """
    GET: List all community reports
    POST: Create a new community report
    """
    if request.method == 'GET':
        reports = CommunityReport.objects.all().values(
            'id', 'title', 'description', 'severity', 
            'latitude', 'longitude', 'is_verified', 'created_at'
        )
        return JsonResponse({'reports': list(reports)})
    
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            title = body.get('title', '').strip()
            description = body.get('description', '').strip()
            severity = body.get('severity', 'medium').lower()
            latitude = float(body.get('latitude'))
            longitude = float(body.get('longitude'))
            
            if not title or not description:
                return HttpResponseBadRequest('Title and description are required')
            
            if severity not in ['low', 'medium', 'high', 'critical']:
                return HttpResponseBadRequest('Invalid severity level')
            
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return HttpResponseBadRequest('Invalid coordinates')
            
            report = CommunityReport.objects.create(
                user=request.user if request.user.is_authenticated else None,
                title=title,
                description=description,
                severity=severity,
                latitude=latitude,
                longitude=longitude,
            )
            
            return JsonResponse({
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'severity': report.severity,
                'latitude': report.latitude,
                'longitude': report.longitude,
                'is_verified': report.is_verified,
                'created_at': report.created_at.isoformat(),
            }, status=201)
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return HttpResponseBadRequest(f'Invalid request: {str(e)}')


@require_http_methods(['DELETE', 'PATCH'])
@csrf_exempt
def api_community_report_detail(request, report_id):
    """
    DELETE: Delete a report (admin only)
    PATCH: Verify/update a report (admin only)
    """
    try:
        report = CommunityReport.objects.get(id=report_id)
    except CommunityReport.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    
    if request.method == 'DELETE':
        if not request.user.is_staff:
            return HttpResponseForbidden('Only admins can delete reports')
        
        report.delete()
        return JsonResponse({'message': 'Report deleted successfully'})
    
    elif request.method == 'PATCH':
        if not request.user.is_staff:
            return HttpResponseForbidden('Only admins can modify reports')
        
        try:
            body = json.loads(request.body.decode('utf-8'))
            
            if 'is_verified' in body:
                report.is_verified = bool(body.get('is_verified'))
            
            if 'severity' in body:
                severity = body.get('severity', '').lower()
                if severity in ['low', 'medium', 'high', 'critical']:
                    report.severity = severity
            
            report.save()
            
            return JsonResponse({
                'id': report.id,
                'title': report.title,
                'severity': report.severity,
                'is_verified': report.is_verified,
                'latitude': report.latitude,
                'longitude': report.longitude,
                'created_at': report.created_at.isoformat(),
            })
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return HttpResponseBadRequest(f'Invalid request: {str(e)}')


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_point_in_circle(point_lat, point_lon, circle_lat, circle_lon, radius_meters):
    """Check if a point is within a circle"""
    distance = calculate_distance(point_lat, point_lon, circle_lat, circle_lon)
    return distance <= radius_meters


def line_circle_intersection(p1_lat, p1_lon, p2_lat, p2_lon, center_lat, center_lon, radius_meters):
    """Check if a line segment intersects with a circle"""
    # Check if either endpoint is in the circle
    if is_point_in_circle(p1_lat, p1_lon, center_lat, center_lon, radius_meters):
        return True
    if is_point_in_circle(p2_lat, p2_lon, center_lat, center_lon, radius_meters):
        return True
    
    # Check closest point on line to circle center
    dx = p2_lon - p1_lon
    dy = p2_lat - p1_lat
    
    if dx == 0 and dy == 0:
        return False
    
    t = max(0, min(1, (
        (center_lon - p1_lon) * dx + (center_lat - p1_lat) * dy
    ) / (dx * dx + dy * dy)))
    
    closest_lon = p1_lon + t * dx
    closest_lat = p1_lat + t * dy
    
    return is_point_in_circle(closest_lat, closest_lon, center_lat, center_lon, radius_meters)


@require_http_methods(['POST'])
@csrf_exempt
def api_route_analysis(request):
    """
    Analyze a route for danger zones
    POST body: {
        "route": [[lat1, lon1], [lat2, lon2], ...],
        "start_lat": float,
        "start_lon": float,
        "end_lat": float,
        "end_lon": float
    }
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        route = body.get('route', [])
        start_lat = float(body.get('start_lat'))
        start_lon = float(body.get('start_lon'))
        end_lat = float(body.get('end_lat'))
        end_lon = float(body.get('end_lon'))
        
        if not route or len(route) < 2:
            return HttpResponseBadRequest('Route with at least 2 points is required')
        
        # Get all community reports
        reports = CommunityReport.objects.all()
        
        # Severity to radius and penalty mapping
        severity_config = {
            'low': {'radius': 100, 'penalty': 5},
            'medium': {'radius': 250, 'penalty': 10},
            'high': {'radius': 400, 'penalty': 20},
            'critical': {'radius': 600, 'penalty': 30},
        }
        
        intersecting_zones = []
        total_penalty = 0
        high_count = 0
        critical_count = 0
        
        # Check each report for route intersection
        for report in reports:
            config = severity_config.get(report.severity, severity_config['medium'])
            radius = config['radius']
            penalty = config['penalty']
            
            # Check route line segments for intersection
            route_intersects = False
            for i in range(len(route) - 1):
                p1 = route[i]
                p2 = route[i + 1]
                
                if line_circle_intersection(p1[0], p1[1], p2[0], p2[1], 
                                          report.latitude, report.longitude, radius):
                    route_intersects = True
                    break
            
            if route_intersects:
                intersecting_zones.append({
                    'id': report.id,
                    'title': report.title,
                    'description': report.description,
                    'severity': report.severity,
                    'latitude': report.latitude,
                    'longitude': report.longitude,
                    'radius': radius,
                    'is_verified': report.is_verified,
                })
                total_penalty += penalty
                
                if report.severity == 'high':
                    high_count += 1
                elif report.severity == 'critical':
                    critical_count += 1
        
        # Calculate safety score
        safety_score = max(0, 100 - total_penalty)
        
        # Determine safety level
        if safety_score >= 80:
            safety_level = 'Safe'
            badge_color = 'green'
        elif safety_score >= 50:
            safety_level = 'Moderate'
            badge_color = 'yellow'
        else:
            safety_level = 'Unsafe'
            badge_color = 'red'
        
        return JsonResponse({
            'intersecting_zones': intersecting_zones,
            'total_zones': len(intersecting_zones),
            'high_severity_zones': high_count,
            'critical_severity_zones': critical_count,
            'safety_score': safety_score,
            'safety_level': safety_level,
            'badge_color': badge_color,
            'total_penalty': total_penalty,
        })
    
    except (ValueError, TypeError, json.JSONDecodeError, KeyError) as e:
        return HttpResponseBadRequest(f'Invalid request: {str(e)}')


def analyze_route_safety(route_coords, start_lat, start_lon, end_lat, end_lon):
    """
    Analyze a single route for safety metrics.
    Returns safety analysis including intersecting zones and safety score.
    """
    try:
        # Get all community reports
        reports = CommunityReport.objects.all()
        
        # Severity to radius and penalty mapping
        severity_config = {
            'low': {'radius': 100, 'penalty': 5},
            'medium': {'radius': 250, 'penalty': 10},
            'high': {'radius': 400, 'penalty': 20},
            'critical': {'radius': 600, 'penalty': 30},
        }
        
        intersecting_zones = []
        total_penalty = 0
        high_count = 0
        critical_count = 0
        
        # Check each report for route intersection
        for report in reports:
            config = severity_config.get(report.severity, severity_config['medium'])
            radius = config['radius']
            penalty = config['penalty']
            
            # Check route line segments for intersection
            route_intersects = False
            for i in range(len(route_coords) - 1):
                p1 = route_coords[i]
                p2 = route_coords[i + 1]
                
                if line_circle_intersection(p1[0], p1[1], p2[0], p2[1], 
                                          report.latitude, report.longitude, radius):
                    route_intersects = True
                    break
            
            if route_intersects:
                intersecting_zones.append({
                    'id': report.id,
                    'title': report.title,
                    'description': report.description,
                    'severity': report.severity,
                    'latitude': report.latitude,
                    'longitude': report.longitude,
                    'radius': radius,
                    'is_verified': report.is_verified,
                })
                total_penalty += penalty
                
                if report.severity == 'high':
                    high_count += 1
                elif report.severity == 'critical':
                    critical_count += 1
        
        # Calculate safety score
        safety_score = max(0, 100 - total_penalty)
        
        # Determine safety level
        if safety_score >= 80:
            safety_level = 'Safe'
            badge_color = 'green'
        elif safety_score >= 50:
            safety_level = 'Moderate'
            badge_color = 'yellow'
        else:
            safety_level = 'Unsafe'
            badge_color = 'red'
        
        return {
            'intersecting_zones': intersecting_zones,
            'total_zones': len(intersecting_zones),
            'high_severity_zones': high_count,
            'critical_severity_zones': critical_count,
            'safety_score': safety_score,
            'safety_level': safety_level,
            'badge_color': badge_color,
            'total_penalty': total_penalty,
        }
    
    except Exception as e:
        # Return default safe analysis if error occurs
        return {
            'intersecting_zones': [],
            'total_zones': 0,
            'high_severity_zones': 0,
            'critical_severity_zones': 0,
            'safety_score': 100,
            'safety_level': 'Safe',
            'badge_color': 'green',
            'total_penalty': 0,
        }


@require_http_methods(['GET'])
@csrf_exempt
def api_route_geometry(request):
    """
    Fetch multiple route alternatives from OSRM with safety analysis.
    Query params: start_lat, start_lon, end_lat, end_lon
    Returns multiple routes ranked by safety score.
    """
    try:
        import urllib.request
        
        start_lat = float(request.GET.get('start_lat'))
        start_lon = float(request.GET.get('start_lon'))
        end_lat = float(request.GET.get('end_lat'))
        end_lon = float(request.GET.get('end_lon'))
        
        if not all([-90 <= start_lat <= 90, -180 <= start_lon <= 180,
                    -90 <= end_lat <= 90, -180 <= end_lon <= 180]):
            return HttpResponseBadRequest('Invalid coordinates')
        
        # Use OSRM public server for routing with alternatives enabled
        # alternatives=true will return multiple route options
        api_url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson&alternatives=true"
        
        try:
            with urllib.request.urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check if routes were found
                if data.get('code') == 'Ok' and data.get('routes') and len(data['routes']) > 0:
                    routes_list = []
                    
                    # Process each route
                    for idx, route in enumerate(data['routes']):
                        coordinates = route['geometry']['coordinates']
                        # Convert [lon, lat] to [lat, lon]
                        route_coords = [[coord[1], coord[0]] for coord in coordinates]
                        
                        distance_meters = route.get('distance', 0)
                        duration_seconds = route.get('duration', 0)
                        
                        # Analyze safety for this route
                        safety_analysis = analyze_route_safety(
                            route_coords, start_lat, start_lon, end_lat, end_lon
                        )
                        
                        # Estimate travel time (40 km/h average urban speed)
                        distance_km = distance_meters / 1000
                        estimated_time_minutes = round((distance_km / 40) * 60)
                        
                        routes_list.append({
                            'id': idx,
                            'route': route_coords,
                            'distance_meters': distance_meters,
                            'distance_km': round(distance_km, 2),
                            'duration_seconds': duration_seconds,
                            'estimated_time_minutes': estimated_time_minutes,
                            'safety_score': safety_analysis['safety_score'],
                            'safety_level': safety_analysis['safety_level'],
                            'badge_color': safety_analysis['badge_color'],
                            'intersecting_zones': safety_analysis['intersecting_zones'],
                            'total_zones': safety_analysis['total_zones'],
                            'high_severity_zones': safety_analysis['high_severity_zones'],
                            'critical_severity_zones': safety_analysis['critical_severity_zones'],
                        })
                    
                    # Sort routes by safety score (descending), then by distance (ascending)
                    routes_list.sort(key=lambda x: (-x['safety_score'], x['distance_meters']))
                    
                    # Determine if safer alternative should be recommended
                    recommended_route_idx = 0  # Default to safest route
                    safer_alternative_recommended = False
                    safer_recommendation_reason = ""
                    
                    # If first route (fastest by default) is unsafe and safer alternative exists
                    if len(routes_list) > 1:
                        fastest_route = min(routes_list, key=lambda x: x['estimated_time_minutes'])
                        safest_route = routes_list[0]
                        
                        if fastest_route['safety_score'] < 70 and safest_route['safety_score'] >= 75:
                            safer_alternative_recommended = True
                            safer_recommendation_reason = "Fastest route contains unsafe zones"
                            recommended_route_idx = 0  # Use safest route
                        elif fastest_route['safety_score'] < safest_route['safety_score'] - 15:
                            safer_alternative_recommended = True
                            safer_recommendation_reason = "Fastest route is significantly less safe"
                            recommended_route_idx = 0  # Use safest route
                    
                    return JsonResponse({
                        'routes': routes_list,
                        'recommended_route_id': routes_list[recommended_route_idx]['id'],
                        'safer_alternative_recommended': safer_alternative_recommended,
                        'safer_recommendation_reason': safer_recommendation_reason,
                        'success': True,
                    })
                else:
                    # Route not found
                    return JsonResponse({
                        'routes': [],
                        'success': False,
                        'error': 'No drivable route exists between these locations'
                    })
        
        except urllib.error.URLError as e:
            return JsonResponse({
                'routes': [],
                'success': False,
                'error': f'Routing service unavailable: {str(e)}'
            })
    
    except (ValueError, TypeError) as e:
        return HttpResponseBadRequest(f'Invalid request: {str(e)}')


# ================ SAFETY INTELLIGENCE CENTER API ================

@require_http_methods(['GET'])
@csrf_exempt
def api_safety_heatmap(request):
    """
    Generate safety heatmap data based on community reports and unsafe zones.
    Returns grid of points with safety scores for visualization.
    
    Query params:
        - bounds: "lat_min,lon_min,lat_max,lon_max" (optional, defaults to Bangalore)
    """
    try:
        # Default to Bangalore bounds
        bounds_str = request.GET.get('bounds', '12.8,77.4,13.1,77.8')
        bounds = list(map(float, bounds_str.split(',')))
        lat_min, lon_min, lat_max, lon_max = bounds
        
        # Create heatmap points
        heatmap_data = []
        
        # Get all unsafe zones and reports
        zones = UnsafeZone.objects.all()
        reports = CommunityReport.objects.all()
        
        # Add danger points from unsafe zones (high intensity)
        for zone in zones:
            heatmap_data.append({
                'lat': zone.latitude,
                'lng': zone.longitude,
                'intensity': 0.8,  # Red zone - critical
                'type': 'unsafe_zone',
                'name': zone.name
            })
        
        # Add danger points from critical/high severity reports
        for report in reports:
            if report.severity in ['high', 'critical']:
                intensity = 0.9 if report.severity == 'critical' else 0.7
                heatmap_data.append({
                    'lat': report.latitude,
                    'lng': report.longitude,
                    'intensity': intensity,
                    'type': 'report',
                    'name': report.title,
                    'severity': report.severity
                })
        
        return JsonResponse({'heatmap_data': heatmap_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_area_safety_score(request):
    """
    Calculate safety score for a specific area (lat, lon, radius).
    
    Query params:
        - lat: Latitude (required)
        - lon: Longitude (required)
        - radius: Radius in meters (default: 1000)
    """
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
        radius = int(request.GET.get('radius', 1000))
        
        # Get area name using reverse geocoding
        area_name = f"Area at {lat:.4f}, {lon:.4f}"
        
        # Find unsafe zones within area
        unsafe_zones = []
        for zone in UnsafeZone.objects.all():
            distance = calculate_distance(lat, lon, zone.latitude, zone.longitude)
            if distance <= radius:
                unsafe_zones.append({
                    'id': zone.id,
                    'name': zone.name,
                    'distance': int(distance),
                    'radius': zone.radius
                })
        
        # Find reports within area
        reports_in_area = []
        severity_count = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        last_incident = None
        
        for report in CommunityReport.objects.all():
            distance = calculate_distance(lat, lon, report.latitude, report.longitude)
            if distance <= radius:
                reports_in_area.append({
                    'id': report.id,
                    'title': report.title,
                    'severity': report.severity,
                    'distance': int(distance),
                    'created_at': report.created_at.isoformat()
                })
                severity_count[report.severity] += 1
                
                if last_incident is None or report.created_at > last_incident:
                    last_incident = report.created_at
        
        # Calculate safety score
        total_incidents = len(reports_in_area) + len(unsafe_zones)
        base_score = 100
        
        # Deduct points for incidents
        base_score -= severity_count['low'] * 2
        base_score -= severity_count['medium'] * 5
        base_score -= severity_count['high'] * 10
        base_score -= severity_count['critical'] * 15
        base_score -= len(unsafe_zones) * 8
        
        safety_score = max(0, min(100, base_score))
        
        # Determine risk level
        if safety_score >= 80:
            risk_level = 'Low'
            risk_color = 'green'
        elif safety_score >= 60:
            risk_level = 'Moderate'
            risk_color = 'yellow'
        elif safety_score >= 40:
            risk_level = 'High'
            risk_color = 'orange'
        else:
            risk_level = 'Critical'
            risk_color = 'red'
        
        # Calculate days since last incident
        days_since_incident = None
        if last_incident:
            delta = datetime.now() - last_incident.replace(tzinfo=None)
            days_since_incident = delta.days
        
        return JsonResponse({
            'area_name': area_name,
            'safety_score': safety_score,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'reports_count': len(reports_in_area),
            'unsafe_zones_count': len(unsafe_zones),
            'unsafe_zones': unsafe_zones,
            'reports': reports_in_area,
            'severity_breakdown': severity_count,
            'last_incident': last_incident.isoformat() if last_incident else None,
            'days_since_incident': days_since_incident,
            'total_incidents': total_incidents
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_time_based_safety(request):
    """
    Calculate time-based safety analysis.
    Returns current and hourly safety recommendations.
    """
    try:
        current_time = datetime.now()
        hour = current_time.hour
        
        # Determine day/night and time-based risk
        if 6 <= hour < 18:
            period = 'Daytime'
            base_risk = 'Low'
            risk_multiplier = 0.7
        elif 18 <= hour < 21:
            period = 'Evening'
            base_risk = 'Moderate'
            risk_multiplier = 1.0
        elif 21 <= hour < 24 or 0 <= hour < 6:
            period = 'Night'
            base_risk = 'High'
            risk_multiplier = 1.5
        else:
            period = 'Late Night'
            base_risk = 'Critical'
            risk_multiplier = 2.0
        
        # Get all reports and calculate time-based statistics
        reports = CommunityReport.objects.all()
        hour_stats = [0] * 24
        
        for report in reports:
            report_hour = report.created_at.hour
            hour_stats[report_hour] += 1
        
        # Find peak hours
        peak_hours = sorted(enumerate(hour_stats), key=lambda x: x[1], reverse=True)[:3]
        
        return JsonResponse({
            'current_time': current_time.isoformat(),
            'current_hour': hour,
            'period': period,
            'base_risk': base_risk,
            'risk_multiplier': risk_multiplier,
            'is_daytime': 6 <= hour < 18,
            'is_night': hour >= 18 or hour < 6,
            'hour_statistics': hour_stats,
            'peak_hours': [{'hour': h, 'incidents': c} for h, c in peak_hours],
            'recommendation': f"{base_risk} risk period. {'Stay alert and use well-lit routes.' if base_risk != 'Low' else 'Relatively safe time to travel.'}"
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_safe_places(request):
    """
    Return safe places like police stations, hospitals, metro stations.
    Currently returns static data (can be extended with real data).
    """
    try:
        safe_places = {
            'police_stations': [
                {'name': 'Whitefield Police Station', 'lat': 12.9698, 'lng': 77.7499, 'type': 'police'},
                {'name': 'Koramangala Police Station', 'lat': 12.9316, 'lng': 77.6245, 'type': 'police'},
                {'name': 'BTM Layout Police Station', 'lat': 12.9176, 'lng': 77.6101, 'type': 'police'},
                {'name': 'Indiranagar Police Station', 'lat': 12.9716, 'lng': 77.6412, 'type': 'police'},
            ],
            'hospitals': [
                {'name': 'Apollo Hospital', 'lat': 12.9716, 'lng': 77.6074, 'type': 'hospital'},
                {'name': 'Fortis Hospital', 'lat': 12.9689, 'lng': 77.5940, 'type': 'hospital'},
                {'name': 'Max Healthcare', 'lat': 12.9671, 'lng': 77.5803, 'type': 'hospital'},
                {'name': 'Manipal Hospital', 'lat': 12.9352, 'lng': 77.6245, 'type': 'hospital'},
            ],
            'metro_stations': [
                {'name': 'Cubbon Park Metro', 'lat': 12.9716, 'lng': 77.5946, 'type': 'metro'},
                {'name': 'Indiranagar Metro', 'lat': 12.9745, 'lng': 77.6412, 'type': 'metro'},
                {'name': 'Whitefield Metro', 'lat': 12.9698, 'lng': 77.7499, 'type': 'metro'},
                {'name': 'Koramangala Metro', 'lat': 12.9316, 'lng': 77.6245, 'type': 'metro'},
            ],
            'bus_stations': [
                {'name': 'Majestic Bus Station', 'lat': 12.9757, 'lng': 77.5663, 'type': 'bus'},
                {'name': 'Silk Board Bus Station', 'lat': 12.9352, 'lng': 77.6245, 'type': 'bus'},
                {'name': 'Whitefield Bus Station', 'lat': 12.9698, 'lng': 77.7499, 'type': 'bus'},
            ]
        }
        
        return JsonResponse({'safe_places': safe_places})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_dangerous_areas(request):
    """
    Get top dangerous areas ranked by incident severity and count.
    Returns top 10 areas.
    """
    try:
        # Define Bangalore areas and their approximate boundaries
        areas = {
            'Whitefield': {'lat': 12.9698, 'lng': 77.7499, 'radius': 2000},
            'Koramangala': {'lat': 12.9316, 'lng': 77.6245, 'radius': 1500},
            'BTM Layout': {'lat': 12.9176, 'lng': 77.6101, 'radius': 1500},
            'Indiranagar': {'lat': 12.9745, 'lng': 77.6412, 'radius': 1500},
            'Majestic': {'lat': 12.9757, 'lng': 77.5663, 'radius': 1500},
            'Silk Board': {'lat': 12.9352, 'lng': 77.6245, 'radius': 1500},
            'Marathahalli': {'lat': 12.9689, 'lng': 77.6840, 'radius': 1500},
            'KR Puram': {'lat': 13.0012, 'lng': 77.6245, 'radius': 1500},
            'Shivajinagar': {'lat': 12.9809, 'lng': 77.5915, 'radius': 1500},
            'MG Road': {'lat': 12.9716, 'lng': 77.5946, 'radius': 1500},
        }
        
        area_scores = []
        
        for area_name, area_coords in areas.items():
            area_lat = area_coords['lat']
            area_lng = area_coords['lng']
            area_radius = area_coords['radius']
            
            # Count incidents and zones in area
            incidents = 0
            severity_total = 0
            
            for report in CommunityReport.objects.all():
                distance = calculate_distance(area_lat, area_lng, report.latitude, report.longitude)
                if distance <= area_radius:
                    incidents += 1
                    severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                    severity_total += severity_map.get(report.severity, 2)
            
            # Add unsafe zones
            for zone in UnsafeZone.objects.all():
                distance = calculate_distance(area_lat, area_lng, zone.latitude, zone.longitude)
                if distance <= area_radius:
                    incidents += 1
                    severity_total += 3
            
            # Calculate danger score
            danger_score = incidents * 10 + severity_total * 5
            
            if danger_score > 0:
                area_scores.append({
                    'area': area_name,
                    'danger_score': danger_score,
                    'incidents': incidents,
                    'severity_rating': min(5, (severity_total / max(1, incidents))),
                    'lat': area_lat,
                    'lng': area_lng
                })
        
        # Sort by danger score
        area_scores.sort(key=lambda x: x['danger_score'], reverse=True)
        top_areas = area_scores[:10]
        
        return JsonResponse({
            'dangerous_areas': top_areas,
            'count': len(top_areas)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_safety_trends(request):
    """
    Get safety trend data for analytics charts.
    Returns weekly and monthly statistics.
    """
    try:
        now = datetime.now()
        
        # Weekly data
        weekly_data = []
        days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i in range(7):
            day_start = now - timedelta(days=i)
            day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = CommunityReport.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            weekly_data.append({
                'day': days_of_week[day_start.weekday()],
                'date': day_start.strftime('%Y-%m-%d'),
                'incidents': count
            })
        
        weekly_data.reverse()
        
        # Monthly data (last 30 days)
        monthly_data = []
        for i in range(30):
            day_start = now - timedelta(days=i)
            day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = CommunityReport.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            monthly_data.append({
                'date': day_start.strftime('%m-%d'),
                'incidents': count
            })
        
        monthly_data.reverse()
        
        # Severity trends
        severity_trends = {
            'low': CommunityReport.objects.filter(severity='low').count(),
            'medium': CommunityReport.objects.filter(severity='medium').count(),
            'high': CommunityReport.objects.filter(severity='high').count(),
            'critical': CommunityReport.objects.filter(severity='critical').count(),
        }
        
        # Active zones
        active_zones = []
        for zone in UnsafeZone.objects.all():
            zone_reports = CommunityReport.objects.filter(
                latitude__gte=zone.latitude - 0.01,
                latitude__lte=zone.latitude + 0.01,
                longitude__gte=zone.longitude - 0.01,
                longitude__lte=zone.longitude + 0.01
            ).count()
            
            if zone_reports > 0:
                active_zones.append({
                    'name': zone.name,
                    'incidents': zone_reports
                })
        
        active_zones.sort(key=lambda x: x['incidents'], reverse=True)
        
        return JsonResponse({
            'weekly_data': weekly_data,
            'monthly_data': monthly_data,
            'severity_trends': severity_trends,
            'active_zones': active_zones[:5]
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ================ AUTHENTICATION VIEWS ================

def validate_password_strength(password):
    """
    Validate password strength requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%)"
    
    return True, "Password is strong"


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_login_locked(request):
    """Check if login is locked due to too many attempts"""
    ip = get_client_ip(request)
    lock_key = f'login_lock_{ip}'
    attempts_key = f'login_attempts_{ip}'
    
    # Get from session
    if lock_key in request.session:
        lock_time = request.session[lock_key]
        if isinstance(lock_time, str):
            lock_time = datetime.fromisoformat(lock_time)
        if datetime.now() < lock_time:
            return True
    
    return False


def record_failed_login(request):
    """Record a failed login attempt"""
    ip = get_client_ip(request)
    attempts_key = f'login_attempts_{ip}'
    lock_key = f'login_lock_{ip}'
    
    attempts = request.session.get(attempts_key, 0)
    attempts += 1
    request.session[attempts_key] = attempts
    
    # Lock after 5 attempts
    if attempts >= 5:
        lock_until = datetime.now() + timedelta(minutes=15)
        request.session[lock_key] = lock_until.isoformat()
        request.session.set_expiry(900)  # 15 minutes
    
    request.session.save()


def reset_failed_logins(request):
    """Reset failed login attempts"""
    ip = get_client_ip(request)
    attempts_key = f'login_attempts_{ip}'
    lock_key = f'login_lock_{ip}'
    
    if attempts_key in request.session:
        del request.session[attempts_key]
    if lock_key in request.session:
        del request.session[lock_key]
    
    request.session.save()


@csrf_protect
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Check if locked
    if is_login_locked(request):
        messages.error(request, 'Too many login attempts. Please try again in 15 minutes.')
        return render(request, 'login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me', False)
        
        if not username or not password:
            messages.error(request, 'Invalid username or password')
            record_failed_login(request)
            return render(request, 'login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            reset_failed_logins(request)
            
            # Set session timeout
            if remember_me:
                request.session.set_expiry(timedelta(days=7))  # 7 days
            else:
                request.session.set_expiry(timedelta(minutes=30))  # 30 minutes
            
            request.session.save()
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            record_failed_login(request)
    
    return render(request, 'login.html')


@csrf_protect
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        terms = request.POST.get('terms', False)
        
        # Validation
        errors = []
        
        if not username or not email or not password1 or not password2:
            errors.append('All fields are required')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        
        if password1 != password2:
            errors.append('Passwords do not match')
        
        if password1:
            is_strong, strength_msg = validate_password_strength(password1)
            if not is_strong:
                errors.append(strength_msg)
        
        if not terms:
            errors.append('You must accept the terms and privacy policy')
        
        # Email validation
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Invalid email address')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')


@require_POST
@csrf_protect
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# Update dashboard view to require login
@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html')


# ================ LOCATION SEARCH API ================

@require_http_methods(['GET'])
@csrf_exempt
def api_location_search(request):
    """
    Global location search with autocomplete.
    Supports worldwide search: countries, cities, streets, landmarks, etc.
    
    Query params:
        - q: Search query (required)
        - limit: Max results (default: 10)
        - fuzzy: Enable fuzzy matching (default: true)
    
    Returns:
        {
            "results": [
                {
                    "id": "place_id",
                    "name": "Location Name",
                    "display_name": "Full address",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "type": "city|road|village|etc",
                    "class": "place|amenity|etc"
                }
            ]
        }
    """
    try:
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        fuzzy = request.GET.get('fuzzy', 'true').lower() == 'true'
        
        if not query:
            return JsonResponse({
                'results': [],
                'error': 'Query parameter is required'
            }, status=400)
        
        if limit < 1 or limit > 50:
            limit = 10
        
        # Import here to avoid circular imports
        from safety.location_search import LocationSearcher
        
        # Perform search
        results = LocationSearcher.search(query, use_fuzzy=fuzzy, limit=limit)
        
        return JsonResponse({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return JsonResponse({
            'results': [],
            'error': str(e)
        }, status=400)


@require_http_methods(['GET'])
@csrf_exempt
def api_reverse_geocode(request):
    """
    Reverse geocoding - get location name from coordinates.
    
    Query params:
        - lat: Latitude (required)
        - lon: Longitude (required)
    
    Returns:
        {
            "location": {
                "display_name": "Street, City, Country",
                "latitude": 12.9716,
                "longitude": 77.5946
            }
        }
    """
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
        
        from safety.location_search import LocationSearcher
        
        location = LocationSearcher.reverse_geocode(lat, lon)
        
        if location:
            return JsonResponse({'location': location})
        else:
            return JsonResponse({
                'error': 'Could not reverse geocode location'
            }, status=400)
    
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'error': 'Invalid coordinates'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


# ================ COMMUNITY REPORTS STATISTICS ================

@require_http_methods(['GET'])
@csrf_exempt
def api_reports_statistics(request):
    """
    Get community reports statistics for dashboard integration.
    Returns total reports, severity breakdown, recent reports, etc.
    """
    try:
        all_reports = CommunityReport.objects.all()
        
        # Count by severity
        severity_counts = {
            'low': all_reports.filter(severity='low').count(),
            'medium': all_reports.filter(severity='medium').count(),
            'high': all_reports.filter(severity='high').count(),
            'critical': all_reports.filter(severity='critical').count(),
        }
        
        total_reports = all_reports.count()
        verified_reports = all_reports.filter(is_verified=True).count()
        
        # Get recent reports (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_reports = all_reports.filter(created_at__gte=seven_days_ago).count()
        
        # Get last incident time
        last_report = all_reports.order_by('-created_at').first()
        last_incident_time = last_report.created_at.isoformat() if last_report else None
        
        return JsonResponse({
            'total_reports': total_reports,
            'verified_reports': verified_reports,
            'severity_breakdown': severity_counts,
            'recent_reports_7days': recent_reports,
            'last_incident': last_incident_time,
            'high_and_critical': severity_counts['high'] + severity_counts['critical']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ================ AI RECOMMENDATIONS BASED ON REAL DATA ================

@require_http_methods(['GET'])
@csrf_exempt
def api_ai_recommendations(request):
    """
    Generate AI recommendations based on actual community reports and unsafe zones.
    Returns personalized safety recommendations.
    """
    try:
        # Get current location (optional)
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        all_reports = CommunityReport.objects.all()
        all_zones = UnsafeZone.objects.all()
        
        # Analyze report severity
        critical_reports = all_reports.filter(severity='critical').count()
        high_reports = all_reports.filter(severity='high').count()
        medium_reports = all_reports.filter(severity='medium').count()
        low_reports = all_reports.filter(severity='low').count()
        
        recommendations = []
        safety_level = 'Safe'
        alert_level = 'Low'
        
        # Generate recommendations based on report data
        if critical_reports > 0:
            recommendations.append({
                'priority': 'Critical',
                'message': f'🚨 Critical incidents reported: {critical_reports} recent danger{" incident" if critical_reports == 1 else " incidents"} in monitored areas. Avoid traveling alone.',
                'color': '#ef4444',
                'icon': 'fa-exclamation-circle'
            })
            safety_level = 'Unsafe'
            alert_level = 'Critical'
        
        if high_reports > 2:
            recommendations.append({
                'priority': 'High',
                'message': f'⚠️ High-risk area: {high_reports} serious incidents reported recently. Increase vigilance.',
                'color': '#f97316',
                'icon': 'fa-triangle-exclamation'
            })
            if safety_level != 'Unsafe':
                safety_level = 'Moderate'
            if alert_level == 'Low':
                alert_level = 'High'
        
        if medium_reports > 5:
            recommendations.append({
                'priority': 'Medium',
                'message': f'⚠️ Moderate incidents reported: {medium_reports} reports in this area. Stay alert.',
                'color': '#eab308',
                'icon': 'fa-circle-exclamation'
            })
            if safety_level == 'Safe':
                safety_level = 'Moderate'
        
        # Recommendations if area is safe
        if low_reports + medium_reports + high_reports + critical_reports == 0:
            recommendations.append({
                'priority': 'Info',
                'message': '✅ No recent incidents reported in monitored areas. Area appears safe.',
                'color': '#10b981',
                'icon': 'fa-check-circle'
            })
            safety_level = 'Safe'
            alert_level = 'Low'
        elif critical_reports == 0 and high_reports == 0:
            if medium_reports + low_reports < 3:
                recommendations.append({
                    'priority': 'Info',
                    'message': '✓ Relatively safe: Limited incident reports. Exercise normal precautions.',
                    'color': '#10b981',
                    'icon': 'fa-info-circle'
                })
                if safety_level == 'Safe':
                    pass
        
        # Time-based recommendations
        current_hour = datetime.now().hour
        if 21 <= current_hour or current_hour < 6:
            recommendations.append({
                'priority': 'Timing',
                'message': '🌙 Night travel detected. Recommend using well-lit routes and sharing your location.',
                'color': '#8b5cf6',
                'icon': 'fa-moon'
            })
        
        # Area-specific recommendations if location provided
        if lat and lon:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                
                # Check for nearby high-severity reports
                area_high_reports = all_reports.filter(severity__in=['high', 'critical'])
                nearby_critical = 0
                
                for report in area_high_reports:
                    dist = calculate_distance(lat_f, lon_f, report.latitude, report.longitude)
                    if dist < 2000:  # Within 2km
                        nearby_critical += 1
                
                if nearby_critical > 0:
                    recommendations.append({
                        'priority': 'Location',
                        'message': f'📍 {nearby_critical} critical incident{"s" if nearby_critical > 1 else ""} reported within 2km. Consider alternative routes.',
                        'color': '#ef4444',
                        'icon': 'fa-map-pin'
                    })
            except (ValueError, TypeError):
                pass
        
        return JsonResponse({
            'safety_level': safety_level,
            'alert_level': alert_level,
            'recommendations': recommendations,
            'total_reports': all_reports.count(),
            'report_breakdown': {
                'critical': critical_reports,
                'high': high_reports,
                'medium': medium_reports,
                'low': low_reports
            },
            'unsafe_zones_count': all_zones.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ================ PROFILE & SETTINGS PAGES ================

@login_required(login_url='login')
def profile_view(request):
    """User profile page"""
    return render(request, 'profile.html')


@login_required(login_url='login')
def settings_view(request):
    """User settings page"""
    return render(request, 'settings.html')


# ================ EMERGENCY CONTACTS API ================

@require_http_methods(['GET', 'POST'])
@csrf_exempt
def api_emergency_contacts(request):
    """
    GET: List all emergency contacts for the user
    POST: Create a new emergency contact
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        contacts = EmergencyContact.objects.filter(user=request.user).values(
            'id', 'name', 'relationship', 'phone_number', 'alternate_number', 'created_at'
        )
        return JsonResponse({'contacts': list(contacts)})
    
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            name = body.get('name', '').strip()
            relationship = body.get('relationship', 'other').lower()
            phone_number = body.get('phone_number', '').strip()
            alternate_number = body.get('alternate_number', '').strip()
            
            # Validation
            if not name or not phone_number:
                return JsonResponse({'error': 'Name and phone number are required'}, status=400)
            
            if relationship not in ['mother', 'father', 'brother', 'sister', 'friend', 'guardian', 'police', 'other']:
                return JsonResponse({'error': 'Invalid relationship type'}, status=400)
            
            # Check if contact already exists
            if EmergencyContact.objects.filter(user=request.user, phone_number=phone_number).exists():
                return JsonResponse({'error': 'This phone number is already added'}, status=400)
            
            contact = EmergencyContact.objects.create(
                user=request.user,
                name=name,
                relationship=relationship,
                phone_number=phone_number,
                alternate_number=alternate_number if alternate_number else None
            )
            
            return JsonResponse({
                'id': contact.id,
                'name': contact.name,
                'relationship': contact.relationship,
                'phone_number': contact.phone_number,
                'alternate_number': contact.alternate_number,
                'created_at': contact.created_at.isoformat(),
            }, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@require_http_methods(['PUT', 'DELETE'])
@csrf_exempt
def api_emergency_contact_detail(request, contact_id):
    """
    PUT: Update an emergency contact
    DELETE: Delete an emergency contact
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        contact = EmergencyContact.objects.get(id=contact_id, user=request.user)
    except EmergencyContact.DoesNotExist:
        return JsonResponse({'error': 'Contact not found'}, status=404)
    
    if request.method == 'PUT':
        try:
            body = json.loads(request.body.decode('utf-8'))
            
            contact.name = body.get('name', contact.name)
            contact.relationship = body.get('relationship', contact.relationship)
            contact.phone_number = body.get('phone_number', contact.phone_number)
            contact.alternate_number = body.get('alternate_number', contact.alternate_number)
            contact.save()
            
            return JsonResponse({
                'id': contact.id,
                'name': contact.name,
                'relationship': contact.relationship,
                'phone_number': contact.phone_number,
                'alternate_number': contact.alternate_number,
                'updated_at': contact.updated_at.isoformat(),
            })
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    
    elif request.method == 'DELETE':
        contact.delete()
        return JsonResponse({'message': 'Contact deleted successfully'})


# ================ USER PREFERENCES API ================

@require_http_methods(['GET', 'POST'])
@csrf_exempt
def api_user_preferences(request):
    """
    GET: Get user preferences
    POST: Update user preferences
    """
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': preferences.id,
            'safety_alerts': preferences.safety_alerts,
            'location_updates': preferences.location_updates,
            'community_reports': preferences.community_reports,
            'email_notifications': preferences.email_notifications,
            'show_ai_recommendations': preferences.show_ai_recommendations,
            'show_analytics': preferences.show_analytics,
            'show_heatmap': preferences.show_heatmap,
            'show_quick_access': preferences.show_quick_access,
            'theme': preferences.theme,
            'auto_theme': preferences.auto_theme,
            'two_factor_auth': preferences.two_factor_auth,
            'data_privacy': preferences.data_privacy,
            'session_timeout': preferences.session_timeout,
        })
    
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            
            # Update preferences
            preferences.safety_alerts = body.get('safety_alerts', preferences.safety_alerts)
            preferences.location_updates = body.get('location_updates', preferences.location_updates)
            preferences.community_reports = body.get('community_reports', preferences.community_reports)
            preferences.email_notifications = body.get('email_notifications', preferences.email_notifications)
            preferences.show_ai_recommendations = body.get('show_ai_recommendations', preferences.show_ai_recommendations)
            preferences.show_analytics = body.get('show_analytics', preferences.show_analytics)
            preferences.show_heatmap = body.get('show_heatmap', preferences.show_heatmap)
            preferences.show_quick_access = body.get('show_quick_access', preferences.show_quick_access)
            preferences.theme = body.get('theme', preferences.theme)
            preferences.auto_theme = body.get('auto_theme', preferences.auto_theme)
            preferences.two_factor_auth = body.get('two_factor_auth', preferences.two_factor_auth)
            preferences.data_privacy = body.get('data_privacy', preferences.data_privacy)
            preferences.session_timeout = body.get('session_timeout', preferences.session_timeout)
            
            preferences.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Preferences saved successfully',
                'id': preferences.id,
                'safety_alerts': preferences.safety_alerts,
                'location_updates': preferences.location_updates,
                'community_reports': preferences.community_reports,
                'email_notifications': preferences.email_notifications,
                'show_ai_recommendations': preferences.show_ai_recommendations,
                'show_analytics': preferences.show_analytics,
                'show_heatmap': preferences.show_heatmap,
                'show_quick_access': preferences.show_quick_access,
                'theme': preferences.theme,
                'auto_theme': preferences.auto_theme,
                'two_factor_auth': preferences.two_factor_auth,
                'data_privacy': preferences.data_privacy,
                'session_timeout': preferences.session_timeout,
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


# ================ SOS API ================

@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_send_sos(request):
    """
    Send SOS alert to all registered emergency contacts
    
    POST body:
    {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        latitude = float(body.get('latitude'))
        longitude = float(body.get('longitude'))
        
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return HttpResponseBadRequest('Invalid coordinates')
        
        # Create SOS alert record
        sos_alert = SOSAlert.objects.create(
            user=request.user,
            latitude=latitude,
            longitude=longitude,
            status='pending'
        )
        
        # Get all emergency contacts for the user
        contacts = EmergencyContact.objects.filter(user=request.user)
        
        if not contacts.exists():
            return JsonResponse({
                'sos_id': sos_alert.id,
                'success': False,
                'message': 'No emergency contacts registered',
                'delivered_to': []
            })
        
        # Prepare SOS message
        from .sms_sender import SMSSender
        
        # Create Google Maps link
        maps_link = f"https://maps.google.com/?q={latitude},{longitude}"
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sms_message = f"""🚨 EMERGENCY ALERT

I may be in danger and need immediate help.

📍 My current location:
{maps_link}

⏰ Time: {timestamp}

Sent from SafePath AI"""
        
        # Send SMS to all contacts
        delivered_count = 0
        failed_count = 0
        delivered_to = []
        failed_contacts = []
        
        for contact in contacts:
            # Try primary phone number
            success, message = SMSSender.send_sms(contact.phone_number, sms_message)
            
            delivery_status = 'delivered' if success else 'failed'
            delivered_at = datetime.now() if success else None
            
            delivery_log = SOSDeliveryLog.objects.create(
                sos_alert=sos_alert,
                contact=contact,
                delivery_status=delivery_status,
                delivered_at=delivered_at,
                error_message=message if not success else None
            )
            
            if success:
                delivered_count += 1
                delivered_to.append({
                    'id': contact.id,
                    'name': contact.name,
                    'phone': contact.phone_number,
                    'status': 'delivered'
                })
            else:
                failed_count += 1
                failed_contacts.append({
                    'id': contact.id,
                    'name': contact.name,
                    'phone': contact.phone_number,
                    'status': 'failed',
                    'error': message
                })
        
        # Update SOS alert status
        sos_alert.status = 'sent' if delivered_count > 0 else 'failed'
        sos_alert.save()
        
        return JsonResponse({
            'sos_id': sos_alert.id,
            'success': delivered_count > 0,
            'delivered_count': delivered_count,
            'failed_count': failed_count,
            'total_contacts': contacts.count(),
            'delivered_to': delivered_to,
            'failed_contacts': failed_contacts,
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'maps_link': maps_link
            },
            'timestamp': timestamp,
            'message': f'SOS sent to {delivered_count}/{contacts.count()} contacts'
        })
    
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return HttpResponseBadRequest(f'Invalid request: {str(e)}')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['GET'])
def api_sos_history(request):
    """
    Get SOS history for the logged-in user
    
    Query params:
        - limit: Max records (default: 50)
        - offset: Pagination offset (default: 0)
    """
    try:
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Get SOS alerts for user
        sos_alerts = SOSAlert.objects.filter(user=request.user).prefetch_related('delivery_logs')
        
        history = []
        for alert in sos_alerts[offset:offset+limit]:
            delivery_logs = alert.delivery_logs.all()
            
            history.append({
                'id': alert.id,
                'latitude': alert.latitude,
                'longitude': alert.longitude,
                'status': alert.status,
                'created_at': alert.created_at.isoformat(),
                'maps_link': f"https://maps.google.com/?q={alert.latitude},{alert.longitude}",
                'contacts_notified': delivery_logs.count(),
                'deliveries': [{
                    'contact_name': log.contact.name,
                    'phone': log.contact.phone_number,
                    'status': log.delivery_status,
                    'delivered_at': log.delivered_at.isoformat() if log.delivered_at else None
                } for log in delivery_logs]
            })
        
        return JsonResponse({
            'history': history,
            'total': SOSAlert.objects.filter(user=request.user).count(),
            'returned': len(history)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ================ ROUTE HISTORY API ================

@login_required
@require_http_methods(['GET', 'POST'])
def api_route_history(request):
    """
    GET: List recent routes for the user
    POST: Save a new route to history
    
    POST body:
    {
        "source_name": str,
        "source_latitude": float,
        "source_longitude": float,
        "destination_name": str,
        "destination_latitude": float,
        "destination_longitude": float,
        "distance_km": float,
        "estimated_time_minutes": int,
        "safety_score": int  # 0-100
    }
    """
    if request.method == 'GET':
        try:
            limit = int(request.GET.get('limit', 20))
            offset = int(request.GET.get('offset', 0))
            
            # Get route history for user, ordered by most recent
            routes = RouteHistory.objects.filter(user=request.user)[offset:offset+limit]
            
            history = [{
                'id': route.id,
                'source_name': route.source_name,
                'source_latitude': route.source_latitude,
                'source_longitude': route.source_longitude,
                'destination_name': route.destination_name,
                'destination_latitude': route.destination_latitude,
                'destination_longitude': route.destination_longitude,
                'distance_km': route.distance_km,
                'estimated_time_minutes': route.estimated_time_minutes,
                'safety_score': route.safety_score,
                'created_at': route.created_at.isoformat(),
                'created_date': route.created_at.strftime('%b %d, %Y'),
            } for route in routes]
            
            return JsonResponse({
                'history': history,
                'total': RouteHistory.objects.filter(user=request.user).count(),
                'returned': len(history)
            })
        except Exception as e:
            return HttpResponseBadRequest(f'Error: {str(e)}')
    
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            
            # Validate required fields
            required_fields = ['source_name', 'source_latitude', 'source_longitude',
                             'destination_name', 'destination_latitude', 'destination_longitude',
                             'distance_km', 'estimated_time_minutes', 'safety_score']
            
            for field in required_fields:
                if field not in body:
                    return HttpResponseBadRequest(f'Missing required field: {field}')
            
            # Create route history record
            route = RouteHistory.objects.create(
                user=request.user,
                source_name=body.get('source_name', '').strip(),
                source_latitude=float(body.get('source_latitude')),
                source_longitude=float(body.get('source_longitude')),
                destination_name=body.get('destination_name', '').strip(),
                destination_latitude=float(body.get('destination_latitude')),
                destination_longitude=float(body.get('destination_longitude')),
                distance_km=float(body.get('distance_km')),
                estimated_time_minutes=int(body.get('estimated_time_minutes')),
                safety_score=int(body.get('safety_score'))
            )
            
            return JsonResponse({
                'id': route.id,
                'message': 'Route saved successfully',
                'source_name': route.source_name,
                'destination_name': route.destination_name,
                'created_at': route.created_at.isoformat(),
            }, status=201)
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return HttpResponseBadRequest(f'Invalid request: {str(e)}')
        except Exception as e:
            return HttpResponseBadRequest(f'Error: {str(e)}')