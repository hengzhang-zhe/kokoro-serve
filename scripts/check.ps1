$ErrorActionPreference = "Stop"
$base = "http://localhost:9000"

Write-Host "Health:"
Invoke-RestMethod "$base/health" | ConvertTo-Json -Depth 5

Write-Host "`nModels:"
Invoke-RestMethod "$base/v1/models" | ConvertTo-Json -Depth 5

Write-Host "`nVoices:"
Invoke-RestMethod "$base/v1/audio/voices" | ConvertTo-Json -Depth 5
