# Context7 Python

A Python FastAPI + MCP server that retrieves and serves documentation content from Context7.

## Requirements
- Python 3.11+
- `uvicorn`, `fastapi`, and other dependencies listed in `pyproject.toml`.
- `.env` file with configuration (see `.env.example`).

## Installation
1. Create an API-Key on https://context7.com/
2. Copy .env.template to .env and edit values
3. Run containerd service
4. Connect via http with the service from your client/IDE

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
#### MCP endpoint is at https://localhost:30123/mcp

### Development
```bash
$ uv venv .venv
(.venv)$ source .venv/bin/activate
(.venv)$ uv sync
(.venv)$ uv sync --extra dev
# Edit the code
(.venv)$ CERT_FILE=data/certs/cert.pem KEY_FILE=data/certs/key.pem python src/main.py