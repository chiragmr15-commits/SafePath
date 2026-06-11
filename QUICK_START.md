# Quick Start Guide - Community Reports System

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 4.2+
- pip package manager

### Step 1: Install Dependencies
No additional dependencies needed (uses Django built-in features and CDN for Leaflet).

### Step 2: Run Migrations
```bash
cd d:\SMART_WOMEN_SAFETY-master
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Create Admin User (if needed)
```bash
python manage.py createsuperuser
```

### Step 4: Start Development Server
```bash
python manage.py runserver 8000
```

### Step 5: Access Applications
- **Main Page**: http://127.0.0.1:8000/
- **Community Reports**: http://127.0.0.1:8000/reports/
- **Navigation**: http://127.0.0.1:8000/navigation/
- **Admin Panel**: http://127.0.0.1:8000/admin/

---

## User Guide

### Creating a Safety Report

**Via Community Reports Page:**

1. **Open Reports Page**: http://127.0.0.1:8000/reports/
2. **Click on Map**: Select the location of the danger
3. **Fill Report Form**:
   - **Title**: "Poor Street Lighting"
   - **Description**: "Two main road completely dark at night"
   - **Severity**: Select from Low/Medium/High/Critical
4. **Submit**: Click "Submit Report" button
5. **Confirm**: Toast notification appears confirming submission

**Report Appears:**
- Immediately on the map as color-coded marker
- In sidebar report list
- Visible to all users and in route analysis

---

### Finding a Safe Route

**Via Navigation Page:**

1. **Open Navigation**: http://127.0.0.1:8000/navigation/
2. **Enter Locations**:
   - **Source**: Starting point (e.g., "New Delhi Station")
   - **Destination**: End point (e.g., "India Gate")
3. **Find Route**: Click "Find Safest Route" button
4. **View Analysis**:
   - Safety score percentage displayed
   - Route marked on map
   - Danger zones highlighted
5. **Review Warnings** (if any):
   - Shows which communities have reported danger
   - Distance from route
   - Severity level of each zone

---

### Understanding Safety Scores

**Score Ranges:**
- **80-100%**: ✅ **SAFE** - Green badge
- **50-79%**: ⚠️ **MODERATE** - Yellow badge
- **0-49%**: ❌ **UNSAFE** - Red badge

**How Score is Calculated:**
```
Base: 100 points
- Low severity zone: -5 points
- Medium severity zone: -10 points
- High severity zone: -20 points
- Critical severity zone: -30 points

Example: Route through 1 critical + 1 high zone
100 - 30 - 20 = 50% (MODERATE)
```

---

## Marker Colors & Meanings

| Color | Severity | Radius | Meaning |
|-------|----------|--------|---------|
| 🟢 Green | Low | 100m | Minor issue, generally safe |
| 🟡 Yellow | Medium | 250m | Moderate concern, use caution |
| 🟠 Orange | High | 400m | Significant danger reported |
| 🔴 Red | Critical | 600m | Critical danger, avoid if possible |

---

## Admin Management

### Accessing Admin Panel
1. Go to: http://127.0.0.1:8000/admin/
2. Log in with superuser credentials
3. Select "Community Reports"

### Verify a Report
1. Find the report in the list
2. Click on it to open details
3. Check the `is_verified` checkbox
4. Click Save

### Delete a Report
1. Select one or more reports using checkboxes
2. Choose "Delete selected reports" from action dropdown
3. Click Go
4. Confirm deletion

### Filter Reports
- By **Severity**: Low, Medium, High, Critical
- By **Date**: Last 24 hours, 7 days, 30 days
- By **Status**: Verified or Unverified

### Search Reports
- Search by report **Title**
- Search by **Description** content
- Search by **Reporter Username**

---

## API Usage Examples

### Create a Report (Python)
```python
import requests
import json

url = 'http://127.0.0.1:8000/api/reports/'
report_data = {
    'title': 'Broken Streetlight',
    'description': 'No lights on Main Street at night',
    'severity': 'high',
    'latitude': 28.6139,
    'longitude': 77.2090
}

response = requests.post(url, json=report_data)
print(response.json())
# Output: {"id": 1, "title": "...", ...}
```

### Get All Reports (JavaScript)
```javascript
fetch('/api/reports/')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.reports.length} reports`);
    data.reports.forEach(report => {
      console.log(`${report.title} - ${report.severity}`);
    });
  });
```

### Analyze Route for Safety (cURL)
```bash
curl -X POST http://127.0.0.1:8000/api/route-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "route": [[28.61, 77.20], [28.62, 77.21], [28.63, 77.22]],
    "start_lat": 28.61,
    "start_lon": 77.20,
    "end_lat": 28.63,
    "end_lon": 77.22
  }'
```

---

## Keyboard Shortcuts

**Navigation Page:**
- `Ctrl+L`: Focus on location input
- `Enter`: Submit location and find route

**Reports Page:**
- `Escape`: Close report modal
- `+/-`: Zoom in/out on map

---

## Notifications & Alerts

### Toast Notifications (Reports Page)
- ✅ **Success**: "Report submitted successfully"
- ❌ **Error**: "Failed to submit report"
- ⚠️ **Warning**: "Please enable location access"

### Proximity Alerts (Navigation Page)
- Appear when within 200m of danger zone
- Show distance to danger zone
- Indicate severity level
- Auto-dismiss after 6 seconds

---

## Privacy & Security

### Data Collected
- Location (latitude/longitude)
- Report details (title, description)
- Severity assessment
- Timestamp
- Optional: User who submitted (if logged in)

### Data Privacy
- Reports visible to all users
- No personal information required to submit
- Location alone doesn't identify individuals
- Anonymous reports fully supported

### Security Features
- CSRF protection on all endpoints
- Input validation on all fields
- SQL injection prevention via Django ORM
- Admin-only delete and verify operations

---

## Troubleshooting

### "Location access denied"
**Solution**: 
- Allow location permission in browser settings
- Try incognito/private window
- Check browser console for errors

### Map not loading
**Solution**:
- Check internet connection (needs CDN access)
- Clear browser cache
- Try different browser
- Check browser console for errors

### Reports not showing
**Solution**:
- Refresh page (F5)
- Check database connection
- Verify Django server is running
- Check browser console errors

### Route analysis not working
**Solution**:
- Verify source and destination are valid
- Check location names are spelled correctly
- Try again after a moment (Nominatim has rate limits)
- Check server logs for errors

### Admin panel showing no reports
**Solution**:
- Run `python manage.py migrate` again
- Clear browser cache
- Log out and log back in
- Check user has admin/staff privileges

---

## Performance Tips

### For Better Performance
1. **Clear browser cache** periodically
2. **Limit report range** in sidebar (scroll through)
3. **Close unused tabs** to reduce memory usage
4. **Refresh page** if map appears frozen
5. **Use recent browser version** for best performance

### Server Optimization
1. Monitor database size
2. Archive old reports periodically
3. Implement caching for frequently accessed routes
4. Use CDN for static files in production

---

## Testing Checklist

- [ ] Can create a new report
- [ ] New report appears on map immediately
- [ ] Marker color matches severity level
- [ ] Sidebar shows new report
- [ ] Can click report in sidebar to center map
- [ ] Can find a route between two locations
- [ ] Safety score displays correctly
- [ ] Warning card shows if route crosses danger zones
- [ ] Proximity alerts appear when near danger
- [ ] Admin panel can verify reports
- [ ] Admin panel can delete reports
- [ ] Reports persist after page refresh

---

## Common Questions

**Q: Can anyone create a report?**
A: Yes! Anyone can create reports anonymously. No login required.

**Q: How long are reports stored?**
A: Indefinitely, but admins can delete false/resolved reports.

**Q: Is my location tracked?**
A: Only when you enable geolocation on the navigation page. You control this permission.

**Q: Can I edit a report after submission?**
A: Not currently. You can report the issue again or contact admin to delete old report.

**Q: How are false reports handled?**
A: Admins can verify reports as authentic or delete them if false.

**Q: Does the safety score change?**
A: Yes, it updates in real-time as new reports are added and danger zones are detected.

**Q: Can I export report data?**
A: Via Django admin panel, use export functions or API endpoints.

---

## Support

For issues or feature requests:
1. Check this guide first
2. Review project documentation
3. Check browser console for errors
4. Contact development team

---

**Last Updated**: 2026-06-10
**Version**: 1.0
**Status**: Production Ready ✅
