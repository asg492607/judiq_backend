$content = Get-Content -Path 'response_builder.py' -Raw
$target = "        final_weaknesses = structured_weaknesses`r`n        final_issues = [r for r in structured_weaknesses if r['severity'] in ['FATAL', 'CRITICAL', 'HIGH']]"
$replacement = "        for r in structured_weaknesses:`r`n            r['text'] = r.get('risk', '')`r`n`r`n        final_weaknesses = structured_weaknesses`r`n        final_issues = [r for r in structured_weaknesses if r.get('severity') in ['FATAL', 'CRITICAL', 'HIGH']]"

if ($content.Contains($target)) {
    $content = $content.Replace($target, $replacement)
    Set-Content -Path 'response_builder.py' -Value $content -NoNewline
    Write-Host "Success CRLF"
} else {
    $targetLF = "        final_weaknesses = structured_weaknesses`n        final_issues = [r for r in structured_weaknesses if r['severity'] in ['FATAL', 'CRITICAL', 'HIGH']]"
    $replacementLF = "        for r in structured_weaknesses:`n            r['text'] = r.get('risk', '')`n`n        final_weaknesses = structured_weaknesses`n        final_issues = [r for r in structured_weaknesses if r.get('severity') in ['FATAL', 'CRITICAL', 'HIGH']]"
    if ($content.Contains($targetLF)) {
        $content = $content.Replace($targetLF, $replacementLF)
        Set-Content -Path 'response_builder.py' -Value $content -NoNewline
        Write-Host "Success LF"
    } else {
        Write-Host "Target not found"
    }
}
