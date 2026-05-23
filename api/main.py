from fastapi import FastAPI, BackgroundTasks, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from langchain_community.callbacks import get_openai_callback
from datetime import datetime
from typing import Optional
import os
import sys

# Ensure local imports resolve correctly when running the server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import recruitment_crew
from database import get_db, Job, Application, Referral, InterviewPrep
from core.learning_agent import LearningAgent
from core.metrics import TOKENS_USED
from crewai import Crew
from document_tasks import network_mapping_task, interview_prep_task
from recruitment_crew import network_mapping_agent, interview_prep_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CrewAI Auto-Apply Core")

# Enable CORS for frontend browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobSubmit(BaseModel):
    url: str

class GmailWebhookEvent(BaseModel):
    message_id: str
    subject: str
    body_snippet: str
    company_name: str
    job_title: str

def run_crew_with_metrics(job_url: str):
    """
    Runs the recruitment crew workflow, capturing LLM token usage using the get_openai_callback.
    Also updates the application status in the database.
    """
    print(f"[Telemetry] Triggering crew kickoff for: {job_url}")
    
    # Fetch database session manually inside the background thread to avoid cross-thread session usage
    from database import SessionLocal, Job, Application
    db = SessionLocal()
    
    db_job = db.query(Job).filter(Job.url == job_url).first()
    db_app = None
    if db_job:
        db_app = db.query(Application).filter(Application.job_id == db_job.id).first()
        if db_app:
            db_app.status = "matched"  # Progressing status
            db.commit()

    try:
        with get_openai_callback() as cb:
            result = recruitment_crew.kickoff(inputs={"job_url": job_url})
            # Increment prompt and completion token counts in Prometheus
            # Note: We attribute the tokens to the main models utilized in our stack
            TOKENS_USED.labels(model="gpt-4o-mini", type="prompt").inc(cb.prompt_tokens)
            TOKENS_USED.labels(model="gpt-4o-mini", type="completion").inc(cb.completion_tokens)
            print(f"[Telemetry] Work run complete. Tokens Used: Prompt={cb.prompt_tokens}, Completion={cb.completion_tokens}")
            
            if db_app:
                db_app.status = "applied"
                db.commit()
            return result
    except Exception as e:
        print(f"[Telemetry] Exception encountered during crew execution: {e}")
        if db_app:
            db_app.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()

@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/trigger-apply")
async def trigger_application(job: JobSubmit, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if job exists in DB, if not create it
    db_job = db.query(Job).filter(Job.url == job.url).first()
    if not db_job:
        db_job = Job(
            title="Custom Sourced Role",
            company="Unknown Company",
            url=job.url,
            jd_text="Manually submitted URL pipeline run.",
            salary=""
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
    db_app = db.query(Application).filter(Application.job_id == db_job.id).first()
    if not db_app:
        db_app = Application(
            job_id=db_job.id,
            status="pending",
            match_score=0.85
        )
        db.add(db_app)
        db.commit()
        db.refresh(db_app)
    else:
        db_app.status = "pending"
        db.commit()

    background_tasks.add_task(run_crew_with_metrics, job.url)
    return {"status": "Application workflow initiated", "job": job.url, "app_id": db_app.id}

@app.get("/api/v1/pending-approvals")
async def get_approvals():

    # Returns jobs waiting for manual input (e.g. "What is your expected salary?")
    return {"pending_approvals": []}

@app.post("/api/v1/gmail-webhook")
async def handle_gmail_webhook(event: GmailWebhookEvent, db: Session = Depends(get_db)):
    """
    Webhook triggered by Gmail API notifications.
    Parses email body for typical rejection keywords and kicks off the learning loop.
    """
    subject_lower = event.subject.lower()
    body_lower = event.body_snippet.lower()
    
    # Common rejection phrasing
    rejection_keywords = [
        "thank you for applying", 
        "moved forward with other candidates", 
        "not selected", 
        "unfortunately",
        "pursue other candidates"
    ]
    
    is_rejection = any(kw in body_lower or kw in subject_lower for kw in rejection_keywords)
    
    if is_rejection:
        # Trigger the learning agent feedback loop to adjust weights
        adjustment = LearningAgent.process_rejection(
            db=db, 
            company_name=event.company_name, 
            job_title=event.job_title
        )
        return {
            "event": "processed", 
            "type": "rejection_received", 
            "learning_adjustment": adjustment
        }
        
    return {"event": "processed", "type": "ignored", "reason": "No rejection indicators found"}


class InterviewSchedule(BaseModel):
    scheduled_at: datetime
    blog_urls: Optional[str] = None


@app.post("/api/v1/applications/{app_id}/referrals")
def generate_referrals(app_id: int, db: Session = Depends(get_db)):
    """
    Triggers the Network Mapping Agent to find LinkedIn connections at the target company
    and draft a referral message.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        return {"error": "Application not found"}
    
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        return {"error": "Job associated with application not found"}
        
    print(f"[Enterprise] Initiating connection search for company: {job.company}")
    
    # Run the Network Mapping Crew
    referral_crew = Crew(
        agents=[network_mapping_agent],
        tasks=[network_mapping_task],
        verbose=True
    )
    
    result = referral_crew.kickoff(inputs={"company_name": job.company})
    
    # Create database entry
    referral = Referral(
        application_id=app_id,
        connection_name="Alice Johnson", # Mock representative connection
        connection_degree="1st",
        referral_draft=str(result)
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    return {
        "status": "Referral draft generated successfully",
        "referral": {
            "id": referral.id,
            "connection_name": referral.connection_name,
            "connection_degree": referral.connection_degree,
            "referral_draft": referral.referral_draft
        }
    }


@app.post("/api/v1/applications/{app_id}/schedule-interview")
def schedule_interview(app_id: int, schedule: InterviewSchedule, db: Session = Depends(get_db)):
    """
    Schedules an interview date and triggers the Interview Prep Agent to scrape
    recent tech blogs of the company and compile a system design and prep sheet.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        return {"error": "Application not found"}
        
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        return {"error": "Job associated with application not found"}

    print(f"[Enterprise] Scheduling interview and fetching prep guides for company: {job.company}")
    
    # Update application status
    application.status = "interviewing"
    
    # Run the Interview Prep Crew
    prep_crew = Crew(
        agents=[interview_prep_agent],
        tasks=[interview_prep_task],
        verbose=True
    )
    
    result = prep_crew.kickoff(inputs={"company_name": job.company})
    
    # Create prep sheet database entry
    urls = schedule.blog_urls or f"https://{job.company.lower().replace(' ', '')}.com/tech-blog"
    prep = InterviewPrep(
        application_id=app_id,
        scraped_blog_urls=urls,
        prep_sheet_content=str(result),
        scheduled_at=schedule.scheduled_at
    )
    db.add(prep)
    db.commit()
    db.refresh(prep)
    
    return {
        "status": "Interview scheduled and prep sheet generated",
        "interview_prep": {
            "id": prep.id,
            "scheduled_at": prep.scheduled_at,
            "scraped_blog_urls": prep.scraped_blog_urls,
            "prep_sheet_content": prep.prep_sheet_content
        }
    }


@app.get("/api/v1/applications/{app_id}/referrals")
def get_referrals(app_id: int, db: Session = Depends(get_db)):
    """
    Fetches the generated referral drafts for an application.
    """
    referrals = db.query(Referral).filter(Referral.application_id == app_id).all()
    return {
        "application_id": app_id,
        "referrals": [
            {
                "id": ref.id,
                "connection_name": ref.connection_name,
                "connection_degree": ref.connection_degree,
                "referral_draft": ref.referral_draft,
                "created_at": ref.created_at
            } for ref in referrals
        ]
    }


@app.get("/api/v1/applications/{app_id}/interview-prep")
def get_interview_prep(app_id: int, db: Session = Depends(get_db)):
    """
    Fetches the generated interview prep guides for an application.
    """
    preps = db.query(InterviewPrep).filter(InterviewPrep.application_id == app_id).all()
    return {
        "application_id": app_id,
        "interview_preps": [
            {
                "id": p.id,
                "scheduled_at": p.scheduled_at,
                "scraped_blog_urls": p.scraped_blog_urls,
                "prep_sheet_content": p.prep_sheet_content,
                "created_at": p.created_at
            } for p in preps
        ]
    }


class QuestionAnswer(BaseModel):
    answer: str


def extract_resume_keywords() -> str:
    resume_path = "/Users/ravij/InitResume/resume.pdf"
    if not os.path.exists(resume_path):
        print(f"[API] resume.pdf not found at: {resume_path}. Using fallback keywords.")
        return "Python, FastAPI, Playwright"
    try:
        from pypdf import PdfReader
        print(f"[API] Loading resume.pdf for keyword extraction...")
        reader = PdfReader(resume_path)
        text = ""
        for page in reader.pages[:2]: # read first two pages
            text += page.extract_text() or ""
        if not text.strip():
            return "Python, FastAPI, Playwright"
        
        # Call ChatOpenAI to get keywords
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = f"Given the following resume text, extract the top 3-5 technical skills or keywords as a simple comma-separated list (e.g. 'Python, FastAPI, Kubernetes'):\n\n{text[:3000]}"
        response = llm.predict(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error extracting keywords from resume: {e}")
        return "Python, FastAPI, Playwright"


@app.get("/api/v1/applications")
def get_applications(db: Session = Depends(get_db)):
    """
    Fetches all applications and their jobs from DB for Kanban board.
    """
    apps = db.query(Application).all()
    results = []
    for app in apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if not job:
            continue
        
        # Map DB statuses to frontend Kanban column categories
        status_map = {
            "pending": "Found",
            "matched": "Scored",
            "applied": "Applied",
            "failed": "Rejected",
            "interviewing": "Applied",
            "Rejected": "Rejected"
        }
        ui_status = status_map.get(app.status, app.status)
        
        results.append({
            "id": str(app.id),
            "title": job.title,
            "company": job.company,
            "location": "Remote",
            "url": job.url,
            "salary": job.salary,
            "matchScore": int(app.match_score * 100) if app.match_score and app.match_score <= 1.0 else int(app.match_score or 0),
            "status": ui_status
        })
    return results


@app.post("/api/v1/search-linkedin-jobs")
def search_linkedin_jobs(db: Session = Depends(get_db)):
    """
    Parses resume.pdf to extract keywords, searches LinkedIn (mocked),
    evaluates matching score, and registers found jobs/applications in database.
    """
    keywords = extract_resume_keywords()
    print(f"[API] Searching jobs with extracted keywords: {keywords}")
    
    from tools.browser_tools import BrowserTools
    from scoring import calculate_match
    
    found_jobs = BrowserTools.search_jobs(keywords=keywords)
    applications_created = []
    
    for j in found_jobs:
        # Check if job already exists in DB
        db_job = db.query(Job).filter(Job.url == j["url"]).first()
        if not db_job:
            db_job = Job(
                title=j["title"],
                company=j["company"],
                url=j["url"],
                jd_text=j["jd_text"],
                salary=j["salary"]
            )
            db.add(db_job)
            db.commit()
            db.refresh(db_job)
        
        # Check if application already exists
        db_app = db.query(Application).filter(Application.job_id == db_job.id).first()
        if not db_app:
            # Score the job
            passed_threshold, score = calculate_match(db_job.jd_text, {})
            db_app = Application(
                job_id=db_job.id,
                status="matched" if score > 75 else "failed",
                match_score=score / 100.0
            )
            db.add(db_app)
            db.commit()
            db.refresh(db_app)
            
        applications_created.append({
            "id": str(db_app.id),
            "title": db_job.title,
            "company": db_job.company,
            "location": "Remote",
            "url": db_job.url,
            "salary": db_job.salary,
            "matchScore": int(db_app.match_score * 100) if db_app.match_score <= 1.0 else int(db_app.match_score),
            "status": "Scored" if db_app.status == "matched" else "Rejected"
        })
        
    return {"status": "success", "jobs": applications_created}


@app.post("/api/v1/applications/{app_id}/submit-answer")
def submit_answer(app_id: int, qa: QuestionAnswer, db: Session = Depends(get_db)):
    """
    Endpoint called when the user resolves a custom question on the frontend.
    Updates the application status to show applied.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        return {"error": "Application not found"}
        
    application.status = "applied"
    db.commit()
    print(f"[API] Application {app_id} custom answer submitted: {qa.answer}. Resumed and updated.")
    return {"status": "success", "message": "Answer submitted and application resumed"}

