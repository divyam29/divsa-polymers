#!/usr/bin/env python
import urllib.request
import urllib.parse

data = {
    'name': 'Jane Doe',
    'email': 'jane@example.com',
    'phone': '9876543211',
    'city': 'Delhi',
    'business': 'Manufacturing'
}

try:
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request('http://localhost:5000/submit-inquiry', data=encoded_data)
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.status}")
        print("✓ Form submitted successfully")
except urllib.error.HTTPError as e:
    if e.code == 302:
        print("✓ Form submitted successfully (redirected)")
    else:
        print(f"Status Code: {e.code}")
except Exception as e:
    print(f"✗ Error: {e}")
