from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "job_scout_scraper",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'scrape-every-10-min': {
            'task': 'tasks.scheduled_scrape',
            'schedule': 600.0, # 10 minutes
        },
    }
)

if __name__ == "__main__":
    app.start()
