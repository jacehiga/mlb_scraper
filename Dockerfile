FROM python:3.11-slim

# Helpful runtime env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# If you still need VCS installs, keep git. If not, remove this block.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Faster, more compatible builds
RUN python -m pip install --upgrade pip setuptools wheel

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of your app (or keep just the file if it's truly single-file)
COPY . .

# Run as non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Stream logs immediately
ENTRYPOINT ["python", "-u", "mlb_scraper.py"]
