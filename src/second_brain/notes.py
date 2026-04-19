"""Note-storage helpers for the second_brain CLI."""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_STORAGE_DIRNAME = "second_brain"
EMPTY_FIRST_LINE = "(empty)"
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")


@dataclass(frozen=True)
class NoteEntry:
    """A discovered note, ready for display."""

    path: Path
    title: str
    first_line: str
    mtime: float


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

    The slug is derived from the first non-empty line of *text* only, so
    long note bodies cannot blow past filesystem name limits. When that
    line slugifies to an empty string (e.g. an emoji-only title), falls
    back to a timestamp-only ``YYYY-MM-DD-HHMMSS.md`` filename.
    """
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    slug = slugify(first_line)
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


def _title_from_stem(stem: str) -> str:
    match = _DATE_PREFIX_RE.match(stem)
    return match.group(1) if match else stem


def _first_non_empty_line(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return EMPTY_FIRST_LINE
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return EMPTY_FIRST_LINE


def iter_notes(storage_dir: Path) -> list[NoteEntry]:
    """Return all ``*.md`` notes under *storage_dir*, newest first.

    Recurses into subdirectories. Returns an empty list when *storage_dir*
    does not exist.
    """
    storage_dir = Path(storage_dir).expanduser()
    if not storage_dir.is_dir():
        return []
    entries: list[NoteEntry] = []
    for path in storage_dir.rglob("*.md"):
        if not path.is_file():
            continue
        entries.append(
            NoteEntry(
                path=path,
                title=_title_from_stem(path.stem),
                first_line=_first_non_empty_line(path),
                mtime=path.stat().st_mtime,
            )
        )
    entries.sort(key=lambda e: e.mtime, reverse=True)
    return entries


def delete_note(entry: NoteEntry) -> None:
    """Delete the file backing *entry*.

    Raises ``FileNotFoundError`` if the file no longer exists on disk.
    """
    entry.path.unlink()


def update_note(entry: NoteEntry, body: str) -> NoteEntry:
    """Overwrite *entry*'s file with *body* and return a refreshed entry.

    Preserves the path (title is derived from the filename stem, so it is
    unchanged). Raises ``ValueError`` if *body* is empty or whitespace-only,
    and ``FileNotFoundError`` if the file is missing.
    """
    if not body or not body.strip():
        raise ValueError("note body must not be empty")
    if not entry.path.exists():
        raise FileNotFoundError(entry.path)
    entry.path.write_text(body, encoding="utf-8")
    return NoteEntry(
        path=entry.path,
        title=_title_from_stem(entry.path.stem),
        first_line=_first_non_empty_line(entry.path),
        mtime=entry.path.stat().st_mtime,
    )


def filter_notes(entries: list[NoteEntry], query: str) -> list[NoteEntry]:
    """Return the subset of *entries* matching *query* (case-insensitive).

    Matches against title, first line, and file body. An empty or
    whitespace-only *query* returns *entries* unchanged.
    """
    needle = query.strip().lower()
    if not needle:
        return entries
    matches: list[NoteEntry] = []
    for entry in entries:
        if needle in entry.title.lower() or needle in entry.first_line.lower():
            matches.append(entry)
            continue
        try:
            body = entry.path.read_text(encoding="utf-8")
        except OSError:
            continue
        if needle in body.lower():
            matches.append(entry)
    return matches


def list_subdirs(root: Path) -> list[Path]:
    """Return sorted immediate subdirectories of *root*.

    Returns an empty list when *root* does not exist.
    """
    root = Path(root).expanduser()
    if not root.is_dir():
        return []
    return sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)
