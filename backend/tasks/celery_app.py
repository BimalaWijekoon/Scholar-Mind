"""
Celery Application Configuration
"""

from celery import Celery
from kombu import Queue
import os

# Redis URLs from environment — use separate DBs to avoid data collision
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Create Celery app
celery_app = Celery(
    "scholar_mind",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.tasks.document_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,
    
    # Task routing
    task_queues=(
        Queue("default", routing_key="task.#"),
        Queue("documents", routing_key="document.#"),
        Queue("graph", routing_key="graph.#"),
    ),
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_routing_key="task.default",
    
    # Task routes
    task_routes={
        "backend.tasks.document_tasks.process_document_task": {
            "queue": "documents",
            "routing_key": "document.process",
        },
        "backend.tasks.document_tasks.extract_entities_task": {
            "queue": "graph",
            "routing_key": "graph.extract",
        },
        "backend.tasks.document_tasks.build_graph_task": {
            "queue": "graph",
            "routing_key": "graph.build",
        },
    },
    
    # Beat scheduler (for periodic tasks)
    beat_schedule={
        "cleanup-old-results": {
            "task": "backend.tasks.document_tasks.cleanup_task",
            "schedule": 3600.0,  # Every hour
        },
    },
    
    # Retry settings
    task_annotations={
        "*": {
            "rate_limit": "100/m",
            "max_retries": 3,
            "default_retry_delay": 60,
        },
    },
)


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task with error handling."""
    
    abstract = True
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Task {task_id} completed successfully")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Task {task_id} retrying due to: {exc}")


# Set as default task base
celery_app.Task = BaseTask


def get_celery_app() -> Celery:
    """Get the Celery application instance."""
    return celery_app
