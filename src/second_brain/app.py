"""second_brain CLI entry point."""

from __future__ import annotations

import os
import sys

import typer
from loguru import logger

from second_brain.notes import resolve_storage_dir, save_thought

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


def main() -> None:
    """CLI entry point."""
    app()
