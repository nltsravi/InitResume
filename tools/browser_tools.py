from crewai_tools import BaseTool
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random
import json
from core.metrics import PLAYWRIGHT_CRASHES, APPLICATION_STATUS

class PlaywrightApplyTool(BaseTool):
    name: str = "Job Application Submitter"
    description: str = "Fills out forms on Lever/Greenhouse given a URL and candidate data."

    def _run(self, job_url: str, resume_path: str, cover_letter_path: str) -> str:
        # User-Agent Rotation mimicking standard Intel Mac OS environments
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/123.0"
        ]
        
        # Viewport Randomization with standard desktop resolutions
        viewports = [
            {"width": 1440, "height": 900},
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864}
        ]

        selected_user_agent = random.choice(user_agents)
        selected_viewport = random.choice(viewports)

        with sync_playwright() as p:
            # Stealth mode configuration
            browser = p.chromium.launch(
                headless=False, 
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent=selected_user_agent,
                viewport=selected_viewport
            )
            page = context.new_page()
            
            # Mask WebDriver properties using playwright-stealth
            Stealth().apply_stealth_sync(page)
            
            try:
                page.goto(job_url)
                time.sleep(random.uniform(1.5, 3.0)) # Random initial human delay
                
                # Mouse Movements emulation to simulate human interactions
                page.mouse.move(x=random.randint(50, 300), y=random.randint(50, 300))
                time.sleep(random.uniform(0.1, 0.3))
                page.mouse.move(x=random.randint(300, 600), y=random.randint(300, 600))
                time.sleep(random.uniform(0.1, 0.2))
                
                # Typing Delays (50ms per keystroke) function
                def type_with_delay(selector, text):
                    page.locator(selector).scroll_into_view_if_needed()
                    page.locator(selector).focus()
                    page.type(selector, text, delay=50)
                    time.sleep(random.uniform(0.2, 0.5))

                type_with_delay('input[name="name"]', "Ravishankar Jayaraman")
                type_with_delay('input[name="email"]', "your.email@example.com")
                type_with_delay('input[name="linkedin"]', "https://linkedin.com/in/yourprofile")
                
                # File uploads
                page.locator('input[type="file"][name="resume"]').scroll_into_view_if_needed()
                page.set_input_files('input[type="file"][name="resume"]', resume_path)
                time.sleep(random.uniform(0.5, 1.2))
                
                # Click submit with hover and click simulation
                submit_btn = page.locator('button[type="submit"]')
                submit_btn.scroll_into_view_if_needed()
                submit_btn.hover()
                time.sleep(random.uniform(0.2, 0.6))
                submit_btn.click()
                
                page.wait_for_load_state('networkidle')
                APPLICATION_STATUS.labels(status="success").inc()
                return "Application Submitted Successfully"
            except Exception as e:
                # Categorize the crash reason for structured telemetry
                err_msg = str(e).lower()
                if "timeout" in err_msg:
                    reason = "TimeoutError"
                elif "selector" in err_msg or "locator" in err_msg or "find" in err_msg:
                    reason = "DOMChangeError"
                elif "navigation" in err_msg or "load" in err_msg or "reach" in err_msg:
                    reason = "NavigationError"
                else:
                    reason = type(e).__name__
                
                PLAYWRIGHT_CRASHES.labels(reason=reason).inc()
                APPLICATION_STATUS.labels(status="failure").inc()
                return f"Application Failed: {str(e)}"
            finally:
                browser.close()


class LinkedInNetworkTool(BaseTool):
    name: str = "LinkedIn Network Mapper"
    description: str = "Queries LinkedIn API (mocked) to find 1st or 2nd-degree connections working at a target company."

    def _run(self, company_name: str) -> str:
        # Simulates LinkedIn connection query
        connections = [
            {"name": "Alice Johnson", "title": "Engineering Manager", "degree": "1st", "company": company_name},
            {"name": "Bob Smith", "title": "Senior Staff Architect", "degree": "2nd", "company": company_name},
            {"name": "Carol Williams", "title": "Tech Lead, Platform", "degree": "2nd", "company": company_name}
        ]
        return json.dumps(connections)


class CompanyBlogScraperTool(BaseTool):
    name: str = "Company Tech Blog Scraper"
    description: str = "Scrapes recent engineering blogs (mocked) for tech stacks, architectural migrations, and engineering culture."

    def _run(self, company_name: str) -> str:
        # Simulates blog scraping
        articles = [
            {
                "title": f"Migrating our microservices to Kafka at {company_name}",
                "content": "Detailed post about our journey migrating from RabbitMQ to Apache Kafka to handle scaling challenges, database load, and microservices decoupling.",
                "date": "2026-03-15"
            },
            {
                "title": f"Why we migrated to PostgreSQL and schema design at {company_name}",
                "content": "An overview of how we scaled PostgreSQL to 10k read ops/sec using pg_bouncer connection pooling, read replicas, and custom partitioning keys.",
                "date": "2026-01-20"
            },
            {
                "title": f"Adopting Next.js and Tailwind CSS for frontend at {company_name}",
                "content": "How we standardized our web app UI dashboard, improved page load speed, and unified our typography and styles.",
                "date": "2025-11-05"
            }
        ]
        return json.dumps(articles)


class BrowserTools:
    @staticmethod
    def scrape_job_details(url: str) -> dict:
        """
        Mock implementation of job scraper details.
        """
        return {
            "title": "Principal Software Engineer",
            "company": "Tech Corp",
            "url": url,
            "jd_text": "We are looking for a Principal Software Engineer with 18+ years of experience in Python, FastAPI, and Playwright.",
            "salary": "$200,000 - $250,000"
        }

    @staticmethod
    def search_jobs(keywords: str, location: str = "") -> list:
        """
        Mock implementation of job searching.
        """
        return [
            {
                "title": "Principal Software Engineer",
                "company": "Tech Corp",
                "url": "https://example.com/job1",
                "jd_text": "We are looking for a Principal Software Engineer with 18+ years of experience in Python, FastAPI, and Playwright.",
                "salary": "$200,000 - $250,000"
            }
        ]

    @staticmethod
    def fill_application_form(job_url: str, resume_path: str, cover_letter_path: str) -> str:
        """
        Fills form using PlaywrightApplyTool.
        """
        tool = PlaywrightApplyTool()
        return tool._run(job_url, resume_path, cover_letter_path)

