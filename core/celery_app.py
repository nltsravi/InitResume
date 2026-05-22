import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "auto_apply_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "core.celery_app.async_run_pipeline": {"queue": "default"},
        "core.celery_app.async_scrape_job": {"queue": "scraping"},
    }
)

@celery_app.task
def async_run_pipeline(keywords: str, resume_path: str, location: str):
    """
    Background worker task to kickoff the CrewAI pipeline.
    """
    print(f"[Celery] Starting background pipeline execution for keywords='{keywords}'...")
    from main import run_job_application_pipeline
    try:
        result = run_job_application_pipeline(keywords, resume_path, location)
        return {"status": "success", "result": str(result)}
    except Exception as e:
        print(f"[Celery] Failed executing job application pipeline: {e}")
        return {"status": "failed", "error": str(e)}

@celery_app.task
def async_scrape_job(url: str):
    """
    Background worker task to scrape details of a single job.
    """
    print(f"[Celery] Scraping single job at: {url}...")
    from tools.browser_tools import BrowserTools
    try:
        result = BrowserTools.scrape_job_details(url)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
