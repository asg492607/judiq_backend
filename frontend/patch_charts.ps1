$path = "c:\Users\Atharva\OneDrive\Desktop\Level_0judiq\frontend\js\modules\charts.js"
$content = [System.IO.File]::ReadAllText($path)

if ($content.Contains("attackVectorsChart")) {
    $content = $content.Replace("attackVectorsChart", "attackChart")
    [System.IO.File]::WriteAllText($path, $content)
    Write-Output "Successfully patched charts.js globally!"
} else {
    Write-Warning "attackVectorsChart NOT found in charts.js!"
}
