#!/usr/bin/env python
"""
Celery worker entry point for TenderIQ.

Run with:
    python worker.py

Or with Celery directly:
    celery -A celery_app worker -Q document_processing -l info
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from celery_app import celery_app


if __name__ == "__main__":
    # Start worker with document_processing queue
    celery_app.worker_main([
        "worker",
        "-Q", "document_processing",
        "-l", "info",
        "--concurrency=2",
    ])