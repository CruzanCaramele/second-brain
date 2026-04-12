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

Save a quick thought as a markdown file:

```bash
uv run second_brain new "My brilliant idea about caching"
# Saved: ~/second_brain/2026-04-12-my-brilliant-idea-about-caching.md
```

The file is written under `$SB_DIR` (default `~/second_brain/`). The
directory is created if it doesn't exist. If a file with the same
date+slug already exists, a numeric suffix (`-2`, `-3`, …) is appended.

With dev environment loaded:

```bash
uv run --env-file .env second_brain new "another idea"
```

Via Python module:

```bash
uv run python -m second_brain new "yet another idea"
```

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
