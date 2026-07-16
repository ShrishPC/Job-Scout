FROM job-scout-backend:latest

WORKDIR /app

# Install Playwright and chromium browser system dependencies
RUN playwright install --with-deps chromium

# Copy scraper code
COPY . .

# Default command for celery worker (overridden for celery-beat in docker-compose)
CMD ["celery", "-A celery_app", "worker", "--loglevel=info"]

