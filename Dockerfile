# Use slim Python 3.14 as base image
FROM python:3.14-slim

# Set working directory in container
WORKDIR /app

# System dependencies (not needed currently)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining application code
COPY . .

# Create directory for persistent data (state and logs)
RUN mkdir -p /app/data

# Default command to run the sync service
CMD ["python", "main.py"]