$scriptPath = "script.js"
$content = Get-Content $scriptPath -Raw

# We will remove the exact string blocks of the functions.

$classifyApiError = '(?s)function classifyApiError\(err, httpStatus\).*?\r?\n\}\r?\n'
$fetchWithRetry = '(?s)/\*\*[\s\*]*Fetch with automatic retry on transient failures\..*?\*/\r?\nasync function fetchWithRetry\(url, options = \{\}, maxRetries = 2, baseDelay = 2000\).*?\r?\n\}\r?\n'
$showAnalysisError = '(?s)/\*\*[\s\*]*Show a structured error modal/banner for analysis failures\..*?\*/\r?\nfunction showAnalysisError\(errorInfo\).*?\r?\n\}\r?\n'
$globalApiBoundary = '(?s)JudiQEvents\.bind\(window, ''judiq:api-error'', function handleGlobalApiBoundary\(event\).*?\r?\n\}\);\r?\n'
$initNetworkMonitor = '(?s)// Network status banner.*?function initNetworkMonitor\(\).*?\r?\n\}\r?\n'

$content = [regex]::Replace($content, $classifyApiError, "")
$content = [regex]::Replace($content, $fetchWithRetry, "")
$content = [regex]::Replace($content, $showAnalysisError, "")
$content = [regex]::Replace($content, $globalApiBoundary, "")
$content = [regex]::Replace($content, $initNetworkMonitor, "")

Set-Content $scriptPath $content
