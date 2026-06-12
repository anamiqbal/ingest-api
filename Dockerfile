# Hardened container image
# - slim base image (smaller attack surface)
# - runs as a non-root user (defense in depth)
# - no build tools left in the final image

FROM python:3.12-slim

# Create an unprivileged user to run the app
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Install dependencies first (layer caching: deps change less often than code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Writable location for the SQLite database
RUN mkdir /data && chown appuser:appuser /data
ENV DB_PATH=/data/data.db

USER appuser

EXPOSE 8010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
