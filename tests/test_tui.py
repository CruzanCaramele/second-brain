"""Smoke tests for the Textual TUI."""

from __future__ import annotations

import os
from pathlib import Path

from second_brain.tui.app import SecondBrainApp


def _touch(path: Path, content: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))


async def test_tui_lists_notes_on_startup(tmp_path):
    _touch(tmp_path / "2026-04-12-alpha.md", "alpha body", 1_000.0)
    _touch(tmp_path / "2026-04-13-beta.md", "beta body", 2_000.0)

    app = SecondBrainApp(storage_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert len(app._visible) == 2
        # Newest first
        assert app._visible[0].path.name == "2026-04-13-beta.md"


async def test_tui_search_filters_notes(tmp_path):
    _touch(tmp_path / "2026-04-12-alpha.md", "alpha body", 1_000.0)
    _touch(tmp_path / "2026-04-13-beta.md", "beta body", 2_000.0)

    app = SecondBrainApp(storage_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        search = app.query_one("#search")
        search.value = "alpha"
        await pilot.pause()
        assert [e.path.name for e in app._visible] == ["2026-04-12-alpha.md"]


async def test_tui_quit_binding(tmp_path):
    app = SecondBrainApp(storage_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
    assert app._visible == []
