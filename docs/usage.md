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

Save a quick thought as a markdown file under `$SB_DIR`:

```bash
uv run second_brain new "My brilliant idea about caching"
# Saved: ~/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
```

- The storage directory is created automatically if missing.
- Filenames follow `YYYY-MM-DD-<slug>.md`. On collision, a `-2`, `-3`, …
  suffix is appended.
- If the thought has no slug-able characters (e.g. emoji-only), the
  filename falls back to `YYYY-MM-DD-HHMMSS.md`.
- The file contents are the thought text verbatim (plain markdown, no
  frontmatter).

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
