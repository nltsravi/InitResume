from .celery_app import celery_app, async_run_pipeline, async_scrape_job

# Celery looks for the application instance (conventionally 'app') in core.tasks
app = celery_app
