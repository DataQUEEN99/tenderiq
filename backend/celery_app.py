"""
Celery application configuration for TenderIQ.
"""
import os
from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "tenderiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.document_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=86400,  # 24 hours
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.document_tasks.process_document": {"queue": "document_processing"},
    "app.tasks.document_tasks.reprocess_document": {"queue": "document_processing"},
}

# Beat schedule (for periodic tasks if needed)
celery_app.conf.beat_schedule = {}


if __name__ == "__main__":
    celery_app.start()