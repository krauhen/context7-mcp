# Pull baseimage from mgb mirror
FROM repository.migros.net/astral/uv:python3.11-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Save RAM with uv/python configuration
ENV UV_CONCURRENT_INSTALLS=1 \
    UV_CONCURRENT_BUILDS=1 \
    UV_CONCURRENT_DOWNLOADS=1 \
    UV_NO_CACHE=true

# Set workdir
WORKDIR /app

# Install some apt packages that are needed or helpfull for debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    libpq5 \
    curl \
    wget \
    net-tools \
    && rm -rf /var/lib/apt/lists/*


# Set env variables and python interpreter at /app/.venv/bin/python
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy project install files
COPY uv.lock pyproject.toml ./

# Install packages
RUN uv sync --locked --no-install-project --no-dev

# Add user and group
RUN addgroup appgroup --gid 6666 \
    && adduser -u 5555 --gid 6666 --disabled-password --gecos "" appuser

# Copy all files to app
COPY --chown=5555:6666 . /app

# Install packages again
RUN uv sync --locked --no-dev

# Step into user appuser
USER appuser

# Start application
ENTRYPOINT ["python", "src/main.py"]