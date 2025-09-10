# Context7 Python

A Python FastAPI + MCP server that retrieves and serves documentation content from Context7.

## Requirements
- Python 3.11+
- `uvicorn`, `fastapi`, and other dependencies listed in `pyproject.toml`.
- `.env` file with configuration (see `.env.example`).

## Installation
### Productive
```bash
$ make all
```
or
```bash
$ docker-compose build
$ docker-compose up
```
#### Go to https://localhost:30123/docs to view OpenAPI
### Development
```bash
$ uv venv .venv
(.venv)$ source .venv/bin/activate
(.venv)$ uv sync
(.venv)$ uv sync --extra dev