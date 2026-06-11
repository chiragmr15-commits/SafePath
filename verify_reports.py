import urllib.request
import json

url = 'http://127.0.0.1:8000/api/reports/'
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        print('=== Database Verification ===')
        print(f'Total Reports: {len(data["reports"])}')
        
        severity_counts = {}
        for report in data['reports']:
            severity = report['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print('\nReports by Severity:')
        for sev in ['low', 'medium', 'high', 'critical']:
            count = severity_counts.get(sev, 0)
            print(f'  {sev.upper()}: {count}')
        
        print('\nLatest Report:')
        if data['reports']:
            latest = data['reports'][0]
            print(f'  Title: {latest["title"]}')
            print(f'  Severity: {latest["severity"]}')
            print(f'  Location: ({latest["latitude"]}, {latest["longitude"]})')
            
except Exception as e:
    print(f'Error: {e}')
