-- PostgreSQL Schema for Application Tracking System (ATS)
-- Database Name: job_search

-- Blacklisted Companies: Organizations blocked from applications
CREATE TABLE IF NOT EXISTS blacklisted_companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) UNIQUE NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs Table: Tracks scraped opportunities with anti-spam unique constraint
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    jd_text TEXT,
    salary VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_job_company UNIQUE (company, title)
);

-- Applications Table: Core pipeline tracker
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending', -- e.g. pending, matched, applied, failed
    match_score FLOAT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents Table: Versioned resumes used per application
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
    resume_s3_url TEXT NOT NULL
);

-- Logs Table: Playwright failure tracking
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    error_message TEXT,
    screenshot_url TEXT
);

-- Referrals Table: Track networking opportunities and connection referral drafts
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
    connection_name VARCHAR(255),
    connection_degree VARCHAR(50),
    referral_draft TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview Preps Table: Track blog URL links and generated prep sheets
CREATE TABLE IF NOT EXISTS interview_preps (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
    scraped_blog_urls TEXT,
    prep_sheet_content TEXT,
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

