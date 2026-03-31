FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application code
COPY models.py .
COPY __init__.py .
COPY client.py .
COPY inference.py .
COPY openenv.yaml .
COPY server/ server/
COPY data/ data/

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD uv run python -c "import httpx; httpx.get('http://localhost:7860/health').raise_for_status()" || exit 1

# Run the server
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
