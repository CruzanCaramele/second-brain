import os
from datetime import datetime
from pathlib import Path

import pytest

from second_brain.notes import (
    NoteEntry,
    build_filename,
    iter_notes,
    resolve_storage_dir,
    save_thought,
    slugify,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("My brilliant idea about caching", "my-brilliant-idea-about-caching"),
        ("Hello, World!", "hello-world"),
        ("  spaced  out  ", "spaced-out"),
        ("UPPER_case-mix", "upper-case-mix"),
        ("---weird---", "weird"),
        ("café ☕ notes", "cafe-notes"),
    ],
)
def test_slugify(text, expected):
    assert slugify(text) == expected


def test_resolve_storage_dir_default(monkeypatch):
    monkeypatch.delenv("SB_DIR", raising=False)
    assert resolve_storage_dir() == Path.home() / "second_brain"


def test_resolve_storage_dir_custom(monkeypatch, tmp_path):
    monkeypatch.setenv("SB_DIR", str(tmp_path / "custom"))
    assert resolve_storage_dir() == tmp_path / "custom"


def test_resolve_storage_dir_expands_user(monkeypatch):
    monkeypatch.setenv("SB_DIR", "~/my-notes")
    assert resolve_storage_dir() == Path.home() / "my-notes"


def test_build_filename_format():
    now = datetime(2026, 4, 12, 10, 30, 0)
    assert build_filename("My brilliant idea about caching", now) == (
        "2026-04-12-my-brilliant-idea-about-caching.md"
    )


def test_save_thought_creates_directory_and_file(tmp_path):
    storage = tmp_path / "notes"
    assert not storage.exists()
    now = datetime(2026, 4, 12, 9, 0, 0)
    path = save_thought("Hello idea", storage, now=now)
    assert path.exists()
    assert path.parent == storage
    assert path.name == "2026-04-12-hello-idea.md"
    assert path.read_text(encoding="utf-8") == "Hello idea"


def test_build_filename_uses_first_line_of_multiline(tmp_path):
    now = datetime(2026, 4, 12, 10, 30, 0)
    text = "My short title\n\nA long body " + "word " * 200
    assert build_filename(text, now) == "2026-04-12-my-short-title.md"


def test_build_filename_skips_blank_leading_lines():
    now = datetime(2026, 4, 12, 10, 30, 0)
    text = "\n   \n\nReal first line\nmore"
    assert build_filename(text, now) == "2026-04-12-real-first-line.md"


def test_build_filename_emoji_first_line_falls_back_to_timestamp():
    now = datetime(2026, 4, 12, 15, 30, 45)
    text = "☕\nBody goes here"
    assert build_filename(text, now) == "2026-04-12-153045.md"


def test_save_thought_long_body_succeeds(tmp_path):
    now = datetime(2026, 4, 12, 9, 0, 0)
    text = "Short title\n\n" + ("word " * 500)
    path = save_thought(text, tmp_path, now=now)
    assert path.name == "2026-04-12-short-title.md"
    assert path.read_text(encoding="utf-8") == text


def test_save_thought_collision_appends_suffix(tmp_path):
    now = datetime(2026, 4, 12, 9, 0, 0)
    p1 = save_thought("same idea", tmp_path, now=now)
    p2 = save_thought("same idea", tmp_path, now=now)
    p3 = save_thought("same idea", tmp_path, now=now)
    assert p1.name == "2026-04-12-same-idea.md"
    assert p2.name == "2026-04-12-same-idea-2.md"
    assert p3.name == "2026-04-12-same-idea-3.md"


def test_save_thought_rejects_empty(tmp_path):
    with pytest.raises(ValueError):
        save_thought("   ", tmp_path, now=datetime(2026, 4, 12))
    assert list(tmp_path.iterdir()) == []


def test_save_thought_returns_absolute_path(tmp_path):
    path = save_thought("idea", tmp_path, now=datetime(2026, 4, 12))
    assert os.path.isabs(path)


@pytest.mark.parametrize("text", ["☕", "!!!", "☕☕☕", "---"])
def test_build_filename_empty_slug_falls_back_to_timestamp(text):
    now = datetime(2026, 4, 12, 15, 30, 45)
    assert build_filename(text, now) == "2026-04-12-153045.md"


def test_save_thought_empty_slug_uses_timestamp(tmp_path):
    now = datetime(2026, 4, 12, 15, 30, 45)
    path = save_thought("☕", tmp_path, now=now)
    assert path.name == "2026-04-12-153045.md"
    assert path.read_text(encoding="utf-8") == "☕"


def test_save_thought_empty_slug_collision_appends_suffix(tmp_path):
    now = datetime(2026, 4, 12, 15, 30, 45)
    p1 = save_thought("☕", tmp_path, now=now)
    p2 = save_thought("!!!", tmp_path, now=now)
    assert p1.name == "2026-04-12-153045.md"
    assert p2.name == "2026-04-12-153045-2.md"


def _touch(path: Path, content: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_iter_notes_missing_dir_returns_empty(tmp_path):
    assert iter_notes(tmp_path / "nope") == []


def test_iter_notes_empty_dir_returns_empty(tmp_path):
    assert iter_notes(tmp_path) == []


def test_iter_notes_sorts_newest_first(tmp_path):
    _touch(tmp_path / "old.md", "older", 1_000_000.0)
    _touch(tmp_path / "new.md", "newer", 2_000_000.0)
    _touch(tmp_path / "mid.md", "middle", 1_500_000.0)
    entries = iter_notes(tmp_path)
    assert [e.path.name for e in entries] == ["new.md", "mid.md", "old.md"]


def test_iter_notes_recurses_subdirectories(tmp_path):
    _touch(tmp_path / "a.md", "root", 1_000.0)
    _touch(tmp_path / "sub" / "b.md", "child", 2_000.0)
    _touch(tmp_path / "sub" / "deep" / "c.md", "grand", 3_000.0)
    names = {e.path.name for e in iter_notes(tmp_path)}
    assert names == {"a.md", "b.md", "c.md"}


def test_iter_notes_ignores_non_markdown(tmp_path):
    _touch(tmp_path / "a.md", "keep", 1_000.0)
    _touch(tmp_path / "b.txt", "drop", 2_000.0)
    _touch(tmp_path / "c.markdown", "drop", 3_000.0)
    names = [e.path.name for e in iter_notes(tmp_path)]
    assert names == ["a.md"]


def test_iter_notes_entry_fields(tmp_path):
    _touch(
        tmp_path / "2026-04-12-buy-milk.md",
        "\n\n  Remember oat milk  \nsecond line\n",
        1_700_000_000.0,
    )
    entries = iter_notes(tmp_path)
    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, NoteEntry)
    assert e.path.name == "2026-04-12-buy-milk.md"
    assert e.title == "buy-milk"
    assert e.first_line == "Remember oat milk"
    assert e.mtime == 1_700_000_000.0


def test_iter_notes_title_falls_back_to_stem_when_no_date_prefix(tmp_path):
    _touch(tmp_path / "random-name.md", "hi", 1_000.0)
    entries = iter_notes(tmp_path)
    assert entries[0].title == "random-name"


def test_iter_notes_empty_file_first_line_is_sentinel(tmp_path):
    _touch(tmp_path / "a.md", "", 1_000.0)
    _touch(tmp_path / "b.md", "\n\n   \n", 2_000.0)
    first_lines = {e.path.name: e.first_line for e in iter_notes(tmp_path)}
    assert first_lines == {"a.md": "(empty)", "b.md": "(empty)"}
