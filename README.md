# second-brain

A tiny CLI for capturing quick thoughts as plain markdown files.

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

Show available commands:

```bash
uv run second_brain --help
```

### Capturing thoughts

Three input methods are supported:

```bash
# Positional argument (quick one-liners)
uv run second_brain new "My brilliant idea about caching"

# From a file
uv run second_brain new --file draft.md

# Interactively in $EDITOR
uv run second_brain new --editor
```

The note is written under `$SB_DIR` (default `~/second_brain/`). The directory
is created if it doesn't exist. The filename is derived from the **first
non-empty line** of the body, so multi-line notes still get short filenames.
On collision a `-2`, `-3`, … suffix is appended. Emoji-only first lines fall
back to a timestamp filename (`YYYY-MM-DD-HHMMSS.md`). Exactly one input
source must be supplied; mixing two exits with code 1.

With dev environment loaded:

```bash
uv run --env-file .env second_brain new "another idea"
```

Via Python module:

```bash
uv run python -m second_brain new "yet another idea"
```

### Listing notes

Show the storage directory and a numbered list of notes, newest first:

```bash
uv run second_brain list
# /Users/you/second_brain
#  1. buy-milk — Remember oat milk — 2026-04-11 18:22
#  2. idea-for-blog — Post about typer callbacks — 2026-04-10 09:14
```

Recurses into subdirectories and ignores non-`.md` files. If the directory is
missing or empty, prints `This is empty`. Cap the number of rows with `--limit`:

```bash
uv run second_brain list --limit 5
```

### Reading a note

Print a note's body to the terminal by its `list` index (1-based, newest first):

```bash
uv run second_brain show 1
# # my-brilliant-idea-about-caching
# # 2026-04-12 15:25
# # /Users/you/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
#
# My brilliant idea about caching
```

The index always maps to the full newest-first list (independent of any
`--limit` used with `list`). Empty store or out-of-range index exit non-zero
with a stderr message.

### Interactive TUI

A full-screen terminal UI powered by [Textual](https://textual.textualize.io/)
is available as an optional extra. Install it, then launch:

```bash
uv sync --extra tui
uv run second_brain tui
```

Features:

- Live search / filter (press `/`)
- Markdown preview pane
- Create, edit (opens `$EDITOR`), and delete notes with a confirmation prompt

| Key      | Action                    |
|----------|---------------------------|
| `j`, `k` | Move selection down / up  |
| `/`      | Focus search              |
| `esc`    | Leave search / close modal |
| `enter`  | Preview selected note     |
| `n`      | New note                  |
| `e`      | Edit in `$EDITOR`         |
| `d`      | Delete (with confirm)     |
| `r`      | Refresh                   |
| `q`      | Quit                      |

Without the extra installed, `second_brain tui` exits with a hint pointing
back to `uv sync --extra tui`.

## Log Output

```
2026-04-12 15:25:56 | INFO | second_brain.app:new:53 | Saved: /Users/you/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
```

## Environment Variables

`.env.example` is the committed template — copy it to `.env` for development:

```bash
cp .env.example .env
```

| Variable    | Default           | Description                                    |
|-------------|-------------------|------------------------------------------------|
| `SB_DIR`    | `~/second_brain`  | Directory where `new` writes markdown files.   |
| `LOG_LEVEL` | `INFO`            | Console log level (`DEBUG`, `INFO`, `WARNING`, …). Set to `DEBUG` in `.env` for verbose console output. |
| `LOG_FILE`  | `app.log`         | Path to the log file.                          |

> **Note:** `uv run` does not auto-load `.env`. Use `uv run --env-file .env` to load dev settings explicitly.

## Testing

Run the test suite:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov
```

## Documentation

Preview docs locally:

```bash
uv run python scripts/serve_docs.py
```

Build static docs:

```bash
uv run mkdocs build
```
