FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN chmod +x docker_entrypoint.sh

# Volumes for output and persistent state
VOLUME ["/out", "/data"]

# Use Docker entrypoint for volume support
ENTRYPOINT ["./docker_entrypoint.sh"]

# Default command: run with default preset
CMD ["--preset", "default", "--hours", "6", "--top", "30"]
