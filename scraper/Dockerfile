FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including those needed for playwright and postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python scraper requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and chromium browser system dependencies
RUN pip install playwright && playwright install --with-deps chromium

# Copy scraper code
COPY . .

# Default command for celery worker (overridden for celery-beat in docker-compose)
CMD ["celery", "-A celery_app", "worker", "--loglevel=info"]
