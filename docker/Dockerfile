FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV (Python package & binary manager)
RUN pip install uv
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency definitions AND README.md for build validation
COPY pyproject.toml uv.lock* README.md ./

ENV UV_HTTP_TIMEOUT=180
ENV UV_HTTP_RETRIES=5

# Now uv sync will work because README.md exists
RUN uv sync 

# Copy application code
COPY src/ ./src/

# Note: Data files are now in src/data/ (copied above with src/)

# Create necessary directories
RUN mkdir -p /tmp/uploads logs

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - use uv run to ensure correct environment
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]