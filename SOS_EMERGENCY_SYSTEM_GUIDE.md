# SOS & Emergency Contact Management System Guide

## Overview

The SafePath AI **Emergency Contact & SOS System** provides a professional way to manage emergency contacts and send SOS alerts to pre-registered contacts when in danger. The system automatically captures your current GPS location and sends SMS notifications to all emergency contacts.

---

## Features

### 1. **Emergency Contact Management**
- **Add Contacts**: Store up to unlimited emergency contacts
- **Contact Details**:
  - Contact Name
  - Relationship (Mother, Father, Brother, Sister, Friend, Guardian, Police, Other)
  - Primary Phone Number
  - Alternate Phone Number (optional)
- **Edit Contacts**: Modify contact details anytime
- **Delete Contacts**: Remove contacts you no longer need

### 2. **SOS Alert System**
- **One-Click SOS**: Send emergency alert with a single button
- **Location Sharing**: Automatically captures your GPS location
- **SMS Notification**: Sends SMS to all emergency contacts with:
  - Emergency alert message
  - Your live location (Google Maps link)
  - Current timestamp
  - App information
- **Confirmation Modal**: Prevents accidental SOS activation with confirmation dialog
- **Real-time Status**: See delivery status for each contact (Delivered/Failed/Pending)

### 3. **SOS History & Tracking**
- **Alert History**: View all past SOS alerts
- **Delivery Status**: Track which contacts received your alert
- **Location Links**: Quick access to location on Google Maps for each alert
- **Timestamp**: Know exactly when each alert was sent

### 4. **SMS Integration**
- **Multiple SMS Services**: Choose from Twilio, Fast2SMS, or TextBelt
- **Environment Configuration**: API credentials stored securely in `.env` file
- **Delivery Tracking**: Know if SMS was successfully delivered
- **Error Handling**: Graceful error messages if SMS fails

---

## How to Use

### Step 1: Add Emergency Contacts

1. Navigate to **Emergency Contacts & SOS** from the dashboard
2. Click the **"Add Contact"** button
3. Fill in the contact details:
   - **Contact Name**: Who this person is (e.g., "Mom")
   - **Relationship**: Select from dropdown
   - **Phone Number**: International format recommended (e.g., +91 9876543210)
   - **Alternate Number**: Optional backup number
4. Click **"Save Contact"**
5. Repeat for all emergency contacts

### Step 2: Send SOS Alert

1. In the **Emergency Contacts & SOS** page, see the prominent red **"SEND SOS"** button
2. Click the **SOS button**
3. A confirmation dialog appears asking:
   - "Are you sure you want to send an SOS alert?"
   - "Your location will be shared with all emergency contacts"
4. Click **"Cancel"** to abort or **"Send SOS"** to confirm
5. The system will:
   - Request your current GPS location
   - Display "Sending SOS..." while processing
   - Send SMS to all registered contacts
   - Show delivery status for each contact

### Step 3: View SOS History

1. Click the **"SOS History"** tab
2. View all past SOS alerts with:
   - Date & time of alert
   - Delivery status (Delivered/Failed)
   - Location link
   - List of notified contacts with delivery status

---

## Configuration

### Required: SMS Service Setup

The SOS system needs an SMS service to send alerts. Choose one:

#### Option 1: TextBelt (FREE, Recommended)
- **Setup Time**: 2 minutes (no signup needed!)
- **Cost**: Free tier available
- **Steps**:
  1. No configuration needed - works out of the box
  2. Uses free TextBelt API by default
  3. Supports SMS to 160+ countries

#### Option 2: Twilio (Paid)
- **Setup Time**: 15 minutes
- **Cost**: ~$0.01 per SMS
- **Steps**:
  1. Go to https://www.twilio.com/
  2. Create account and get credentials:
     - Account SID
     - Auth Token
     - From Phone Number
  3. Copy to `.env` file:
     ```
     SMS_SERVICE=twilio
     TWILIO_ACCOUNT_SID=your_account_sid
     TWILIO_AUTH_TOKEN=your_auth_token
     TWILIO_FROM_NUMBER=+1234567890
     ```

#### Option 3: Fast2SMS (India-based, Paid)
- **Setup Time**: 10 minutes
- **Cost**: ~$0.002 per SMS
- **Steps**:
  1. Go to https://www.fast2sms.com/
  2. Create account and get API Key
  3. Copy to `.env` file:
     ```
     SMS_SERVICE=fast2sms
     FAST2SMS_API_KEY=your_api_key
     ```

### Setup Instructions

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your chosen SMS service credentials

3. **Restart the application** for changes to take effect

4. **Test SOS** with a contact to verify SMS delivery

---

## SMS Message Format

When you send an SOS alert, your emergency contacts receive this message:

```
🚨 EMERGENCY ALERT

I may be in danger and need immediate help.

📍 My current location:
https://maps.google.com/?q=12.9716,77.5946

⏰ Time: 2026-06-11 14:30:45

Sent from SafePath AI
```

**Key Details**:
- Clear emergency indicator with 🚨
- Google Maps link (clickable on most phones)
- Your exact timestamp
- Identifies the source as SafePath AI

---

## Security & Privacy

### What Data is Shared?

**ONLY when you send SOS**:
- Current GPS location coordinates
- Current timestamp
- Contact list (implicit - alerts sent to your contacts)

**Never shared automatically**:
- Your location tracking
- Browsing history
- Profile information
- Contact details with third parties

### Data Protection

- Only logged-in users can access emergency contacts
- Only you can manage your contacts
- Only you can send SOS alerts from your account
- SMS delivery logs are stored locally
- Contacts cannot see each other's information

### Privacy Notes

- Contact phone numbers are encrypted in database
- SOS alerts are deleted after 90 days
- Emergency contacts cannot be accessed by other users
- GPS location is only used during SOS alert

---

## Important Tips

### ✅ Do This

- **Add trusted people**: Parents, siblings, close friends, partner
- **Include phone numbers**: Both primary and alternate numbers
- **Keep numbers updated**: Update if contacts change numbers
- **Test the system**: Send one SOS to verify it works
- **Have backup contacts**: At least 3-5 contacts recommended
- **Use international format**: +CountryCode-PhoneNumber
- **Enable location services**: Required for SOS to work

### ❌ Don't Do This

- **Don't add strangers**: Only trusted emergency contacts
- **Don't forget numbers**: Verify numbers before saving
- **Don't ignore failed deliveries**: Check if SMS service is working
- **Don't rely solely on SOS**: Also call 911/Police directly if possible
- **Don't share access**: Don't give others access to your account
- **Don't send false SOS**: Only for genuine emergencies

---

## Troubleshooting

### Issue: "No emergency contacts registered"

**Cause**: You haven't added any contacts yet

**Fix**: 
1. Click "Add Contact" button
2. Add at least one emergency contact
3. Try SOS again

### Issue: "SMS Failed to Deliver"

**Cause**: SMS service not properly configured

**Fix**:
1. Check that `.env` file exists and is filled correctly
2. Verify phone numbers are in correct international format
3. Check SMS service API key/credentials
4. Try with a different SMS service (e.g., switch to TextBelt)
5. Test with a known working phone number

### Issue: "Unable to get your location"

**Cause**: Location services disabled or permission denied

**Fix**:
1. **Enable Location Services**:
   - Browser > Settings > Location > Allow
   - Device > Settings > Location > On
2. **Grant Permissions**:
   - When prompted, click "Allow" for location access
3. **Use Desktop**: Use on a desktop/tablet with location enabled
4. **Check Browser**: Some browsers restrict location access

### Issue: SMS Sent But Not Received

**Cause**: Network issues or carrier problems

**Fix**:
1. Check that SMS service is configured correctly
2. Verify contact's phone number is correct
3. Check contact's phone has signal/SMS enabled
4. Try with a different SMS service
5. Add alternate phone number and try that

### Issue: Can't Add Contact - "This phone number is already added"

**Cause**: You already saved this number

**Fix**:
1. Edit the existing contact instead of adding new one
2. Or delete the old contact and add with different relationship
3. Use a different phone number if needed

---

## Emergency Procedures

### If You're In Danger

1. **Call 911 First** (or local police number)
   - Police response is faster than SMS
   - Give them your location directly
   
2. **Send SOS Alert**
   - Click SOS button
   - Confirm sending
   - Contacts will receive your location

3. **Move to Safety**
   - If possible, move to a safe location
   - Stay on phone with police
   - Keep phone battery charged

### If You Accidentally Send SOS

**Don't Panic!** SafePath AI tracks SOS alerts:

1. Contact your emergency contacts immediately
2. Call them to explain it was accidental
3. Share your current status
4. This helps you test the system (good practice!)

---

## API Reference (For Developers)

### Get Emergency Contacts
```
GET /api/emergency-contacts/
```

### Add Emergency Contact
```
POST /api/emergency-contacts/
Body: {
  "name": "Contact Name",
  "relationship": "mother|father|...",
  "phone_number": "+91XXXXXXXXXX",
  "alternate_number": "+91XXXXXXXXXX" (optional)
}
```

### Update Emergency Contact
```
PUT /api/emergency-contacts/<id>/
Body: { ... }
```

### Delete Emergency Contact
```
DELETE /api/emergency-contacts/<id>/
```

### Send SOS Alert
```
POST /api/send-sos/
Body: {
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

### Get SOS History
```
GET /api/sos-history/?limit=50&offset=0
```

---

## Frequently Asked Questions (FAQ)

**Q: How many contacts can I add?**
A: Unlimited. Add as many as you need.

**Q: Will my location be tracked always?**
A: No. Location is ONLY shared when you send SOS alert.

**Q: What if SMS delivery fails?**
A: Try again, verify phone numbers, or switch SMS service.

**Q: Can others see my emergency contacts?**
A: No. Only you can see and manage your contacts.

**Q: Is this app monitored 24/7?**
A: No. This is a self-service emergency alert system. Always call 911 for immediate police response.

**Q: How fast is the SOS alert sent?**
A: Usually within 2-5 seconds of confirmation.

**Q: Can I schedule SOS alerts?**
A: No. Currently manual only. Emergency requires immediate action.

**Q: What happens if my phone dies?**
A: SOS alert is not sent. Keep your battery charged.

**Q: Can I send SOS to one contact instead of all?**
A: Currently sends to all. Future feature planned for selective recipients.

**Q: How long are SOS alerts stored?**
A: Up to 90 days. View history within this period.

---

## Support & Feedback

- **Report Issues**: Contact support with error details
- **Feature Requests**: Suggest improvements
- **Safety Concerns**: Let us know about any concerns
- **Testing**: Help us test the system

---

## Emergency Numbers (India)

- **Police**: 100
- **Ambulance**: 102 or 108
- **Fire**: 101
- **Women Helpline**: 1091
- **Cybercrime**: 155260

**Always call Emergency Services FIRST. Use SafePath as backup.**

---

## Version Information

- **System**: SafePath AI - Emergency Contact & SOS
- **Version**: 1.0
- **Last Updated**: June 2026
- **Status**: Production Ready

---

## Legal Disclaimer

SafePath AI is a safety assistance tool, not a replacement for emergency services. For life-threatening situations:

1. **ALWAYS call 911 (or local emergency number) first**
2. Use SafePath SOS as a supplementary alert system
3. Keep your phone charged and location services enabled
4. Update emergency contacts regularly
5. Test the system periodically

**SafePath AI developers are not liable for:**
- Failure to deliver SMS alerts
- Network/carrier issues
- Incorrect contact information
- Delayed emergency response
- Device/location service failures

SafePath works best when used WITH proper emergency procedures, not as a replacement.

---

*Stay Safe. Stay Connected. Be Smart. 🛡️*
