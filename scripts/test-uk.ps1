$root = Split-Path -Parent $PSScriptRoot

$body = @{
  model = "kokoro"
  input = "Hello! Welcome to Kokoro Serve. Learning English can be easy and enjoyable."
  voice = "bf_emma"
  response_format = "mp3"
  speed = 1.0
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://localhost:9000/v1/audio/speech" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "$root\output\uk.mp3"

Write-Host "Generated: $root\output\uk.mp3"
