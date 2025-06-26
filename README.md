# Book Catalogue API

REST API for managing books and authors built with FastAPI.

## Setup

Install uv:
```bash
# Official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

Install dependencies:
```bash
uv sync
```

## Running

Start server:
```bash
uv run python main.py
```

Server runs on `http://localhost:8080`

## Testing

Interactive docs: `http://localhost:8080/docs`

Run tests:
```bash
uv run pytest -v
```

## Development

```bash
uv run ruff check    # Linting
uv run pyright       # Type checking
```
