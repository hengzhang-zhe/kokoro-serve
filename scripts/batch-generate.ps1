param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,

    [string]$BaseUrl = "http://localhost:9000",

    [string]$OutputRoot = ".\\output",

    [string]$ObjectKeyPrefix = "audio/kokoro",

    [double]$Speed = 1.0
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $InputFile)) { throw "Input file not found: $InputFile" }

$source = Get-Content $InputFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($source.schemaVersion -ne "typingo-tts-export/v1") {
    throw "Unsupported input schemaVersion: $($source.schemaVersion)"
}

$defaultVoices = @(
    [pscustomobject]@{ voice = "af_heart";   locale = "en-US"; gender = "female"; accent = "US" },
    [pscustomobject]@{ voice = "am_michael"; locale = "en-US"; gender = "male";   accent = "US" },
    [pscustomobject]@{ voice = "bf_emma";    locale = "en-GB"; gender = "female"; accent = "UK" },
    [pscustomobject]@{ voice = "bm_george";  locale = "en-GB"; gender = "male";   accent = "UK" }
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$batchRoot = Join-Path $OutputRoot "batch-$timestamp"
$audioRoot = Join-Path $batchRoot "audio\\kokoro"
New-Item -ItemType Directory -Force -Path $audioRoot | Out-Null

$assets = New-Object System.Collections.Generic.List[object]
$failed = New-Object System.Collections.Generic.List[object]
$total = @($source.items).Count
$index = 0

foreach ($item in $source.items) {
    $index++
    Write-Host "[$index/$total] $($item.contentId) $($item.type): $($item.text)"

    $profiles = if ($null -ne $item.variants -and @($item.variants).Count -gt 0) {
        @($item.variants)
    } else {
        $defaultVoices
    }

    foreach ($profile in $profiles) {
        $contentDir = Join-Path $audioRoot $item.contentId
        New-Item -ItemType Directory -Force -Path $contentDir | Out-Null

        $filename = "$($profile.voice).mp3"
        $file = Join-Path $contentDir $filename
        $objectKey = "$ObjectKeyPrefix/$($item.contentId)/$filename"

        try {
            $body = @{
                model = "kokoro"
                input = $item.text
                voice = $profile.voice
                response_format = "mp3"
                speed = $Speed
            } | ConvertTo-Json

            Invoke-WebRequest `
                -Uri "$BaseUrl/v1/audio/speech" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body `
                -OutFile $file

            $hash = (Get-FileHash -Path $file -Algorithm SHA256).Hash.ToLowerInvariant()
            $size = (Get-Item $file).Length

            $assets.Add([pscustomobject]@{
                contentId = $item.contentId
                role = "primary"
                locale = $profile.locale
                voice = $profile.voice
                provider = "kokoro"
                storageProvider = "local"
                bucket = $null
                objectKey = $objectKey
                sourceUrl = $null
                checksumSha256 = $hash
                mimeType = "audio/mpeg"
                sizeBytes = $size
                durationSeconds = $null
            })

            Write-Host "  OK $($profile.accent)-$($profile.gender) $($profile.voice) -> $objectKey"
        }
        catch {
            $failed.Add([pscustomobject]@{
                contentId = $item.contentId
                voice = $profile.voice
                message = $_.Exception.Message
            })
            Write-Warning "  FAILED $($profile.voice): $($_.Exception.Message)"
        }
    }
}

$manifest = [pscustomobject]@{
    schemaVersion = "typingo-audio-manifest/v1"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    provider = "kokoro"
    model = "hexgrad/Kokoro-82M"
    assets = $assets
    failed = $failed
}

$manifestPath = Join-Path $batchRoot "audio-manifest.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host ""
Write-Host "Batch complete"
Write-Host "Audio directory : $batchRoot\\audio"
Write-Host "Manifest        : $manifestPath"
Write-Host "Generated assets: $($assets.Count)"
Write-Host "Failed assets   : $($failed.Count)"
