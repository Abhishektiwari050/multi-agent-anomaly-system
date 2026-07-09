FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set default env variables
ENV PYTHONUNBUFFERED=1
ENV STATE_FILE_PATH=tasks.json

# Command to run the agent
CMD ["python", "main.py"]
