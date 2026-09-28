$root = Split-Path -Parent $PSScriptRoot

$text = @"
Welcome to Kokoro Serve.
Schedule. Tomato. Water. Advertisement.
Could you tell me where the nearest train station is?
"@

$voices = @(
  "af_heart",
  "af_bella",
  "am_michael",
  "bf_emma",
  "bm_george"
)

foreach ($voice in $voices) {
  $body = @{
    model = "kokoro"
    input = $text
    voice = $voice
    response_format = "mp3"
    speed = 1.0
  } | ConvertTo-Json

  $file = "$root\output\$voice.mp3"

  Invoke-WebRequest `
    -Uri "http://localhost:9000/v1/audio/speech" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -OutFile $file

  Write-Host "Generated: $file"
}
