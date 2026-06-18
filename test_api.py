import urllib.request
import json

url = 'https://cheque-bounce-ragbased.onrender.com/api/v1/analyze'
data = json.dumps({
    "case_type": "cheque_bounce",
    "amount": 500000.0,
    "cheque_present": True,
    "notice_sent": True,
    "description": "test"
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(json.dumps(result.get("issues", []), indent=2))
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(e.read().decode())
