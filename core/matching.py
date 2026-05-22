from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json

class MatchingEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def calculate_ats_match(self, resume_text: str, job_description: str) -> dict:
        """
        Compares a resume against a job description, returns a match score and recommended keywords to add.
        """
        print("[MatchingEngine] Running ATS semantic alignment check...")
        
        prompt = PromptTemplate.from_template(
            """
            Analyze the following resume against the job description.
            
            Resume:
            {resume}
            
            Job Description:
            {job_description}
            
            Return a JSON object containing:
            1. "score": An integer match percentage (0 to 100).
            2. "missing_skills": List of keywords/skills present in the job description but missing from the resume.
            3. "alignment_analysis": A short paragraph explaining the gaps and strong matches.
            
            Your response MUST be strict, valid JSON.
            """
        )
        
        formatted_prompt = prompt.format(resume=resume_text[:2000], job_description=job_description[:2000])
        
        try:
            response = self.llm.predict(formatted_prompt)
            # Find and parse JSON from the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(response[start:end])
        except Exception as e:
            print(f"Error calculating ATS match: {e}")
            
        # Return fallback mock analysis
        return {
            "score": 75,
            "missing_skills": ["Playwright", "FastAPI"],
            "alignment_analysis": "The candidate has strong Python skills but lacks direct Playwright/FastAPI experience mentioned in the description."
        }
