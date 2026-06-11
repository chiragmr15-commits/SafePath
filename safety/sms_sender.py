"""
SMS Sending Utility for SOS Alerts
Supports Twilio, Fast2SMS, and TextBelt APIs
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, List, Tuple

class SMSSender:
    """
    Send SMS using configured SMS service
    Supported services: twilio, fast2sms, textbelt
    """
    
    SERVICE = os.getenv('SMS_SERVICE', 'textbelt')  # Default to TextBelt
    
    @staticmethod
    def send_sms(phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Send SMS to a single phone number
        Returns: (success: bool, message: str)
        """
        if not phone_number or not message:
            return False, "Phone number and message are required"
        
        # Try to send based on configured service
        if SMSSender.SERVICE == 'twilio':
            return SMSSender._send_twilio(phone_number, message)
        elif SMSSender.SERVICE == 'fast2sms':
            return SMSSender._send_fast2sms(phone_number, message)
        else:  # Default to textbelt
            return SMSSender._send_textbelt(phone_number, message)
    
    @staticmethod
    def _send_twilio(phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS using Twilio API"""
        try:
            from twilio.rest import Client
        except ImportError:
            return False, "Twilio library not installed. Install with: pip install twilio"
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_FROM_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            return False, "Twilio credentials not configured"
        
        try:
            client = Client(account_sid, auth_token)
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            return True, f"SMS sent successfully (ID: {message_obj.sid})"
        except Exception as e:
            return False, f"Twilio error: {str(e)}"
    
    @staticmethod
    def _send_fast2sms(phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS using Fast2SMS API"""
        api_key = os.getenv('FAST2SMS_API_KEY')
        
        if not api_key:
            return False, "Fast2SMS API key not configured"
        
        try:
            # Fast2SMS requires phone number with country code (e.g., +91XXXXXXXXXX or 91XXXXXXXXXX)
            phone = phone_number.replace('+', '')
            if not phone.startswith('91'):  # Add India country code if missing
                if len(phone) == 10:
                    phone = '91' + phone
            
            url = 'https://www.fast2sms.com/dev/bulkSMS'
            headers = {
                'authorization': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = urllib.parse.urlencode({
                'sender_id': 'SafePath',
                'message': message,
                'language': 'english',
                'route': 'p',
                'numbers': phone
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('return'):
                    return True, "SMS sent successfully"
                else:
                    return False, f"Fast2SMS error: {result.get('message', 'Unknown error')}"
        
        except Exception as e:
            return False, f"Fast2SMS error: {str(e)}"
    
    @staticmethod
    def _send_textbelt(phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS using TextBelt API (Free service)"""
        try:
            url = 'https://textbelt.com/text'
            
            # TextBelt works best with +1 for US/Canada, or +country_code for others
            phone = phone_number.strip()
            if not phone.startswith('+'):
                if phone.startswith('91'):  # India
                    phone = '+' + phone
                elif len(phone) == 10:  # Assume India if 10 digits
                    phone = '+91' + phone
            
            data = urllib.parse.urlencode({
                'phone': phone,
                'message': message,
                'key': 'textbelt'  # Free tier
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('success'):
                    return True, "SMS sent successfully"
                else:
                    return False, f"TextBelt error: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return False, f"TextBelt error: {str(e)}"
    
    @staticmethod
    def send_bulk_sms(phone_numbers: List[str], message: str) -> Dict[str, Tuple[bool, str]]:
        """
        Send SMS to multiple phone numbers
        Returns: {phone: (success, message), ...}
        """
        results = {}
        for phone in phone_numbers:
            results[phone] = SMSSender.send_sms(phone, message)
        return results


# For Python 2/3 compatibility
try:
    import urllib.parse
except ImportError:
    import urllib as urllib_module
    urllib.parse = urllib_module.parse
