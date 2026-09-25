import json
import os
from pathlib import Path
from typing import Any

from app.config import get_chroma_persist_dir


def _manifest_path() -> Path:
    return get_chroma_persist_dir() / "manifest.json"


def load_manifest() -> list[dict[str, Any]]:
    path = _manifest_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def save_manifest(entries: list[dict[str, Any]]) -> None:
    path = _manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def add_entry(entry: dict[str, Any]) -> dict[str, Any]:
    entries = load_manifest()
    entries.append(entry)
    save_manifest(entries)
    return entry


def remove_entry(document_id: str) -> dict[str, Any] | None:
    entries = load_manifest()
    removed = next((entry for entry in entries if entry.get("id") == document_id), None)
    if removed is not None:
        save_manifest([entry for entry in entries if entry.get("id") != document_id])
    return removed


def get_entry(document_id: str) -> dict[str, Any] | None:
    return next((entry for entry in load_manifest() if entry.get("id") == document_id), None)
