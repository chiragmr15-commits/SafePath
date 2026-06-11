# SOS & Emergency Contact System - Quick Reference Card

## 🎯 Quick Links

| Component | File | Purpose |
|-----------|------|---------|
| Models | `safety/models.py` | EmergencyContact, SOSAlert, SOSDeliveryLog |
| Views/APIs | `safety/views.py` | All SOS endpoints |
| Frontend | `templates/emergency_contacts.html` | User interface |
| SMS | `safety/sms_sender.py` | SMS sending service |
| Routes | `safety/urls.py` | URL endpoints |
| Migrations | `safety/migrations/0003_*` | Database schema |

---

## 📱 API Endpoints

### Emergency Contacts
```
GET    /api/emergency-contacts/              List contacts
POST   /api/emergency-contacts/              Add contact
PUT    /api/emergency-contacts/<id>/         Update contact
DELETE /api/emergency-contacts/<id>/         Delete contact
```

### SOS Alerts
```
POST   /api/send-sos/                        Send SOS alert
GET    /api/sos-history/                     View history
```

---

## 🔧 Configuration

```bash
# Create .env from template
cp .env.example .env

# Edit .env with SMS service
SMS_SERVICE=textbelt  # or: twilio, fast2sms
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
FAST2SMS_API_KEY=...

# Restart server
python manage.py runserver
```

---

## 📊 Database Schema

### EmergencyContact
```sql
id | user_id | name | relationship | phone_number | alternate_number | created_at | updated_at
```

### SOSAlert
```sql
id | user_id | latitude | longitude | status | created_at | updated_at
```

### SOSDeliveryLog
```sql
id | sos_alert_id | contact_id | delivery_status | delivered_at | error_message
```

---

## 🔐 Security Decorators

```python
@login_required          # Require authentication
@csrf_protect           # CSRF token validation
@require_http_methods   # Validate HTTP method
@csrf_exempt            # Skip CSRF for AJAX
```

---

## 📝 Request/Response Examples

### Add Emergency Contact
```json
POST /api/emergency-contacts/

Request:
{
  "name": "Mom",
  "relationship": "mother",
  "phone_number": "+91 9876543210",
  "alternate_number": "+91 9876543211"
}

Response:
{
  "id": 1,
  "name": "Mom",
  "relationship": "mother",
  "phone_number": "+91 9876543210",
  "alternate_number": "+91 9876543211",
  "created_at": "2026-06-11T14:30:00Z"
}
```

### Send SOS
```json
POST /api/send-sos/

Request:
{
  "latitude": 12.9716,
  "longitude": 77.5946
}

Response:
{
  "sos_id": 1,
  "success": true,
  "delivered_count": 3,
  "failed_count": 0,
  "total_contacts": 3,
  "delivered_to": [
    {"id": 1, "name": "Mom", "phone": "+91...", "status": "delivered"},
    {"id": 2, "name": "Dad", "phone": "+91...", "status": "delivered"},
    {"id": 3, "name": "Sister", "phone": "+91...", "status": "delivered"}
  ],
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "maps_link": "https://maps.google.com/?q=12.9716,77.5946"
  },
  "timestamp": "2026-06-11 14:30:45",
  "message": "SOS sent to 3/3 contacts"
}
```

### Get SOS History
```json
GET /api/sos-history/?limit=10&offset=0

Response:
{
  "history": [
    {
      "id": 1,
      "latitude": 12.9716,
      "longitude": 77.5946,
      "status": "sent",
      "created_at": "2026-06-11T14:30:00Z",
      "maps_link": "https://maps.google.com/?q=12.9716,77.5946",
      "contacts_notified": 3,
      "deliveries": [
        {
          "contact_name": "Mom",
          "phone": "+91 9876543210",
          "status": "delivered",
          "delivered_at": "2026-06-11T14:30:05Z"
        }
      ]
    }
  ],
  "total": 5,
  "returned": 1
}
```

---

## 🧪 Testing

### Unit Test Example
```python
from django.test import TestCase
from django.contrib.auth.models import User
from safety.models import EmergencyContact

class EmergencyContactTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='pass123'
        )
    
    def test_add_contact(self):
        contact = EmergencyContact.objects.create(
            user=self.user,
            name='Mom',
            relationship='mother',
            phone_number='+91 9876543210'
        )
        self.assertEqual(contact.name, 'Mom')
```

### Integration Test
```python
from django.test import Client

client = Client()
client.login(username='test', password='pass123')

# Add contact
response = client.post('/api/emergency-contacts/', {
    'name': 'Mom',
    'relationship': 'mother',
    'phone_number': '+91 9876543210'
})
assert response.status_code == 201

# Send SOS
response = client.post('/api/send-sos/', {
    'latitude': 12.9716,
    'longitude': 77.5946
})
assert response.status_code == 200
```

---

## 🐛 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Not logged in | Login first |
| 400 Bad Request | Invalid data | Check JSON format |
| 404 Not Found | Contact doesn't exist | Verify contact ID |
| 500 Server Error | SMS service down | Check SMS service status |
| Location permission | Browser blocked location | Allow location in settings |

---

## 📈 Performance Tips

- **Pagination**: Use `?limit=50&offset=0` for history
- **Caching**: Cache contact list for frequent access
- **Batch SMS**: Send to multiple contacts concurrently
- **Database**: Index on `user_id` for faster queries
- **CDN**: Host static files on CDN for faster loads

---

## 🚀 Deployment

```bash
# Collect static files
python manage.py collectstatic

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Start production server
gunicorn core.wsgi --bind 0.0.0.0:8000
```

---

## 📚 Reference Documentation

- User Guide: `SOS_EMERGENCY_SYSTEM_GUIDE.md`
- Implementation: `SOS_IMPLEMENTATION_SUMMARY.md`
- Models: `safety/models.py`
- Views: `safety/views.py`
- Frontend: `templates/emergency_contacts.html`

---

## 🆘 Troubleshooting Command Line

```bash
# Check Django setup
python manage.py check

# Show migrations status
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Create test data
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.create_user('test', password='test123')
>>> from safety.models import EmergencyContact
>>> EmergencyContact.objects.create(user=u, name='Mom', phone_number='+1234567890')

# Check SMS configuration
python manage.py shell
>>> import os
>>> print(f"SMS Service: {os.getenv('SMS_SERVICE')}")
>>> print(f"TextBelt: {os.getenv('TEXTBELT_API_KEY')}")
```

---

## 💡 Pro Tips

- **Always backup database before major changes**
- **Test SMS service with real numbers first**
- **Keep emergency contacts updated**
- **Monitor SMS delivery status regularly**
- **Use HTTPS in production**
- **Set up error logging/monitoring**
- **Cache contact list for performance**
- **Implement rate limiting for SOS**
- **Keep API keys secure (use .env)**
- **Test with multiple phone numbers**

---

## 📞 Support

- **Issues**: Check Django server logs
- **SMS Issues**: Verify SMS service configuration
- **Database**: Run `python manage.py dbshell`
- **Logs**: Check `error.log` and `debug.log`

---

Last Updated: June 2026
Version: 1.0.0
Status: Production Ready ✅
