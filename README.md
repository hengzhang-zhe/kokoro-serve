# Kokoro Serve

A self-hosted HTTP service built directly on the official Kokoro inference library and model.

## Upstream

- Inference library: `hexgrad/kokoro`
- Model repository: `hexgrad/Kokoro-82M`

Kokoro Serve does not embed or fork third-party FastAPI/WebUI wrappers. It provides its own API, Docker packaging, runtime configuration, tests, and audio encoding around the official Kokoro interfaces.

## Features

- OpenAI-style `POST /v1/audio/speech`
- American English and British English voice routing
- MP3 / WAV / FLAC / Opus output
- One shared `KModel` reused by multiple `KPipeline` instances
- CPU-first Docker deployment
- Persistent Hugging Face cache
- Health, model and voice discovery endpoints
- Windows-friendly local deployment
- Unified default port: `9000`

## Quick start

Recommended Windows location:

```text
D:\Zhe\Code\kokoro-serve
```

```powershell
git clone https://github.com/hengzhang-zhe/kokoro-serve.git
cd kokoro-serve
Copy-Item .env.example .env
docker compose build
docker compose up -d
docker compose logs -f
```

OpenAPI:

```text
http://localhost:9000/docs
```

Health:

```text
http://localhost:9000/health
```

## Local Python development

Open this project in PyCharm with a dedicated Python environment and install `requirements.txt`. Run the `uvicorn` module with `app.main:app --host 127.0.0.1 --port 9000 --reload --reload-dir app` from the project directory. The app sets `HF_HOME` to `./data/huggingface` by default, so model downloads stay inside the project without a machine-specific PyCharm setting.

Docker Compose mounts the same `./data/huggingface` directory into the container. Both runtimes use regular cache files rather than symlinks so Windows and Linux can read the same downloads. Restart the local process after changing the cache configuration. Only one runtime can bind host port `9000` at a time; change one port when running both services.

## Generate speech

```http
POST /v1/audio/speech
Content-Type: application/json

{
  "model": "kokoro",
  "input": "Learning English can be easy and enjoyable.",
  "voice": "af_heart",
  "response_format": "mp3",
  "speed": 1.0
}
```

Voice prefixes enabled by this service:

| Prefix | Locale | Description |
|---|---|---|
| `af_*` | `en-US` | American English female |
| `am_*` | `en-US` | American English male |
| `bf_*` | `en-GB` | British English female |
| `bm_*` | `en-GB` | British English male |

## Architecture

```text
HTTP API :9000
   ↓
KokoroServeEngine
   ↓
shared KModel
   ├─ KPipeline(lang_code="a")  American English
   └─ KPipeline(lang_code="b")  British English
   ↓
hexgrad/Kokoro-82M
```

Kokoro's official `KModel` documentation states that one model instance can be reused across multiple pipelines to avoid redundant memory allocation, which is the design used here.

See `docs/ARCHITECTURE.md` and `THIRD_PARTY_NOTICES.md`.


## Batch Audio Studio

Open:

```text
http://localhost:9000/
```

The web UI accepts `typingo-tts-export.json` exported from Typingo Admin Audio Management.

Workflow:

```text
Typingo Audio Management
  -> select learning items
  -> select Kokoro voices
  -> export typingo-tts-export.json
  -> upload to Kokoro Batch Audio Studio
  -> generate
  -> download ZIP
```

The ZIP contains:

```text
audio/
  kokoro/
    <contentId>/
      <voice>.mp3
audio-manifest.json
generation-report.json
```

`audio-manifest.json` retains the Typingo `contentId`, locale and Kokoro voice for every generated file, so Typingo can associate imported audio with the original learning item.

The web batch processor generates only the explicit `variants` contained in the uploaded task. It does not add default voices.
