FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Use uv to install base dependencies to system environment
RUN uv pip install --system -r requirements.txt

# Copy application code and startup script
COPY app/ ./app/
COPY start.sh .

# Create dependencies directory
RUN mkdir -p /dependencies

# Set startup script permissions
RUN chmod +x start.sh

# Expose port
EXPOSE 8194

# Use startup script instead of direct uvicorn command
CMD ["./start.sh"]