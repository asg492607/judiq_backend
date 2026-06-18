$path = "c:\Users\Atharva\OneDrive\Desktop\Level_0judiq\backend\response_builder.py"
$content = [System.IO.File]::ReadAllText($path)

# 1. Target for fatal_defect
$target1 = @'
        structured_weaknesses = []
        if limitation.get("is_premature"):
            structured_weaknesses.append({"risk": "Premature Complaint", "severity": "FATAL", "detail": "Non-curable defect under NI Act."})
        elif limitation.get("notice_delay_days", 0) > 0:
             structured_weaknesses.append({"risk": "Notice Delayed", "severity": "HIGH", "detail": f"Statutory notice delayed by {limitation['notice_delay_days']} days. Application for condonation mandatory."})
        
        if not case_data.get("proof_present", True):
             structured_weaknesses.append({"risk": "Missing Proof", "severity": "HIGH", "detail": "Proof (Cheque/Memo/Notice) is missing."})
'@

# 1. Replacement for fatal_defect
$replacement1 = @'
        structured_weaknesses = []
        fatal_defect = case_data.get("fatal_defect") or engine_result.get("failure_point")
        if fatal_defect:
             structured_weaknesses.append({
                 "risk": str(fatal_defect),
                 "severity": "FATAL",
                 "detail": f"This case has a fatal statutory/procedural defect: {fatal_defect}. It is highly recommended not to file or to withdraw."
             })

        if limitation.get("is_premature"):
            structured_weaknesses.append({"risk": "Premature Complaint", "severity": "FATAL", "detail": "Non-curable defect under NI Act."})
        elif limitation.get("notice_delay_days", 0) > 0:
             structured_weaknesses.append({"risk": "Notice Delayed", "severity": "HIGH", "detail": f"Statutory notice delayed by {limitation['notice_delay_days']} days. Application for condonation mandatory."})
        
        if not case_data.get("proof_present", True):
             structured_weaknesses.append({"risk": "Missing Proof", "severity": "HIGH", "detail": "Proof (Cheque/Memo/Notice) is missing."})
'@

# 2. Target for text/title/description duplication
$target2 = @'
        for r in structured_weaknesses:
            r['text'] = r.get('risk', '')
'@

# 2. Replacement for text/title/description duplication
$replacement2 = @'
        for r in structured_weaknesses:
            r['text'] = r.get('risk', '')
            r['title'] = r.get('risk', '')
            r['description'] = r.get('detail', '')
'@

# Normalize newlines to \n to ensure robust matching
$contentNormalized = $content -replace "`r`n", "`n"
$target1Normalized = $target1 -replace "`r`n", "`n"
$replacement1Normalized = $replacement1 -replace "`r`n", "`n"
$target2Normalized = $target2 -replace "`r`n", "`n"
$replacement2Normalized = $replacement2 -replace "`r`n", "`n"

if ($contentNormalized.Contains($target1Normalized)) {
    $contentNormalized = $contentNormalized.Replace($target1Normalized, $replacement1Normalized)
    Write-Output "Successfully matched and replaced fatal_defect block!"
} else {
    Write-Warning "Target 1 (fatal_defect block) NOT found!"
}

if ($contentNormalized.Contains($target2Normalized)) {
    $contentNormalized = $contentNormalized.Replace($target2Normalized, $replacement2Normalized)
    Write-Output "Successfully matched and replaced key duplication block!"
} else {
    Write-Warning "Target 2 (key duplication block) NOT found!"
}

[System.IO.File]::WriteAllText($path, $contentNormalized)
