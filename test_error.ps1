try {
    $json = '{"case_id": "TEST-01", "case_type": "cheque_bounce", "cheque_present": true, "notice_sent": true, "amount": 500000.0, "description": "test"}'
    $res = Invoke-WebRequest -Uri 'https://cheque-bounce-ragbased.onrender.com/api/v1/analyze' -Method Post -Body $json -ContentType 'application/json'
    Write-Output $res.Content
} catch {
    $res = $_.Exception.Response
    $stream = $res.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $body = $reader.ReadToEnd()
    Write-Output "Status: $($res.StatusCode)"
    Write-Output "Body: $body"
}
