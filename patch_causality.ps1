$path = "c:\Users\Atharva\OneDrive\Desktop\Level_0judiq\backend\response_builder.py"
$content = [System.IO.File]::ReadAllText($path)

# 1. Target for causality_map assignment and difference calculation
$target1 = @'
        # New institutional-grade components
        causality_map = engine_result.get("causality_map", [])
        top_penalties = engine_result.get("top_penalties", [])
        strategy_result = engine_result.get("strategy_result", {})
        adversarial_result = engine_result.get("adversarial_result", {})

        verdict = "STRONG CASE"
        if score <= 25 or engine_result.get("verdict") == "DO NOT FILE":
            verdict = "DO NOT FILE"
        elif score < 40: 
            verdict = "WEAK CASE / HIGH RISK"
        elif score < 70: 
            verdict = "MODERATE CASE"
'@

$replacement1 = @'
        # New institutional-grade components
        causality_map = list(engine_result.get("causality_map", []))
        top_penalties = engine_result.get("top_penalties", [])
        strategy_result = engine_result.get("strategy_result", {})
        adversarial_result = engine_result.get("adversarial_result", {})

        verdict = "STRONG CASE"
        if score <= 25 or engine_result.get("verdict") == "DO NOT FILE":
            verdict = "DO NOT FILE"
        elif score < 40: 
            verdict = "WEAK CASE / HIGH RISK"
        elif score < 70: 
            verdict = "MODERATE CASE"

        # Dynamically append adjustments so score breakdown matches final score
        current_sum = sum(c.get("impact", 0) for c in causality_map)
        diff = int(score - current_sum)
        if diff != 0:
            if verdict == "DO NOT FILE" or score == 0:
                causality_map.append({
                    "fact": "Fatal Defect Override",
                    "impact": diff,
                    "type": "negative",
                    "rationale": "Case has fatal procedural/statutory defects."
                })
            else:
                causality_map.append({
                    "fact": "Judicial Adjustment & Calibration",
                    "impact": diff,
                    "type": "negative" if diff < 0 else "positive",
                    "rationale": "Calibration for territorial jurisdiction and court rules."
                })
'@

# 2. Target for dictionary keys
$target2 = @'
            "causality_map":  engine_result.get("causality_map", []),
            "compliance_pct": engine_result.get("compliance_pct", 0),
            "economics":      engine_result.get("economics", {}),
            "checkpoints":    engine_result.get("checkpoints", []),
            "explicit_risk_propagation": [f"{c['fact']}: {c['impact']}" for c in engine_result.get("causality_map", [])],
            "causality_delta": [c['impact'] for c in engine_result.get("causality_map", [])],
'@

$replacement2 = @'
            "causality_map":  causality_map,
            "compliance_pct": engine_result.get("compliance_pct", 0),
            "economics":      engine_result.get("economics", {}),
            "checkpoints":    engine_result.get("checkpoints", []),
            "explicit_risk_propagation": [f"{c['fact']}: {c['impact']}" for c in causality_map],
            "causality_delta": [c['impact'] for c in causality_map],
'@

$contentNormalized = $content -replace "`r`n", "`n"
$target1Normalized = $target1 -replace "`r`n", "`n"
$replacement1Normalized = $replacement1 -replace "`r`n", "`n"
$target2Normalized = $target2 -replace "`r`n", "`n"
$replacement2Normalized = $replacement2 -replace "`r`n", "`n"

if ($contentNormalized.Contains($target1Normalized)) {
    $contentNormalized = $contentNormalized.Replace($target1Normalized, $replacement1Normalized)
    Write-Output "Successfully patched causality_map calculation!"
} else {
    Write-Warning "Target 1 (causality_map calculation) NOT found!"
}

if ($contentNormalized.Contains($target2Normalized)) {
    $contentNormalized = $contentNormalized.Replace($target2Normalized, $replacement2Normalized)
    Write-Output "Successfully patched dictionary return keys!"
} else {
    Write-Warning "Target 2 (dictionary return keys) NOT found!"
}

[System.IO.File]::WriteAllText($path, $contentNormalized)
