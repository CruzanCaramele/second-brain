"""Note-storage helpers for the second_brain CLI."""

from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

DEFAULT_STORAGE_DIRNAME = "second_brain"


def slugify(text: str) -> str:
    """Return a filesystem-safe slug for *text*.

    Lowercases, strips accents, replaces non-alphanumeric runs with ``-``,
    and trims leading/trailing dashes.
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")


def resolve_storage_dir() -> Path:
    """Resolve the notes storage directory.

    Reads ``SB_DIR`` from the environment, expanding ``~``. Falls back to
    ``~/second_brain`` when the env var is unset or empty.
    """
    raw = os.environ.get("SB_DIR", "").strip()
    if not raw:
        return Path.home() / DEFAULT_STORAGE_DIRNAME
    return Path(raw).expanduser()


def build_filename(text: str, now: datetime) -> str:
    """Build a ``YYYY-MM-DD-<slug>.md`` filename for *text* at *now*.

    When *text* slugifies to an empty string (e.g. an emoji-only thought),
    falls back to a timestamp-only ``YYYY-MM-DD-HHMMSS.md`` filename.
    """
    slug = slugify(text)
    if not slug:
        return f"{now.strftime('%Y-%m-%d-%H%M%S')}.md"
    return f"{now.strftime('%Y-%m-%d')}-{slug}.md"


def save_thought(
    text: str,
    storage_dir: Path,
    now: datetime | None = None,
) -> Path:
    """Save *text* as a markdown file under *storage_dir* and return the path.

    Creates the directory if missing. On filename collisions appends
    ``-2``, ``-3``, … before the ``.md`` suffix. Raises ``ValueError`` if
    *text* is empty or whitespace-only.
    """
    if not text or not text.strip():
        raise ValueError("thought must not be empty")

    now = now or datetime.now()
    storage_dir = Path(storage_dir).expanduser()
    storage_dir.mkdir(parents=True, exist_ok=True)

    base = build_filename(text, now)
    stem = base[:-3]
    candidate = storage_dir / base
    counter = 2
    while candidate.exists():
        candidate = storage_dir / f"{stem}-{counter}.md"
        counter += 1

    candidate.write_text(text, encoding="utf-8")
    return candidate.resolve()
