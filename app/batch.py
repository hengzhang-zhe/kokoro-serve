from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import uuid
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine import get_engine
from app.voices import resolve_voice

SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
OUTPUT_ROOT = Path("output") / "batches"


@dataclass
class BatchJob:
    id: str
    source_path: Path
    root: Path
    status: str = "imported"
    total: int = 0
    completed: int = 0
    failed: int = 0
    item_count: int = 0
    voices: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    zip_path: Path | None = None


_jobs: dict[str, BatchJob] = {}
_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(value: str, field_name: str) -> str:
    if not value or not SAFE_ID.fullmatch(value):
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value


def _read_task(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schemaVersion") != "typingo-tts-export/v1":
        raise ValueError("Unsupported task schemaVersion")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")
    return data


async def import_task(raw: bytes) -> dict[str, Any]:
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError("Task file is too large")

    data = json.loads(raw.decode("utf-8-sig"))
    if data.get("schemaVersion") != "typingo-tts-export/v1":
        raise ValueError("Unsupported task schemaVersion")

    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")

    voice_counter: Counter[str] = Counter()
    total = 0
    normalized_items = []

    for item in items:
        content_id = _safe(str(item.get("contentId", "")), "contentId")
        text = str(item.get("text", "")).strip()
        if not text:
            raise ValueError(f"Blank text for contentId={content_id}")
        variants = item.get("variants") or []
        if not isinstance(variants, list):
            raise ValueError(f"variants must be an array for contentId={content_id}")

        normalized_variants = []
        for variant in variants:
            voice = _safe(str(variant.get("voice", "")), "voice")
            route = resolve_voice(voice)
            locale = str(variant.get("locale") or route.locale)
            normalized_variants.append({
                **variant,
                "voice": voice,
                "locale": locale,
            })
            voice_counter[voice] += 1
            total += 1

        if normalized_variants:
            normalized_items.append({
                **item,
                "contentId": content_id,
                "text": text,
                "variants": normalized_variants,
            })

    job_id = uuid.uuid4().hex
    root = OUTPUT_ROOT / job_id
    root.mkdir(parents=True, exist_ok=False)
    source_path = root / "task.json"
    normalized = {**data, "items": normalized_items}
    source_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

    job = BatchJob(
        id=job_id,
        source_path=source_path,
        root=root,
        total=total,
        item_count=len(normalized_items),
        voices=dict(voice_counter),
    )
    async with _lock:
        _jobs[job_id] = job

    return job_view(job)


def job_view(job: BatchJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "itemCount": job.item_count,
        "audioCount": job.total,
        "completed": job.completed,
        "failed": job.failed,
        "voices": job.voices,
        "error": job.error,
        "downloadReady": job.zip_path is not None and job.zip_path.exists(),
    }


def get_job(job_id: str) -> BatchJob:
    job = _jobs.get(job_id)
    if job is None:
        root = OUTPUT_ROOT / job_id
        source = root / "task.json"
        status_file = root / "status.json"
        if source.exists() and status_file.exists():
            saved = json.loads(status_file.read_text(encoding="utf-8"))
            job = BatchJob(
                id=job_id,
                source_path=source,
                root=root,
                status=saved.get("status", "unknown"),
                total=int(saved.get("audioCount", 0)),
                completed=int(saved.get("completed", 0)),
                failed=int(saved.get("failed", 0)),
                item_count=int(saved.get("itemCount", 0)),
                voices=saved.get("voices", {}),
                error=saved.get("error"),
                zip_path=(root / "typingo-audio-batch.zip") if (root / "typingo-audio-batch.zip").exists() else None,
            )
            _jobs[job_id] = job
    if job is None:
        raise KeyError(job_id)
    return job


def _save_status(job: BatchJob) -> None:
    (job.root / "status.json").write_text(
        json.dumps(job_view(job), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def start_generation(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job.status == "running":
        return job_view(job)
    if job.status not in {"imported", "failed", "completed_with_errors"}:
        raise ValueError(f"Job cannot be started from status={job.status}")

    job.status = "running"
    job.completed = 0
    job.failed = 0
    job.error = None
    job.zip_path = None

    audio_root = job.root / "audio" / "kokoro"
    if audio_root.exists():
        shutil.rmtree(audio_root)
    for stale in ("audio-manifest.json", "generation-report.json", "typingo-audio-batch.zip"):
        p = job.root / stale
        if p.exists():
            p.unlink()

    _save_status(job)
    asyncio.create_task(_run(job))
    return job_view(job)


async def _run(job: BatchJob) -> None:
    assets: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    try:
        task = _read_task(job.source_path)
        engine = get_engine()

        for item in task["items"]:
            content_id = item["contentId"]
            text = item["text"]
            for variant in item.get("variants") or []:
                voice = variant["voice"]
                locale = variant["locale"]
                try:
                    data = await engine.synthesize(
                        text=text,
                        voice=voice,
                        speed=1.0,
                        response_format="mp3",
                    )
                    relative = Path("audio") / "kokoro" / content_id / f"{voice}.mp3"
                    target = job.root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)

                    digest = hashlib.sha256(data).hexdigest()
                    assets.append({
                        "contentId": content_id,
                        "role": "primary",
                        "locale": locale,
                        "voice": voice,
                        "provider": "kokoro",
                        "storageProvider": "local",
                        "bucket": None,
                        "objectKey": relative.as_posix(),
                        "sourceUrl": None,
                        "checksumSha256": digest,
                        "mimeType": "audio/mpeg",
                        "sizeBytes": len(data),
                        "durationSeconds": None,
                    })
                    job.completed += 1
                except Exception as exc:
                    job.failed += 1
                    failures.append({
                        "contentId": content_id,
                        "voice": voice,
                        "message": str(exc),
                    })
                finally:
                    _save_status(job)

        manifest = {
            "schemaVersion": "typingo-audio-manifest/v1",
            "generatedAt": _now(),
            "provider": "kokoro",
            "model": "hexgrad/Kokoro-82M",
            "assets": assets,
        }
        (job.root / "audio-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (job.root / "generation-report.json").write_text(
            json.dumps({
                "generatedAt": _now(),
                "requested": job.total,
                "completed": job.completed,
                "failed": job.failed,
                "failures": failures,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        zip_path = job.root / "typingo-audio-batch.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            audio_root = job.root / "audio"
            if audio_root.exists():
                for file in audio_root.rglob("*"):
                    if file.is_file():
                        archive.write(file, file.relative_to(job.root).as_posix())
            archive.write(job.root / "audio-manifest.json", "audio-manifest.json")
            archive.write(job.root / "generation-report.json", "generation-report.json")

        job.zip_path = zip_path
        job.status = "completed_with_errors" if failures else "completed"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
    finally:
        _save_status(job)
