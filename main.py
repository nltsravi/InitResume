from crewai import Crew, Process
from recruitment_crew import job_search_agent, analysis_agent, resume_agent, application_agent
from document_tasks import search_task, score_task, tailor_resume_task, apply_task

recruitment_crew = Crew(
    agents=[job_search_agent, analysis_agent, resume_agent, application_agent],
    tasks=[search_task, score_task, tailor_resume_task, apply_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    # Kicks off the daily run
    result = recruitment_crew.kickoff()
    print("Daily Application Run Complete.", result)
