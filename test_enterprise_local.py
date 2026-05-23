import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os

# Set mock env vars BEFORE importing any project files
os.environ["OPENAI_API_KEY"] = "mock-key"
os.environ["DATABASE_URL"] = "sqlite:///test_jobs.db"

# Remove any pre-existing test db file
if os.path.exists("test_jobs.db"):
    try:
        os.remove("test_jobs.db")
    except Exception:
        pass

from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal, Job, Application, Referral, InterviewPrep
from api.main import app

class TestEnterpriseEndpoints(unittest.TestCase):
    def setUp(self):
        # Ensure clean state by removing test db if it exists
        if os.path.exists("test_jobs.db"):
            try:
                os.remove("test_jobs.db")
            except Exception:
                pass
                
        # Create all tables in sqlite database
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.client = TestClient(app)

        # Create a mock job and application in database
        self.mock_job = Job(
            title="Principal Engineer",
            company="Google",
            url="https://google.com/jobs/1",
            jd_text="Looking for a seasoned system architect with experience in python and scalability.",
            salary="$200,000"
        )
        self.db.add(self.mock_job)
        self.db.commit()

        self.mock_application = Application(
            job_id=self.mock_job.id,
            status="pending",
            match_score=0.9
        )
        self.db.add(self.mock_application)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        engine.dispose()
        if os.path.exists("test_jobs.db"):
            try:
                os.remove("test_jobs.db")
            except Exception:
                pass

    @patch('api.main.Crew.kickoff')
    def test_generate_referrals(self, mock_kickoff):
        # Mock Crew.kickoff to return a mock referral draft
        mock_kickoff.return_value = "Mocked Referral Draft: Dear Alice, I'm interested in the Principal Engineer role..."

        response = self.client.post(f"/api/v1/applications/{self.mock_application.id}/referrals")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("referral", data)
        self.assertEqual(data["referral"]["connection_name"], "Alice Johnson")
        self.assertEqual(data["referral"]["connection_degree"], "1st")
        self.assertIn("Mocked Referral Draft", data["referral"]["referral_draft"])

        # Check DB persistence (use session refresh or expire_all to bypass caching)
        self.db.expire_all()
        referral_in_db = self.db.query(Referral).filter(Referral.application_id == self.mock_application.id).first()
        self.assertIsNotNone(referral_in_db)
        self.assertEqual(referral_in_db.connection_name, "Alice Johnson")
        self.assertEqual(referral_in_db.referral_draft, "Mocked Referral Draft: Dear Alice, I'm interested in the Principal Engineer role...")

        # Test GET endpoint
        get_response = self.client.get(f"/api/v1/applications/{self.mock_application.id}/referrals")
        self.assertEqual(get_response.status_code, 200)
        get_data = get_response.json()
        self.assertEqual(len(get_data["referrals"]), 1)
        self.assertEqual(get_data["referrals"][0]["connection_name"], "Alice Johnson")

    @patch('api.main.Crew.kickoff')
    def test_schedule_interview(self, mock_kickoff):
        # Mock Crew.kickoff to return a mock prep sheet
        mock_kickoff.return_value = "Mocked Prep Sheet: System Design with Kafka and PostgreSQL..."

        schedule_data = {
            "scheduled_at": datetime.utcnow().isoformat(),
            "blog_urls": "https://google.com/tech-blog"
        }

        response = self.client.post(
            f"/api/v1/applications/{self.mock_application.id}/schedule-interview",
            json=schedule_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("interview_prep", data)
        self.assertEqual(data["interview_prep"]["scraped_blog_urls"], "https://google.com/tech-blog")
        self.assertIn("Mocked Prep Sheet", data["interview_prep"]["prep_sheet_content"])

        # Check DB status update on Application (expire_all to bypass session cache)
        self.db.expire_all()
        app_in_db = self.db.query(Application).filter(Application.id == self.mock_application.id).first()
        self.assertEqual(app_in_db.status, "interviewing")

        # Check DB persistence of InterviewPrep
        prep_in_db = self.db.query(InterviewPrep).filter(InterviewPrep.application_id == self.mock_application.id).first()
        self.assertIsNotNone(prep_in_db)
        self.assertEqual(prep_in_db.scraped_blog_urls, "https://google.com/tech-blog")
        self.assertEqual(prep_in_db.prep_sheet_content, "Mocked Prep Sheet: System Design with Kafka and PostgreSQL...")

        # Test GET endpoint
        get_response = self.client.get(f"/api/v1/applications/{self.mock_application.id}/interview-prep")
        self.assertEqual(get_response.status_code, 200)
        get_data = get_response.json()
        self.assertEqual(len(get_data["interview_preps"]), 1)
        self.assertEqual(get_data["interview_preps"][0]["scraped_blog_urls"], "https://google.com/tech-blog")

    @patch('api.main.extract_resume_keywords')
    @patch('tools.browser_tools.BrowserTools.search_jobs')
    def test_search_linkedin_jobs(self, mock_search_jobs, mock_extract):
        # Mock resume extraction and job search
        mock_extract.return_value = "Python, FastAPI"
        mock_search_jobs.return_value = [
            {
                "title": "Principal Engineer",
                "company": "Stripe",
                "url": "https://jobs.lever.co/stripe/principal-eng",
                "jd_text": "Python FastAPI Playwright",
                "salary": "$200k"
            }
        ]
        
        response = self.client.post("/api/v1/search-linkedin-jobs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["jobs"]), 1)
        self.assertEqual(data["jobs"][0]["company"], "Stripe")
        
        # Test GET applications endpoint
        get_response = self.client.get("/api/v1/applications")
        self.assertEqual(get_response.status_code, 200)
        apps = get_response.json()
        self.assertTrue(any(app["company"] == "Stripe" for app in apps))

    def test_submit_answer(self):
        answer_data = {"answer": "I have 5 years experience with FastAPI."}
        response = self.client.post(
            f"/api/v1/applications/{self.mock_application.id}/submit-answer",
            json=answer_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        # Verify database update
        self.db.expire_all()
        app_in_db = self.db.query(Application).filter(Application.id == self.mock_application.id).first()
        self.assertEqual(app_in_db.status, "applied")

if __name__ == "__main__":
    unittest.main()
