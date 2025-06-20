FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mlb_scraper.py .

# When Railway triggers the container, run your script directly
CMD ["python", "mlb_scraper.py"]
