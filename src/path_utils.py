from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
WINDOWS_DIR = DATA_DIR / "windows"
VALIDATION_DIR = DATA_DIR / "validation"
REPORTS_DIR = REPO_ROOT / "reports"


def resolve_path(value: str | Path | None, *, default_base: Path | None = None) -> Path:
    if value is None:
        raise ValueError("Path value is required")
    path = Path(value)
    if path.is_absolute():
        return path
    base = default_base or REPO_ROOT
    candidate = base / path
    if candidate.exists():
        return candidate
    if (REPO_ROOT / path).exists():
        return REPO_ROOT / path
    return candidate
