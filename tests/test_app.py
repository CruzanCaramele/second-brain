from pathlib import Path

from typer.testing import CliRunner

from second_brain.app import app

runner = CliRunner()


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


def test_default_storage_dir_used_when_sb_dir_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("SB_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["new", "default dir"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "second_brain").is_dir()
    assert len(list((tmp_path / "second_brain").glob("*.md"))) == 1
