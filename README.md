# second-brain

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

Via the CLI entrypoint:

```bash
uv run second_brain
```

With dev environment loaded:

```bash
uv run --env-file .env second_brain
```

Via Python module:

```bash
uv run python -m second_brain
```

## Log Output

```
2026-04-11 21:22:10 | INFO | second_brain.app:main:29 | Hello from second_brain!
```

## Environment Variables

`.env.example` is the committed template — copy it to `.env` for development:

```bash
cp .env.example .env
```

| Variable    | Default   | Description                                    |
|-------------|-----------|------------------------------------------------|
| `LOG_LEVEL` | `INFO`    | Console log level (`DEBUG`, `INFO`, `WARNING`, …). Set to `DEBUG` in `.env` for verbose console output. |
| `LOG_FILE`  | `app.log` | Path to the log file.                          |

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
