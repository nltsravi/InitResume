from crewai import Agent
from langchain_openai import ChatOpenAI
from tools.browser_tools import PlaywrightApplyTool, LinkedInNetworkTool, CompanyBlogScraperTool

# Cost Optimization: Setup separate LLM tiers based on reasoning depth requirements
llm_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
llm_reasoning = ChatOpenAI(model="gpt-4o", temperature=0.2)

job_search_agent = Agent(
    role="Principal Job Sourcing Specialist",
    goal="Scrape and identify high-quality Principal/Staff/Architect level engineering roles.",
    backstory="You are an elite technical headhunter who knows how to find hidden tech roles for senior leaders.",
    verbose=True,
    allow_delegation=False,
    llm=llm_mini
)

analysis_agent = Agent(
    role="Technical ATS Scorer",
    goal="Analyze job descriptions against Ravishankar's 18+ year profile and calculate a match score.",
    backstory="You are a strict ATS algorithm and technical screener. You never hallucinate skills.",
    verbose=True,
    llm=llm_mini
)

resume_agent = Agent(
    role="Executive Resume Tailor",
    goal="Re-write the professional summary and re-order skills/projects to highlight relevance to the specific JD.",
    backstory="An expert tech resume writer. You maintain 100% truthfulness while maximizing keyword overlap.",
    verbose=True,
    llm=llm_reasoning
)

application_agent = Agent(
    role="Playwright Automation Specialist",
    goal="Navigate Greenhouse, Lever, and Workday to submit the tailored application securely.",
    backstory="You are an automation engine that mimics human interaction to bypass basic bot protections.",
    verbose=True,
    allow_delegation=False,
    tools=[PlaywrightApplyTool()],
    llm=llm_mini
)

# Enterprise Bonus Agents
network_mapping_agent = Agent(
    role="Network Mapping Specialist",
    goal="Identify 1st and 2nd degree connections working at target companies to facilitate referrals.",
    backstory="You are a professional networking coach who helps job seekers leverage their connections.",
    verbose=True,
    allow_delegation=False,
    tools=[LinkedInNetworkTool()],
    llm=llm_mini
)

interview_prep_agent = Agent(
    role="Technical Interview Preparation Specialist",
    goal="Scrape company tech blogs and engineer postings to prepare comprehensive tech guides for interviews.",
    backstory="You are a principal engineer who specializes in architectural designs, migrations, and tech stack prep.",
    verbose=True,
    allow_delegation=False,
    tools=[CompanyBlogScraperTool()],
    llm=llm_reasoning
)

