"""
Tasks Module - Celery background tasks
"""

from backend.tasks.celery_app import celery_app
from backend.tasks.document_tasks import (
    process_document_task,
    extract_entities_task,
    build_graph_task,
)

__all__ = [
    "celery_app",
    "process_document_task",
    "extract_entities_task",
    "build_graph_task",
]
