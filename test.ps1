$json = '{"case_id": "TEST-01", "case_type": "cheque_bounce", "cheque_present": true, "notice_sent": true, "amount": 500000.0, "description": "test"}'
$res = Invoke-RestMethod -Uri 'https://cheque-bounce-ragbased.onrender.com/api/v1/analyze' -Method Post -Body $json -ContentType 'application/json'
$res.issues | ConvertTo-Json -Depth 5
