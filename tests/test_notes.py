import os
from datetime import datetime
from pathlib import Path

import pytest

from second_brain.notes import (
    build_filename,
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
