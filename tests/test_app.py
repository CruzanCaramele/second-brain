import os
import re
from pathlib import Path

from typer.testing import CliRunner

from second_brain.app import app

runner = CliRunner()


def _touch(path: Path, content: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_new_creates_markdown_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["new", "My brilliant idea about caching"])
    assert result.exit_code == 0, result.output
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "My brilliant idea about caching"
    assert files[0].name.endswith("-my-brilliant-idea-about-caching.md")


def test_new_echoes_saved_path(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["new", "log me"])
    assert "log-me.md" in result.output


def test_new_logs_saved_path_to_log_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path / "notes"))
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    result = runner.invoke(app, ["new", "logged via loguru"])
    assert result.exit_code == 0, result.output
    assert "logged-via-loguru.md" in log_file.read_text(encoding="utf-8")


def test_new_creates_storage_dir_if_missing(tmp_path, monkeypatch):
    target = tmp_path / "does-not-exist-yet"
    monkeypatch.setenv("SB_DIR", str(target))
    result = runner.invoke(app, ["new", "bootstrap"])
    assert result.exit_code == 0, result.output
    assert target.is_dir()
    assert len(list(target.glob("*.md"))) == 1


def test_new_rejects_empty_thought(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["new", "   "])
    assert result.exit_code != 0
    assert list(tmp_path.glob("*.md")) == []


def test_help_shows_new_subcommand():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "new" in result.output


def test_help_shows_list_subcommand():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "list" in result.output


def test_list_empty_dir_prints_path_and_sentinel(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert str(tmp_path) in result.output
    assert "This is empty" in result.output


def test_list_missing_dir_prints_path_and_sentinel(tmp_path, monkeypatch):
    target = tmp_path / "does-not-exist"
    monkeypatch.setenv("SB_DIR", str(target))
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert str(target) in result.output
    assert "This is empty" in result.output


def test_list_shows_notes_newest_first(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "2026-04-10-old.md", "older thought", 1_000_000.0)
    _touch(tmp_path / "2026-04-11-new.md", "newer thought", 2_000_000.0)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == str(tmp_path)
    assert "1." in lines[1] and "new" in lines[1] and "newer thought" in lines[1]
    assert "2." in lines[2] and "old" in lines[2] and "older thought" in lines[2]


def test_list_recurses_and_ignores_non_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "a.md", "root md", 1_000.0)
    _touch(tmp_path / "sub" / "b.md", "nested md", 2_000.0)
    _touch(tmp_path / "c.txt", "ignored", 3_000.0)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert "a.md" not in result.output or "root md" in result.output
    assert "nested md" in result.output
    assert "ignored" not in result.output


def test_list_empty_file_renders_empty_sentinel(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "blank.md", "", 1_000.0)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert "(empty)" in result.output


def test_list_limit_caps_results(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "a.md", "first", 1_000.0)
    _touch(tmp_path / "b.md", "second", 2_000.0)
    _touch(tmp_path / "c.md", "third", 3_000.0)
    result = runner.invoke(app, ["list", "--limit", "2"])
    assert result.exit_code == 0, result.output
    assert "third" in result.output
    assert "second" in result.output
    assert "first" not in result.output


def test_list_limit_zero_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["list", "--limit", "0"])
    assert result.exit_code != 0


def test_help_shows_show_subcommand():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "show" in result.output


def test_show_prints_header_and_body_of_newest(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "2026-04-10-old.md", "older body", 1_000_000.0)
    newest = tmp_path / "2026-04-11-new.md"
    _touch(newest, "newer body line 1\nnewer body line 2", 2_000_000.0)
    result = runner.invoke(app, ["show", "1"])
    assert result.exit_code == 0, result.output
    assert "# new" in result.output
    assert "# 1970-01-" in result.output or "2026" in result.output  # formatted mtime
    assert f"# {newest.resolve()}" in result.output or f"# {newest}" in result.output
    assert "newer body line 1" in result.output
    assert "newer body line 2" in result.output
    assert "older body" not in result.output


def test_show_second_index_returns_older_note(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "a.md", "older body", 1_000_000.0)
    _touch(tmp_path / "b.md", "newer body", 2_000_000.0)
    result = runner.invoke(app, ["show", "2"])
    assert result.exit_code == 0, result.output
    assert "older body" in result.output
    assert "newer body" not in result.output


def test_show_empty_store_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["show", "1"])
    assert result.exit_code == 1
    assert "No notes found" in result.output


def test_show_out_of_range_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "a.md", "only one", 1_000.0)
    result = runner.invoke(app, ["show", "99"])
    assert result.exit_code == 1
    assert "out of range" in result.output
    assert "have 1" in result.output


def test_show_rejects_zero(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    _touch(tmp_path / "a.md", "x", 1_000.0)
    result = runner.invoke(app, ["show", "0"])
    assert result.exit_code != 0


def test_new_from_file_writes_body_and_slug_from_first_line(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path / "notes"))
    src = tmp_path / "draft.md"
    src.write_text("First line title\n\nBody paragraph.\n", encoding="utf-8")
    result = runner.invoke(app, ["new", "--file", str(src)])
    assert result.exit_code == 0, result.output
    files = list((tmp_path / "notes").glob("*.md"))
    assert len(files) == 1
    assert (
        files[0].read_text(encoding="utf-8") == "First line title\n\nBody paragraph.\n"
    )
    assert files[0].name.endswith("-first-line-title.md")


def test_new_from_file_missing_path_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    missing = tmp_path / "nope.md"
    result = runner.invoke(app, ["new", "--file", str(missing)])
    assert result.exit_code != 0
    assert list(tmp_path.glob("*.md")) == []


def test_new_from_editor_writes_buffer(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    monkeypatch.setattr(
        "second_brain.app.typer.edit",
        lambda *a, **k: "Editor title\n\nMore text.\n",
    )
    result = runner.invoke(app, ["new", "--editor"])
    assert result.exit_code == 0, result.output
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "Editor title\n\nMore text.\n"
    assert files[0].name.endswith("-editor-title.md")


def test_new_editor_aborted_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    monkeypatch.setattr("second_brain.app.typer.edit", lambda *a, **k: None)
    result = runner.invoke(app, ["new", "--editor"])
    assert result.exit_code != 0
    assert list(tmp_path.glob("*.md")) == []


def test_new_editor_empty_buffer_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    monkeypatch.setattr("second_brain.app.typer.edit", lambda *a, **k: "   \n")
    result = runner.invoke(app, ["new", "--editor"])
    assert result.exit_code != 0
    assert list(tmp_path.glob("*.md")) == []


def test_new_rejects_multiple_input_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    src = tmp_path / "draft.md"
    src.write_text("body", encoding="utf-8")
    result = runner.invoke(app, ["new", "hello", "--file", str(src)])
    assert result.exit_code != 0
    result = runner.invoke(app, ["new", "--file", str(src), "--editor"])
    assert result.exit_code != 0
    result = runner.invoke(app, ["new", "hello", "--editor"])
    assert result.exit_code != 0


def test_new_with_no_input_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("SB_DIR", str(tmp_path))
    result = runner.invoke(app, ["new"])
    assert result.exit_code != 0
    assert list(tmp_path.glob("*.md")) == []


def test_new_from_file_emoji_only_first_line_falls_back_to_timestamp(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SB_DIR", str(tmp_path / "notes"))
    src = tmp_path / "emoji.md"
    src.write_text("🎉🎉🎉\n\nbody\n", encoding="utf-8")
    result = runner.invoke(app, ["new", "--file", str(src)])
    assert result.exit_code == 0, result.output
    files = list((tmp_path / "notes").glob("*.md"))
    assert len(files) == 1
    # timestamp fallback: YYYY-MM-DD-HHMMSS.md (no slug part)
    assert re.match(r"^\d{4}-\d{2}-\d{2}-\d{6}\.md$", files[0].name)


def test_default_storage_dir_used_when_sb_dir_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("SB_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["new", "default dir"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "second_brain").is_dir()
    assert len(list((tmp_path / "second_brain").glob("*.md"))) == 1


# ----------------------------- tui subcommand ------------------------------


def test_tui_invokes_run(monkeypatch):
    import second_brain.tui as tui_pkg

    calls: list[int] = []
    monkeypatch.setattr(tui_pkg, "run", lambda: calls.append(1))
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 0, result.output
    assert calls == [1]


def test_tui_missing_textual_shows_install_hint(monkeypatch):
    import sys

    import second_brain as sb_pkg

    # Remove cached submodule entries so the import runs fresh.
    for name in [n for n in sys.modules if n.startswith("second_brain.tui")]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    # Setting sys.modules entry to None makes `from second_brain import tui`
    # raise ImportError when falling back to sys.modules lookup.
    monkeypatch.setitem(sys.modules, "second_brain.tui", None)
    # Also detach the attribute from the parent package so Python can't find
    # an already-imported submodule via attribute access.
    monkeypatch.delattr(sb_pkg, "tui", raising=False)

    result = runner.invoke(app, ["tui"])
    assert result.exit_code != 0
    assert "uv sync --extra tui" in result.output
