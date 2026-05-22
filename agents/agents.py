from crewai import Agent
from langchain_openai import ChatOpenAI
from tools.browser_tools import BrowserTools

class ApplicationAgents:
    def __init__(self):
        # Configure separate LLM tiers based on reasoning requirements
        self.llm_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        self.llm_reasoning = ChatOpenAI(model="gpt-4o", temperature=0.2)

    def job_researcher_agent(self) -> Agent:
        return Agent(
            role="Senior Job Researcher",
            goal="Scrape, discover, and filter relevant job listings matching the user's criteria.",
            backstory=(
                "You are an expert at navigating job boards, developer portals, and applicant tracking systems (ATS). "
                "You know how to query platforms like LinkedIn, Indeed, and Lever to extract clean, relevant job data, "
                "skipping sponsored spam and finding high-fit roles."
            ),
            tools=[BrowserTools.scrape_job_details, BrowserTools.search_jobs],
            llm=self.llm_mini,
            verbose=True,
            allow_delegation=False
        )

    def resume_customizer_agent(self) -> Agent:
        return Agent(
            role="Professional Resume Customizer",
            goal="Analyze the job description and customize the user's resume/skills profile to maximize ATS score.",
            backstory=(
                "You have years of experience in recruitment and HR. You know exactly what recruiters and ATS "
                "parsers look for in resumes. You highlight key achievements, rephrase skill summaries, and align "
                "descriptions perfectly with the job posting while maintaining complete truthfulness."
            ),
            llm=self.llm_reasoning,
            verbose=True,
            allow_delegation=False
        )

    def auto_applier_agent(self) -> Agent:
        return Agent(
            role="Autonomous Form Submission Agent",
            goal="Navigate application portals and automatically submit applications with customized resumes.",
            backstory=(
                "An expert automation specialist powered by Playwright. You can fill text inputs, select dropdowns, "
                "upload files, and complete captcha bypass flows to submit job application forms seamlessly and securely."
            ),
            tools=[BrowserTools.fill_application_form],
            llm=self.llm_mini,
            verbose=True,
            allow_delegation=False
        )

    def network_mapping_agent(self) -> Agent:
        from tools.browser_tools import LinkedInNetworkTool
        return Agent(
            role="Network Mapping Specialist",
            goal="Identify 1st and 2nd degree connections working at target companies to facilitate referrals.",
            backstory="You are a professional networking coach who helps job seekers leverage their connections.",
            tools=[LinkedInNetworkTool()],
            llm=self.llm_mini,
            verbose=True,
            allow_delegation=False
        )

    def interview_prep_agent(self) -> Agent:
        from tools.browser_tools import CompanyBlogScraperTool
        return Agent(
            role="Technical Interview Preparation Specialist",
            goal="Scrape company tech blogs and engineer postings to prepare comprehensive tech guides for interviews.",
            backstory="You are a principal engineer who specializes in architectural designs, migrations, and tech stack prep.",
            tools=[CompanyBlogScraperTool()],
            llm=self.llm_reasoning,
            verbose=True,
            allow_delegation=False
        )
