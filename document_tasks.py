from crewai import Task
from recruitment_crew import (
    job_search_agent, 
    analysis_agent, 
    resume_agent, 
    application_agent,
    network_mapping_agent,
    interview_prep_agent
)

search_task = Task(
    description="Search and identify engineering roles at Principal/Staff/Architect levels matching the candidate criteria.",
    expected_output="A list of job opportunities with titles, companies, URLs and JDs.",
    agent=job_search_agent
)

score_task = Task(
    description="Analyze job descriptions against the candidate's profile to calculate match score.",
    expected_output="A structured score and analysis highlighting matching and missing skills.",
    agent=analysis_agent
)

tailor_resume_task = Task(
    description="""
    Job Description: {jd_text}
    Candidate Master Profile: {candidate_profile}
    
    1. Extract top 5 keywords from JD.
    2. Rewrite the Professional Summary to highlight 18+ years in Software Engineering/Architecture, emphasizing the extracted keywords.
    3. DO NOT invent experience.
    4. Output in Markdown format.
    """,
    expected_output="A highly tailored resume in Markdown.",
    agent=resume_agent
)

apply_task = Task(
    description="Submit the tailored application package securely using Playwright automation.",
    expected_output="Application submission receipt/status confirmation.",
    agent=application_agent
)

network_mapping_task = Task(
    description="""
    Search for 1st or 2nd-degree connections working at {company_name} using LinkedIn tools.
    For each connection found, draft a tailored referral message highlighting my background and asking for an introduction or referral.
    """,
    expected_output="A structured list of connections and drafted referral messages in Markdown format.",
    agent=network_mapping_agent
)

interview_prep_task = Task(
    description="""
    Scrape the recent engineering blogs for {company_name}.
    Identify their tech stacks, recent architectural transitions (e.g. Kafka migrations, scaling PostgreSQL), and system architectures.
    Generate a comprehensive, tailored technical interview preparation guide.
    """,
    expected_output="A comprehensive technical interview preparation sheet in Markdown format.",
    agent=interview_prep_agent
)
