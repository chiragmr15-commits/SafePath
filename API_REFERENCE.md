# API Reference - Community Reports System

## Base URL
```
http://127.0.0.1:8000/api/
```

---

## Endpoints

### 1. Community Reports List & Create

#### GET /reports/
Retrieve all community reports.

**Request**:
```
GET /api/reports/
```

**Response** (200 OK):
```json
{
  "reports": [
    {
      "id": 1,
      "title": "Poor Lighting",
      "description": "Very dark road with no street lights",
      "severity": "high",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "is_verified": false,
      "created_at": "2026-06-10T13:46:33.890Z"
    },
    {
      "id": 2,
      "title": "Broken Streetlight",
      "description": "Multiple broken lights in area",
      "severity": "low",
      "latitude": 28.6150,
      "longitude": 77.2100,
      "is_verified": true,
      "created_at": "2026-06-10T13:47:00.000Z"
    }
  ]
}
```

---

#### POST /reports/
Create a new community report.

**Request**:
```
POST /api/reports/
Content-Type: application/json

{
  "title": "Dark Road",
  "description": "No street lights on main road",
  "severity": "high",
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Report title (max 255 chars) |
| description | string | Yes | Detailed description |
| severity | string | Yes | low, medium, high, or critical |
| latitude | float | Yes | -90 to 90 |
| longitude | float | Yes | -180 to 180 |

**Response** (201 Created):
```json
{
  "id": 1,
  "title": "Dark Road",
  "description": "No street lights on main road",
  "severity": "high",
  "latitude": 28.6139,
  "longitude": 77.209,
  "is_verified": false,
  "created_at": "2026-06-10T13:50:00.000Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid parameters or missing required fields
- 422 Unprocessable Entity: Invalid severity level

---

### 2. Report Detail Operations

#### DELETE /reports/{id}/
Delete a report (admin only).

**Request**:
```
DELETE /api/reports/1/
```

**Authorization**:
- User must be staff/superuser
- Returns 403 if not authorized

**Response** (200 OK):
```json
{
  "message": "Report deleted successfully"
}
```

**Error Responses**:
- 403 Forbidden: User is not admin
- 404 Not Found: Report doesn't exist

---

#### PATCH /reports/{id}/
Update report verification status (admin only).

**Request**:
```
PATCH /api/reports/1/
Content-Type: application/json

{
  "is_verified": true,
  "severity": "critical"
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| is_verified | boolean | No | Mark as verified/unverified |
| severity | string | No | Update severity level |

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Poor Lighting",
  "severity": "critical",
  "is_verified": true,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "created_at": "2026-06-10T13:46:33.890Z"
}
```

**Error Responses**:
- 403 Forbidden: User is not admin
- 404 Not Found: Report doesn't exist

---

### 3. Route Safety Analysis

#### POST /route-analysis/
Analyze a route for danger zones.

**Request**:
```
POST /api/route-analysis/
Content-Type: application/json

{
  "route": [
    [28.6100, 77.2050],
    [28.6120, 77.2080],
    [28.6150, 77.2100],
    [28.6180, 77.2120]
  ],
  "start_lat": 28.6100,
  "start_lon": 77.2050,
  "end_lat": 28.6180,
  "end_lon": 77.2120
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| route | array | Yes | Array of [lat, lon] pairs |
| start_lat | float | Yes | Starting latitude |
| start_lon | float | Yes | Starting longitude |
| end_lat | float | Yes | Ending latitude |
| end_lon | float | Yes | Ending longitude |

**Response** (200 OK):
```json
{
  "intersecting_zones": [
    {
      "id": 1,
      "title": "Poor Lighting",
      "description": "Very dark road with no street lights",
      "severity": "high",
      "latitude": 28.6139,
      "longitude": 77.209,
      "radius": 400,
      "is_verified": false
    },
    {
      "id": 2,
      "title": "Suspicious Activity",
      "description": "Reports of criminal activity",
      "severity": "critical",
      "latitude": 28.6150,
      "longitude": 77.2100,
      "radius": 600,
      "is_verified": true
    }
  ],
  "total_zones": 2,
  "high_severity_zones": 1,
  "critical_severity_zones": 1,
  "safety_score": 50,
  "safety_level": "Moderate",
  "badge_color": "yellow",
  "total_penalty": 50
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| intersecting_zones | array | List of detected danger zones |
| total_zones | integer | Total number of intersecting zones |
| high_severity_zones | integer | Count of high severity zones |
| critical_severity_zones | integer | Count of critical severity zones |
| safety_score | integer | 0-100 safety percentage |
| safety_level | string | Safe/Moderate/Unsafe |
| badge_color | string | green/yellow/red |
| total_penalty | integer | Sum of all penalties |

**Error Responses**:
- 400 Bad Request: Invalid route data

---

## Data Models

### CommunityReport
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "user123"
  },
  "title": "string (max 255)",
  "description": "string",
  "severity": "low|medium|high|critical",
  "latitude": -90 to 90,
  "longitude": -180 to 180,
  "is_verified": false,
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime"
}
```

---

## Severity Levels

| Level | Value | Radius | Penalty | Color |
|-------|-------|--------|---------|-------|
| Low | low | 100m | -5 | Green |
| Medium | medium | 250m | -10 | Yellow |
| High | high | 400m | -20 | Orange |
| Critical | critical | 600m | -30 | Red |

---

## Error Handling

### HTTP Status Codes
| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid parameters |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |

### Error Response Format
```json
{
  "error": "Description of the error"
}
```

---

## Rate Limiting

Currently no rate limiting implemented. For production, consider:
- API key authentication
- Request throttling (100 requests/minute per IP)
- User-based limits

---

## Authentication

### Public Endpoints
- `GET /api/reports/` - Public, no auth required
- `POST /api/reports/` - Public, no auth required

### Admin-Only Endpoints
- `DELETE /api/reports/{id}/` - Requires user.is_staff=True
- `PATCH /api/reports/{id}/` - Requires user.is_staff=True
- `POST /api/route-analysis/` - Public, no auth required

---

## Usage Examples

### Python
```python
import requests
import json

# Create a report
url = 'http://127.0.0.1:8000/api/reports/'
data = {
    'title': 'Unsafe Area',
    'description': 'Dark road with no lights',
    'severity': 'high',
    'latitude': 28.6139,
    'longitude': 77.2090
}
response = requests.post(url, json=data)
print(response.json())

# Get all reports
response = requests.get(url)
reports = response.json()['reports']

# Analyze route
url = 'http://127.0.0.1:8000/api/route-analysis/'
route_data = {
    'route': [[28.61, 77.20], [28.62, 77.21], [28.63, 77.22]],
    'start_lat': 28.61,
    'start_lon': 77.20,
    'end_lat': 28.63,
    'end_lon': 77.22
}
response = requests.post(url, json=route_data)
analysis = response.json()
```

### JavaScript
```javascript
// Create a report
fetch('/api/reports/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    title: 'Unsafe Area',
    description: 'Dark street',
    severity: 'high',
    latitude: 28.6139,
    longitude: 77.2090
  })
})
.then(r => r.json())
.then(data => console.log('Report created:', data));

// Get all reports
fetch('/api/reports/')
  .then(r => r.json())
  .then(data => console.log('Reports:', data.reports));

// Analyze route
fetch('/api/route-analysis/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    route: [[28.61, 77.20], [28.62, 77.21]],
    start_lat: 28.61,
    start_lon: 77.20,
    end_lat: 28.62,
    end_lon: 77.21
  })
})
.then(r => r.json())
.then(data => console.log('Safety Score:', data.safety_score));
```

### cURL
```bash
# Create report
curl -X POST http://127.0.0.1:8000/api/reports/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Unsafe Area",
    "description": "Dark street",
    "severity": "high",
    "latitude": 28.6139,
    "longitude": 77.2090
  }'

# Get all reports
curl http://127.0.0.1:8000/api/reports/

# Delete report (admin)
curl -X DELETE http://127.0.0.1:8000/api/reports/1/

# Verify report (admin)
curl -X PATCH http://127.0.0.1:8000/api/reports/1/ \
  -H "Content-Type: application/json" \
  -d '{"is_verified": true}'
```

---

## Webhooks (Future Enhancement)

Planned for future releases:
- Report creation webhooks
- Route analysis alerts
- Admin verification notifications

---

## Versioning

Current API Version: **1.0**

Future versions planned with backward compatibility.

---

## Support & Issues

For API issues:
1. Check status codes and error messages
2. Verify parameters match documentation
3. Check Django logs for details
4. Review console errors in browser

---

**Last Updated**: 2026-06-10
**Status**: Production Ready ✅
