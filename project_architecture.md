# CrewAI Auto-Apply Core: Technical Architecture & Usage Guide

This document provides a comprehensive breakdown of the **CrewAI Auto-Apply Core (ATS & Pipeline Automation)** project, including its system architecture, step-by-step sequential flows, and instructions on how to use the system as an end user.

---

## 1. Technical Architecture Diagram

The system follows a microservices-based design with an agentic orchestrator (CrewAI), an asynchronous processing layer (Celery/Redis), vector search (Chroma DB), and monitoring instrumentation (Prometheus/Grafana).

```mermaid
graph TD
    %% Frontend Layer
    subgraph Frontend [Presentation Layer]
        UI[Next.js Dashboard / Port 3000]
    end

    %% API and Orchestration Layer
    subgraph API_Services [Application Layer]
        API[FastAPI Backend / Port 8000]
        CrewAI[CrewAI Agent Framework]
        Celery[Celery Task Worker]
        Redis[Redis Task Broker / Port 6379]
    end

    %% Data and Knowledge Layer
    subgraph Data_Storage [Data & Knowledge Layer]
        DB[(PostgreSQL / Port 5432)]
        Chroma[(Chroma DB Vector Store)]
    end

    %% Telemetry Layer
    subgraph Telemetry [Observability Layer]
        Prom[Prometheus Server / Port 9090]
        Grafana[Grafana Dashboard / Port 3001]
    end

    %% External Interfaces
    subgraph External [External Services]
        OpenAI[OpenAI API GPT-4o / GPT-4o-mini]
        LinkedIn[LinkedIn Scraper Mock]
        CompanyBlog[Company Tech Blogs]
        JobBoards[Lever & Greenhouse Portals]
        Gmail[Gmail API Webhook]
    end

    %% Interactions
    UI <-->|REST APIs / JSON| API
    API -->|Enqueue Jobs| Redis
    Redis -->|Process Tasks| Celery
    Celery -->|Execute Crews| CrewAI
    API -.->|Alternative Run| CrewAI

    CrewAI <-->|Retrieve Relevant Experience| Chroma
    CrewAI <-->|LLM Queries| OpenAI
    CrewAI <-->|Scrape JDs & Apply| JobBoards
    CrewAI <-->|Fetch Connections| LinkedIn
    CrewAI <-->|Scrape Tech Blogs| CompanyBlog

    API <-->|Read / Write Apps & Logs| DB
    API -.->|Expose Metrics /metrics| Prom
    Prom -->|Read Metrics| Grafana
    Gmail -->|Push Rejection Webhooks| API
```

### Components Description

*   **Next.js Dashboard**: A responsive, Tailwind CSS-powered UI that acts as the user control center. It represents the application pipeline as a visual Kanban board.
*   **FastAPI Backend**: The gateway API handling HTTP requests, webhooks (e.g., Gmail rejections), background task scheduling, and serving data to the UI.
*   **Celery & Redis**: An asynchronous queueing system to run resource-heavy browser automation processes and multi-agent runs without blocking the API threads.
*   **CrewAI Framework**: Coordinates specialised AI agents to perform complex, sequential workflows:
    *   **Principal Job Sourcing Specialist**: Discovers job descriptions.
    *   **Technical ATS Scorer**: Ranks jobs based on semantic fit and candidate experience.
    *   **Executive Resume Tailor**: Customizes specific parts of the resume.
    *   **Playwright Automation Specialist**: Emulates human behavior (delays, mouse movements, stealth headers) to submit forms.
    *   **Network Mapping Specialist**: Identifies referrals via LinkedIn.
    *   **Interview Prep Specialist**: Researches technical blog postings to draft study guides.
*   **PostgreSQL**: Relational database storing structured details about jobs, application statuses, logs, referral drafts, and interview preps.
*   **Chroma DB**: A vector store holding chunked embeddings of the candidate's master resume for context retrieval during resume tailoring and question resolution.
*   **Prometheus & Grafana**: Collects and visualizes live telemetry (LLM token consumption rates, success/failure metrics, and automation crash reasons).

---

## 2. Sequential Workflow Diagram

Below is the execution flow from the moment an application is triggered down to the automatic application submission and potential learning updates.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Next.js Dashboard
    participant API as FastAPI Backend
    participant Crew as CrewAI Agent Orchestrator
    participant RAG as Chroma DB (Vector Store)
    participant LLM as OpenAI (GPT-4o/4o-mini)
    participant Browser as Playwright Stealth Browser
    participant Gmail as Gmail Webhook Service

    User->>UI: Input Job URL & Click Launch
    UI->>API: POST /api/v1/trigger-apply {url}
    API->>Crew: Kickoff recruitment_crew with job_url

    Note over Crew: Phase 1: Job Scraping & Sourcing
    Crew->>Browser: Scrape Job URL
    Browser-->>Crew: Job Description & Metadata

    Note over Crew: Phase 2: Match & Score (Cost Optimised: GPT-4o-mini)
    Crew->>LLM: Compare Job details vs Profile
    LLM-->>Crew: ATS Match Score & Missing Skills (w_tech, w_exp, w_domain, w_role)

    alt Match Score <= 75% (Rejected)
        Crew-->>API: Stop & Mark Job as "Rejected" (Low Score)
        API-->>UI: Update Kanban column to "Rejected"
    else Match Score > 75% (Matched)
        Note over Crew: Phase 3: Resume Tailoring (High Reasoning: GPT-4o)
        Crew->>RAG: Retrieve candidate experience matching JD keywords
        RAG-->>Crew: Semantic experience chunks
        Crew->>LLM: Customize Professional Summary & Project order
        LLM-->>Crew: Tailored Resume (Markdown)

        Note over Crew: Phase 4: Stealth Submission
        Crew->>Browser: Load Application Form (Lever/Greenhouse)
        
        alt Form contains custom screening questions (e.g. compensation expectations)
            Browser-->>Crew: Custom question detected
            Crew-->>API: Pause Application & Set Status to "Pending Approval"
            API-->>UI: Display Alert "Resolve Custom Question"
            User->>UI: Input Answer text
            UI->>API: POST /api/v1/applications/{id}/submit-answer
            API-->>Crew: Resume execution with custom answers
        end

        Crew->>Browser: Type data (realistic human delays), Upload Resume, Click Submit
        Browser-->>Crew: Confirmation of Submission
        Crew-->>API: Save Application & Mark Status as "Applied"
        API-->>UI: Update Kanban column to "Applied"
    end

    Note over Crew: Telemetry updates
    API->>API: Increment Prometheus Counters (tokens, success_rates, playwright_crashes)

    Note over Gmail, API: Asynchronous Feedback Loop
    Gmail->>API: POST /api/v1/gmail-webhook (Rejection email received)
    API->>API: Call LearningAgent.process_rejection()
    API->>API: Recalculate weights.json (reduce w_tech, increase w_domain/role relevance)
    API-->>UI: Reflected in future matching scores
```

---

## 3. End-User Guide (How to Use)

### A. Setting Up Your Profile
1.  **Configure Environment**: Set your API credentials in your `.env` file (e.g., `OPENAI_API_KEY`, mock/real `LINKEDIN_COOKIES`).
2.  **Upload Master Resume**: Place your master resume in the root directory (named `resume.pdf`). The system uses `core/rag.py` to ingest and split this resume, storing the embeddings in `./chroma_db`.

### B. Accessing the Services
Ensure Docker Compose is running (`docker-compose up --build`).
*   **Web Dashboard**: Open [http://localhost:3000](http://localhost:3000)
*   **API Docs (Swagger)**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Telemetry Dashboards**: Open Grafana at [http://localhost:3001](http://localhost:3001) (User: `admin` / Password: `admin`) to monitor token costs and Playwright crashes.

### C. Triggering an Auto-Apply Run
1.  Navigate to the **Web Dashboard** (`localhost:3000`).
2.  Locate the top bar section labeled **"Trigger Autonomous Apply Flow"**.
3.  Paste a target job application URL (e.g., Greenhouse or Lever job post) into the input field.
4.  Click **Launch**.
5.  The system starts the pipeline:
    *   It scrapes the JD, evaluates the match score, and places the job in the **Found** column.
    *   As the score is determined, it moves to the **Scored** column.
    *   If matched, the resume tailor runs, moving the job to **Tailoring**.

### D. Resolving Pending Approvals (Manual Intervention)
If the application form features custom text questions that AI cannot answer confidently without authorization (such as salary expectations or authorization status):
1.  The card will move to the **Pending Approval** column.
2.  The card will display a warning: **"Resolve Custom Question"**.
3.  Click this button to open the modal.
4.  Review the question asked by the application form and type your custom answer.
5.  Click **Resume & Apply**. The Playwright browser agent resumes automatically, fills the answer into the page, and completes the submission.

### E. Getting Referrals and Interview Prep Sheets
Once a job is in the **Applied** status, you can trigger post-application workflows:
1.  **Generate Networking Referrals**:
    *   Click on the application card in the dashboard or trigger the POST endpoint `/api/v1/applications/{app_id}/referrals`.
    *   The **Network Mapping Agent** queries your LinkedIn connections to draft personalized outreach messages in Markdown format.
2.  **Generate Interview Prep Guides**:
    *   Schedule an interview by clicking the interview scheduling prompt or hitting POST `/api/v1/applications/{app_id}/schedule-interview` with an interview date and time.
    *   The **Interview Prep Specialist** scrapes the target company's engineering blogs.
    *   It extracts architectural highlights (e.g. migration stories, technical stacks) and outputs a comprehensive preparation document.
