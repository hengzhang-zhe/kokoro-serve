# Architecture

## Scope

Typingo Kokoro is an HTTP service wrapper around the official Kokoro inference library and Kokoro-82M model.

It deliberately does not fork a third-party Kokoro API server.

## Upstream boundary

```text
typingo-kokoro
   ↓ Python dependency
hexgrad/kokoro
   ↓ Hugging Face model download
hexgrad/Kokoro-82M
```

The official `KModel` implementation downloads `config.json` and the model weights from Hugging Face when needed.

## Runtime model

Kokoro's official model implementation documents that one `KModel` instance can be reused across multiple `KPipeline` instances to avoid redundant memory allocation.

Typingo Kokoro therefore uses:

```text
one KModel
├─ KPipeline(lang_code="a") → American English
└─ KPipeline(lang_code="b") → British English
```

Both pipelines share the same model instance.

## Process model

Run one Uvicorn worker per container.

Multiple workers would each load their own model copy. For higher throughput, prefer horizontally scaling containers instead of increasing Uvicorn workers in one container.

## Concurrency

Inference is protected by an application-level semaphore. The default is:

```text
KOKORO_SERVE_MAX_CONCURRENCY=2
```

Tune this after measuring CPU/GPU utilization and latency.

## Storage

Hugging Face runtime assets are persisted under:

```text
./data/huggingface
```

Local Python resolves this path from the project package before importing Kokoro. Docker Compose bind-mounts the same directory at `/data/huggingface`. `HF_HUB_DISABLE_SYMLINKS=1` keeps cache entries as regular files so both Windows and the Linux container can read them. The cache is ignored by Git and is populated on first model or voice use.

Generated test files are stored under:

```text
./output
```

Neither directory should be committed to Git.

## Production integration

Typingo Kokoro should stay stateless from the product perspective.

Authentication, subscriptions, quotas, Redis metadata and permanent audio caching belong upstream in the consuming application or media service.

A recommended permanent cache identity is:

```text
SHA256(
    provider
  | model_revision
  | locale
  | voice
  | speed
  | normalized_text
)
```

For local development the Compose file binds to `127.0.0.1`. In production expose the service only on a private network.
