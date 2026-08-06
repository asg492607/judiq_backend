$content = Get-Content -Path 'index.html' -Raw
$content = $content.Replace('class="result-card"', 'class="result-card animate-fade-in-up"')
Set-Content -Path 'index.html' -Value $content -NoNewline
