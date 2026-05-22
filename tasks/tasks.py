from crewai import Task
from textwrap import dedent

class ApplicationTasks:
    def search_jobs_task(self, agent, keywords: str, location: str) -> Task:
        return Task(
            description=dedent(f"""\
                Search for job postings matching the query '{keywords}' in '{location}'.
                Scrape at least 2 relevant job details, extracting:
                1. Job Title
                2. Company Name
                3. Application URL
                4. Job Description & Requirements"""),
            expected_output="A list of structured job posting information in JSON format.",
            agent=agent
        )

    def customize_resume_task(self, agent, resume_path: str, search_task: Task) -> Task:
        return Task(
            description=dedent(f"""\
                Read the user's original resume at '{resume_path}'.
                For each job discovered in the search task, analyze the job requirements.
                Customize the resume (profile statement, skill hierarchy, key project bullet points) 
                to align perfectly with the target job's keywords and tech stack, while maintaining truthfulness.
                Format the optimized resume profile and description for application forms."""),
            expected_output="Tailored profile descriptions, customized achievements, and form inputs for each targeted job.",
            agent=agent,
            context=[search_task]
        )

    def apply_to_jobs_task(self, agent, customize_task: Task) -> Task:
        return Task(
            description=dedent("""\
                Using the tailored resume data and application details from the customization task,
                navigate to each job's application URL. 
                Fill out the application forms (name, email, github, linkedin, custom cover letter details),
                upload the customized resume, and execute the form submission."""),
            expected_output="A execution summary log listing URLs applied to and submission status/receipts.",
            agent=agent,
            context=[customize_task]
        )
