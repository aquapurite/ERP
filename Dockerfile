FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render uses PORT env var)
EXPOSE 10000

# Start command - use shell form to expand $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
