"""second_brain CLI entry point."""

from __future__ import annotations

import os
import sys
from datetime import datetime

import typer
from loguru import logger

from second_brain.notes import iter_notes, resolve_storage_dir, save_thought

app = typer.Typer(help="second_brain — capture quick thoughts as markdown.")


def configure_logging() -> None:
    """Configure loguru for console and file logging.

    Removes the default handler and sets up:
    - stderr handler at LOG_LEVEL (default: INFO, configurable via env var)
    - File handler at DEBUG level writing to LOG_FILE (default: app.log)
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE", "app.log")
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> |"
        " <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> |"
        " <level>{message}</level>"
    )
    logger.remove()
    logger.add(sys.stderr, level=log_level, format=log_format)
    logger.add(
        log_file, level="DEBUG", rotation="50 KB", retention=1, format=log_format
    )


@app.callback()
def _root() -> None:
    """Root callback — runs before every subcommand."""
    configure_logging()


@app.command("new")
def new(
    thought: str = typer.Argument(..., help="The thought to save."),
) -> None:
    """Save a quick thought as a markdown file under ``$SB_DIR``."""
    try:
        path = save_thought(thought, resolve_storage_dir())
    except ValueError as exc:
        logger.error(str(exc))
        raise typer.Exit(code=1) from exc
    logger.info(f"Saved: {path}")
    typer.echo(f"Saved: {path}")


@app.command("list")
def list_notes(
    limit: int | None = typer.Option(
        None,
        "--limit",
        min=1,
        help="Maximum number of notes to show.",
    ),
) -> None:
    """List notes under ``$SB_DIR``, newest first."""
    storage_dir = resolve_storage_dir()
    typer.echo(str(storage_dir))
    entries = iter_notes(storage_dir)
    if not entries:
        typer.echo("This is empty")
        return
    if limit is not None:
        entries = entries[:limit]
    for index, entry in enumerate(entries, start=1):
        date = datetime.fromtimestamp(entry.mtime).strftime("%Y-%m-%d %H:%M")
        typer.echo(f"{index:>2}. {entry.title} — {entry.first_line} — {date}")
    logger.debug(f"Listed {len(entries)} note(s) from {storage_dir}")


@app.command("show")
def show(
    index: int = typer.Argument(
        ..., min=1, help="1-based index from `list` output."
    ),
) -> None:
    """Print a note's contents by its ``list`` index."""
    storage_dir = resolve_storage_dir()
    entries = iter_notes(storage_dir)
    if not entries:
        typer.echo(f"No notes found in {storage_dir}", err=True)
        raise typer.Exit(code=1)
    if index > len(entries):
        typer.echo(
            f"Index {index} out of range (have {len(entries)} notes)", err=True
        )
        raise typer.Exit(code=1)
    entry = entries[index - 1]
    date = datetime.fromtimestamp(entry.mtime).strftime("%Y-%m-%d %H:%M")
    typer.echo(f"# {entry.title}")
    typer.echo(f"# {date}")
    typer.echo(f"# {entry.path}")
    typer.echo("")
    typer.echo(entry.path.read_text(encoding="utf-8"))
    logger.debug(f"Showed note {index}: {entry.path}")


def main() -> None:
    """CLI entry point."""
    app()
