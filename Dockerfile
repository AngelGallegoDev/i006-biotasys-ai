# Use Python 3.11 slim image for smaller size
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from the uv image
COPY --from=uv_bin /uv /uv/bin /usr/local/bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# We use --system to install into the system python since it's a container
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application using uv
CMD ["uv", "run", "fastapi", "run", "main.py"]

