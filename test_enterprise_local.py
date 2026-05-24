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
        # Drop and recreate tables to ensure absolute isolation without breaking the connection pool
        Base.metadata.drop_all(bind=engine)
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

    @patch('api.main.ResumeRAGPipeline')
    @patch('api.main.ChatOpenAI')
    @patch('api.main.PdfReader')
    def test_upload_resume_success(self, mock_pdf_reader, mock_chat_openai, mock_rag_pipeline):
        # Mocking PDF Reader to return some text
        mock_pdf_reader.return_value.pages = [MagicMock()]
        mock_pdf_reader.return_value.pages[0].extract_text.return_value = "Ravishankar is a principal engineer with 18+ years experience..."
        
        # Mocking ChatOpenAI predict method
        mock_llm_instance = MagicMock()
        mock_llm_instance.predict.return_value = '{"name": "Ravishankar", "experience_years": "18+ years", "skills": ["Python", "FastAPI"], "summary": "Experienced engineer."}'
        mock_chat_openai.return_value = mock_llm_instance
        
        # Mocking resume upload file payload
        file_content = b"%PDF-1.4\n%..."
        
        import io
        response = self.client.post(
            "/api/v1/upload-resume",
            files={"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["filename"], "resume.pdf")
        self.assertEqual(data["analysis"]["name"], "Ravishankar")
        self.assertEqual(data["analysis"]["experience_years"], "18+ years")

    def test_upload_resume_invalid_format(self):
        import io
        response = self.client.post(
            "/api/v1/upload-resume",
            files={"file": ("resume.txt", io.BytesIO(b"Not a PDF file"), "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are accepted", response.json()["detail"])

    def test_upload_resume_invalid_magic_bytes(self):
        import io
        response = self.client.post(
            "/api/v1/upload-resume",
            files={"file": ("resume.pdf", io.BytesIO(b"Hello world PDF!"), "application/pdf")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file format", response.json()["detail"])

    @patch('tempfile.SpooledTemporaryFile.tell')
    def test_upload_resume_exceeds_size(self, mock_tell):
        mock_tell.return_value = 301 * 1024 * 1024
        import io
        response = self.client.post(
            "/api/v1/upload-resume",
            files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4\n%..."), "application/pdf")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("exceeds the 300MB limit", response.json()["detail"])

    @patch('os.path.exists')
    @patch('os.stat')
    def test_get_resume_status_not_exists(self, mock_stat, mock_exists):
        mock_exists.return_value = False
        response = self.client.get("/api/v1/resume-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"exists": False})

    @patch('os.path.exists')
    @patch('os.stat')
    @patch('api.main.extract_resume_keywords')
    def test_get_resume_status_exists_fallback(self, mock_keywords, mock_stat, mock_exists):
        def side_effect(path):
            if "resume.pdf" in path:
                return True
            return False
        mock_exists.side_effect = side_effect
        
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_mtime = 1716500000
        
        mock_keywords.return_value = "Python, FastAPI, AWS"
        
        response = self.client.get("/api/v1/resume-status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["exists"])
        self.assertEqual(data["filename"], "resume.pdf")
        self.assertEqual(data["analysis"]["name"], "Ravishankar")
        self.assertEqual(data["analysis"]["skills"], ["Python", "FastAPI", "AWS"])

def tearDownModule():
    # Clean up sqlite DB file after all tests finish
    if os.path.exists("test_jobs.db"):
        try:
            os.remove("test_jobs.db")
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
