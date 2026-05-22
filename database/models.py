from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class BlacklistedCompany(Base):
    __tablename__ = "blacklisted_companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    url = Column(Text, unique=True, nullable=False)
    jd_text = Column(Text, nullable=True)
    salary = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('company', 'title', name='unique_job_company'),
    )

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")  # pending, matched, applied, failed
    match_score = Column(Float, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="application", cascade="all, delete-orphan")
    interview_preps = relationship("InterviewPrep", back_populates="application", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    resume_s3_url = Column(Text, nullable=False)

    application = relationship("Application", back_populates="documents")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    error_message = Column(Text, nullable=True)
    screenshot_url = Column(Text, nullable=True)

    job = relationship("Job", back_populates="logs")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    connection_name = Column(String(255), nullable=True)
    connection_degree = Column(String(50), nullable=True)
    referral_draft = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="referrals")


class InterviewPrep(Base):
    __tablename__ = "interview_preps"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    scraped_blog_urls = Column(Text, nullable=True)
    prep_sheet_content = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="interview_preps")

