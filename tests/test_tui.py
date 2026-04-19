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


async def test_tui_edit_splits_multiword_editor(tmp_path, monkeypatch):
    """`EDITOR='code --wait'` must be shlex-split so subprocess doesn't
    treat it as a single executable name."""
    _touch(tmp_path / "2026-04-12-x.md", "body", 1_000.0)

    captured: list[list[str]] = []

    class _FakeCompleted:
        returncode = 0

    def fake_run(argv, check=False, **kwargs):
        captured.append(list(argv))
        return _FakeCompleted()

    monkeypatch.setenv("EDITOR", "fake-editor --wait --flag")
    monkeypatch.setattr("second_brain.tui.app.subprocess.run", fake_run)

    app = SecondBrainApp(storage_dir=tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Bypass App.suspend() which requires a real terminal.
        from contextlib import nullcontext

        monkeypatch.setattr(app, "suspend", lambda: nullcontext())
        app.action_edit_selected()
        await pilot.pause()

    assert len(captured) == 1
    assert captured[0][:3] == ["fake-editor", "--wait", "--flag"]
    assert captured[0][-1].endswith("2026-04-12-x.md")


async def test_tui_delete_race_notifies(tmp_path):
    """Deleting a note whose file vanished mid-flight should notify,
    not silently swallow the error."""
    _touch(tmp_path / "2026-04-12-x.md", "body", 1_000.0)

    app = SecondBrainApp(storage_dir=tmp_path)
    notifications: list[tuple[str, str | None]] = []

    async with app.run_test() as pilot:
        await pilot.pause()
        # Simulate external deletion.
        (tmp_path / "2026-04-12-x.md").unlink()
        # Patch notify to capture calls.
        app.notify = lambda msg, severity=None, **kw: notifications.append(
            (msg, severity)
        )
        # Directly invoke the confirm callback path.
        entry = app._visible[0]
        from second_brain.notes import delete_note

        try:
            delete_note(entry)
        except FileNotFoundError:
            pass
        # Now simulate the user confirming again — should notify.
        app.action_delete_selected()
        # Confirm via the 'y' binding on the modal.
        await pilot.press("y")
        await pilot.pause()

    assert any("already gone" in msg for msg, _sev in notifications)
