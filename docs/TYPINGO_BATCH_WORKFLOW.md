# Typingo offline audio workflow

Typingo Kokoro can be used as an offline audio production tool for Typingo. Typingo does not need to call Typingo Kokoro in production.

## 1. Export from Typingo Admin

Use the **导出 TTS 内容** action on the learning-content page. The downloaded file is `typingo-tts-export.json` and contains stable Typingo `contentId`, content type, language, and source text.

By default Typingo exports published English word/sentence/paragraph content that does not already have a ready primary audio asset.

## 2. Generate four voice variants

With Typingo Kokoro running on port 9000:

```powershell
.\scripts\batch-generate.ps1 -InputFile "D:\Downloads\typingo-tts-export.json"
```

Each content item gets four default variants:

- `af_heart` / `en-US` / American female
- `am_michael` / `en-US` / American male
- `bf_emma` / `en-GB` / British female
- `bm_george` / `en-GB` / British male

Output:

```text
output/
└─ batch-YYYYMMDD-HHMMSS/
   ├─ audio/
   │  └─ kokoro/
   │     └─ <contentId>/
   │        ├─ af_heart.mp3
   │        ├─ am_michael.mp3
   │        ├─ bf_emma.mp3
   │        └─ bm_george.mp3
   └─ audio-manifest.json
```

## 3. Upload audio files

Copy the contents of the generated `audio/` directory into the root of Typingo storage. If production uses `STORAGE_LOCAL_ROOT=/data/storage`, then:

```text
audio/kokoro/<contentId>/af_heart.mp3
```

must end up at:

```text
/data/storage/audio/kokoro/<contentId>/af_heart.mp3
```

The physical path must match the manifest `objectKey`.

## 4. Import the manifest

In Typingo Admin choose **导入音频清单** and upload `audio-manifest.json`.

Typingo registers each file as a `media_asset` and links it back to the original learning content through `content_media_asset`. SHA-256 and object-key identities allow repeated imports to reuse assets rather than blindly creating duplicates.

## Design boundary

Typingo remains the source of truth for content IDs and text. Typingo Kokoro remains an offline speech-production service. Binary audio stays outside Git and outside PostgreSQL; the JSON manifest is the contract connecting generated files back to Typingo.
