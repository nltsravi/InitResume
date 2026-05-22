# CrewAI Auto-Apply Core (ATS & Pipeline Automation)

An autonomous, agent-driven job application tracking system (ATS) and pipeline automation platform. It discovers job openings, scores them based on custom fit algorithms, tailors resumes to target roles, automates application submissions securely, and drives networking referrals and system design preparation guides.

---

## 🚀 Key Features

*   **Job Search & Scoring Engine**: Automatically identifies opportunities and ranks them using a weighted match score algorithm (evaluating skill semantic similarity, 18+ years experience target, industry domain relevance, and role fit).
*   **Resume Customizer**: Employs deep-reasoning LLMs (`gpt-4o`) to customize professional summaries, skills lists, and project rankings for targeted keywords, ensuring zero hallucinations.
*   **Stealth Auto-Applier**: A Playwright-based form submission tool with user-agent rotation, viewport randomization, realistic typing/mouse-movement delays, and stealth masking to bypass bot detection on Greenhouse and Lever.
*   **Enterprise Bonus Agents**:
    *   **Network Mapping Specialist**: Queries LinkedIn connections to locate 1st/2nd-degree contacts at target companies and drafts custom referral requests.
    *   **Interview Prep Specialist**: Scrapes recent company engineering blogs to extract system architecture, tech stacks, and recent migrations (e.g., Kafka migrations, pg_bouncer scaling) to build tailored technical guides.
*   **Learning Feedback Loop**: Webhook integration to parse rejection emails and feed data back into the search and scoring algorithm to dynamically adjust weights.
*   **Prometheus & Grafana Monitoring**: Out-of-the-box telemetry tracking LLM token rates (segmented by prompt/completion), submission success rates, and automation crash reasons (e.g. DOM changes, timeouts).
*   **Cost Optimization**: Dual-tier LLM routing using `gpt-4o-mini` for search/scoring/networking, reserving `gpt-4o` only for high-reasoning resume tailoring and interview prep sheets, and using `text-embedding-3-small` embeddings.

---

## 🛠️ Architecture

*   **Backend Core API**: FastAPI (Python)
*   **Task Queue & Broker**: Celery & Redis
*   **Database**: PostgreSQL & SQLAlchemy ORM
*   **Orchestration Framework**: CrewAI & LangChain
*   **Telemetry**: Prometheus Client & Grafana Provisioning
*   **UI Dashboard**: Next.js & Tailwind CSS

---

## 💻 Instructions to Execute

### Prerequisites
*   Docker & Docker Compose installed.
*   OpenAI API Key.

### 1. Configuration (`.env`)
Create a `.env` file in the root directory based on `.env.example`:
```env
# Credentials Vault
OPENAI_API_KEY=sk-proj-your-openai-api-key
LINKEDIN_COOKIES='[{"name": "li_at", "value": "your_cookie_here", "domain": ".linkedin.com"}]'

# Database Configuration
DB_USER=postgres
DB_PASSWORD=admin
DB_NAME=job_search
DB_PORT=5432
REDIS_PORT=6379
```

### 2. Run with Docker Compose (Recommended)
Build and spin up the complete system (API Server, Celery Worker, PostgreSQL Database, Redis Broker, Prometheus, Grafana, and Frontend UI Dashboard):
```bash
docker-compose up --build
```

### 3. Run Locally (Development Mode)
If you prefer running individual services locally for development:

**A. Start Backend API Server:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**B. Start Celery Worker:**
```bash
celery -A core.tasks worker --loglevel=info
```

**C. Run the Frontend Dashboard:**
```bash
cd ui
npm install
npm run dev
```

---

## 🌐 Access URLs

| Service / Portal | URL | Credentials (if applicable) |
| :--- | :--- | :--- |
| **Frontend UI Dashboard** | [http://localhost:3000](http://localhost:3000) | None |
| **FastAPI Backend Server** | [http://localhost:8000](http://localhost:8000) | None |
| **Interactive API Documentation (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | None |
| **Prometheus Metrics Endpoint** | [http://localhost:8000/metrics](http://localhost:8000/metrics) | None |
| **Prometheus Web UI** | [http://localhost:9090](http://localhost:9090) | None |
| **Grafana Dashboard Viewer** | [http://localhost:3001](http://localhost:3001) | User: `admin`<br>Pass: `admin` |

---

## 🧪 Verification & Testing

The application includes two test suites inside the `/scratch` directory:
- **Telemetry Verification**: `test_telemetry.py` ensures Prometheus metrics are correctly exported and agents use optimized LLM tiers.
- **Enterprise Features Verification**: `test_enterprise.py` validates the database schema, models, custom agents, mock tools, and new REST endpoints for referral/interview preps using SQLite.

Run the tests locally:
```bash
# Run Telemetry tests
PYTHONPATH=. python3 /Users/ravij/.gemini/antigravity/scratch/test_telemetry.py

# Run Enterprise Agent tests
PYTHONPATH=. python3 /Users/ravij/.gemini/antigravity/scratch/test_enterprise.py
```
