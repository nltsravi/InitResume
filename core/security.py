import os
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Job, Application, BlacklistedCompany

def is_company_blacklisted(db: Session, company_name: str) -> bool:
    """
    Checks if a company is present in the blacklisted companies database table.
    """
    blacklisted = db.query(BlacklistedCompany).filter(
        BlacklistedCompany.company_name.ilike(company_name.strip())
    ).first()
    return blacklisted is not None

def has_applied_recently(db: Session, company_name: str, job_title: str, limit_months: int = 6) -> bool:
    """
    Checks if the user has applied to the same company and job title within the specified months.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=limit_months * 30)
    
    # Query database for recent applications matching company and title
    recent_app = db.query(Application).join(Job).filter(
        Job.company.ilike(company_name.strip()),
        Job.title.ilike(job_title.strip()),
        Application.status == "Applied",
        Application.applied_at >= cutoff_date
    ).first()
    
    return recent_app is not None

def get_vault_credentials() -> dict:
    """
    Loads secrets (OpenAI Keys, LinkedIn Cookies) from env or vault.
    """
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        # Cookies can be stored as a stringified JSON array in LINKEDIN_COOKIES
        "linkedin_cookies": json.loads(os.getenv("LINKEDIN_COOKIES", "[]"))
    }
