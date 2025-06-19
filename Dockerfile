FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Copy your scraper and install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mlb_scraper.py .

# Set up cron (if running daily inside container)
RUN apt-get update && apt-get install -y cron

# Add crontab entry: runs every day at 11:30 PM PT (6:30 AM UTC)
RUN echo "30 6 * * * python /app/mlb_scraper.py >> /app/cron.log 2>&1" > cronjob && \
    crontab cronjob

# Start cron on container boot
CMD ["cron", "-f"]
