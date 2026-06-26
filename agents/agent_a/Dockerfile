FROM python:3.11-slim

WORKDIR /app

# Enable unbuffered stream output
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library and agent-specific code
COPY shared/ ./shared/
COPY agents/agent_a/ ./agents/agent_a/

CMD ["python", "agents/agent_a/main.py"]
