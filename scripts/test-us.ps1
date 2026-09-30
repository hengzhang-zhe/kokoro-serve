$root = Split-Path -Parent $PSScriptRoot

$body = @{
  model = "kokoro"
  input = "Hello! Welcome to Typingo Kokoro. Learning English can be easy and enjoyable."
  voice = "af_heart"
  response_format = "mp3"
  speed = 1.0
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://localhost:9000/v1/audio/speech" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "$root\output\us.mp3"

Write-Host "Generated: $root\output\us.mp3"
