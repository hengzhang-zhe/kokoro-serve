"""Shared application runtime defaults."""

import os
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("HF_HOME", str(_PROJECT_ROOT / "data" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
