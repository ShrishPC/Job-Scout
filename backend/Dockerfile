FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies for PostgreSQL adapter and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . .

EXPOSE 8000

# Run db initialization, then start the FastAPI application
CMD ["sh", "-c", "python init_db.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
