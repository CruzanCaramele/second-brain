# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

Show available commands:

```bash
uv run second_brain --help
```

Or as a Python module:

```bash
uv run python -m second_brain --help
```

## Capturing thoughts

Three input methods are available:

| Invocation | Filename seed | Body |
|---|---|---|
| `second_brain new "idea"` | `idea` | `idea` |
| `second_brain new --file note.md` | first line of `note.md` | contents of `note.md` |
| `second_brain new --editor` | first line of editor buffer | editor buffer |

**Positional argument** (quick one-liners):

```bash
uv run second_brain new "My brilliant idea about caching"
# Saved: ~/second_brain/2026-04-13-my-brilliant-idea-about-caching.md
```

**From a file** (`--file PATH`):

```bash
uv run second_brain new --file draft.md
# Saved: ~/second_brain/2026-04-13-<first-line-slug>.md
```

**From `$EDITOR`** (`--editor`):

```bash
uv run second_brain new --editor
# Opens $EDITOR; saves on quit. Aborts if the buffer is empty.
```

Rules:

- Exactly one input source must be supplied; mixing two or more exits with code 1.
- The storage directory is created automatically if missing.
- Filenames follow `YYYY-MM-DD-<slug>.md`, where the slug is derived from
  the **first non-empty line** of the body (so long bodies don't overflow
  filesystem name limits). On collision, a `-2`, `-3`, … suffix is appended.
- If the first line has no slug-able characters (e.g. emoji-only), the
  filename falls back to `YYYY-MM-DD-HHMMSS.md`.
- The file contents are the body text verbatim (plain markdown, no frontmatter).

## Listing notes

Show where notes live and a numbered list of existing notes, newest first:

```bash
uv run second_brain list
# /Users/you/second_brain
#  1. buy-milk — Remember oat milk — 2026-04-11 18:22
#  2. idea-for-blog — Post about typer callbacks — 2026-04-10 09:14
```

- The first line is the absolute path of the notes directory (resolved from `$SB_DIR`).
- Entries are sorted by file modification time, newest first.
- Recurses into subdirectories; non-`.md` files are ignored.
- If the directory is missing or contains no notes, prints `This is empty`.
- Empty `.md` files render a `(empty)` sentinel in place of the first line.

Cap the output with `--limit`:

```bash
uv run second_brain list --limit 5
```

`--limit` must be a positive integer; `0` or negative values are rejected with a usage error.

## Reading a note

Print a note's contents to the terminal by its `list` index (1-based, newest first):

```bash
uv run second_brain show 1
# # my-brilliant-idea-about-caching
# # 2026-04-12 15:25
# # /Users/you/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
#
# My brilliant idea about caching
```

- The index matches the number in `second_brain list` (always against the full
  newest-first list — it is **not** affected by any prior `--limit`).
- Output is a three-line `# `-prefixed header (title, timestamp, path), a blank
  line, then the raw markdown body. Pipe into `glow`, `bat`, etc. as needed.
- Errors are written to stderr with exit code `1`:
  - `No notes found in <dir>` when the store is empty.
  - `Index N out of range (have M notes)` when `N` is too large.
- `show 0` (or any `N < 1`) is rejected with a Typer usage error.

## Log Output

```
2026-04-12 15:25:56 | INFO | second_brain.app:new:53 | Saved: /Users/you/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
```

## Environment Variables

| Variable    | Default           | Description                               |
|-------------|-------------------|-------------------------------------------|
| `SB_DIR`    | `~/second_brain`  | Directory where `new` writes markdown.    |
| `LOG_LEVEL` | `INFO`            | Console log level (DEBUG, INFO, …)        |
| `LOG_FILE`  | `app.log`         | Path to the log file                      |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.
