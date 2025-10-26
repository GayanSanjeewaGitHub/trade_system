FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY mcp_server/requirements.txt /app/mcp_server/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r mcp_server/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY mcp_server/ /app/mcp_server/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port for HTTP transport (optional)
EXPOSE 8080

# Run MCP server
CMD ["python", "mcp_server/server.py"]
