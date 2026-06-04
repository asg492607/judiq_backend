$ErrorActionPreference = 'Stop'
$origJson = Get-Content criminal_knowledge_base.json -Raw | ConvertFrom-Json
$patchJson = Get-Content patch.json -Raw | ConvertFrom-Json

foreach ($prop in $patchJson.psobject.properties) {
    $name = $prop.name
    $val = $prop.value
    
    if ($origJson.vulnerability_models.psobject.properties.match($name).Count -gt 0) {
        $origJson.vulnerability_models.$name = $val
    } else {
        $origJson.vulnerability_models | Add-Member -MemberType NoteProperty -Name $name -Value $val
    }
}

$origJson | ConvertTo-Json -Depth 10 | Set-Content criminal_knowledge_base.json
