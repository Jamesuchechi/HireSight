"""
SQLAlchemy ORM models for database tables.
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Resume(Base):
    """Model for uploaded resume files."""
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String, nullable=False)  # pdf, docx
    
    # Parsed candidate info
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    location = Column(String)
    
    # Raw extracted text for debugging
    raw_text = Column(Text)
    
    # Structured data
    parsed_data = Column(JSON)  # Full extracted data as JSON
    
    # Embedding vector
    embedding = Column(JSON)  # Stored as JSON array of floats for compatibility
    embedding_model = Column(String)  # Name of model used for embedding
    
    # Metadata
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Integer, default=0)  # 0 = not processed, 1 = parsed, 2 = embedded
    
    # Relations
    candidates = relationship("Candidate", back_populates="resume", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename}, name={self.name})>"


class JobDescription(Base):
    """Model for job descriptions to match against."""
    __tablename__ = "job_descriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    company = Column(String, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    
    # Extracted key info
    required_skills = Column(JSON)  # Stored as JSON array of skill names
    required_experience_years = Column(Integer)
    required_education = Column(String)
    
    # Embedding vector
    embedding = Column(JSON)  # Stored as JSON array of floats
    embedding_model = Column(String)
    
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    scores = relationship("CandidateScore", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, title={self.title})>"


class Candidate(Base):
    """Model for parsed candidate information."""
    __tablename__ = "candidates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String, nullable=False, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    location = Column(String)
    
    # Extracted from resume
    skills = Column(JSON)  # Stored as JSON array of skill names
    experience_summary = Column(Text)
    education = Column(Text)
    years_of_experience = Column(Float)
    
    # Normalized/standardized data
    normalized_skills = Column(JSON)  # Stored as JSON array of normalized skills
    
    # Relations
    resume = relationship("Resume", back_populates="candidates")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.name}, email={self.email})>"


class UserRole(PyEnum):
    job_seeker = "job_seeker"
    company = "company"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole, name="user_roles"), nullable=False, default=UserRole.job_seeker)
    company_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class CandidateScore(Base):
    """Model for candidate-job matching scores."""
    __tablename__ = "candidate_scores"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("job_descriptions.id"), nullable=False, index=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False, index=True)
    
    # Overall score (0-100)
    overall_score = Column(Float, nullable=False, index=True)
    
    # Component scores (0-100 each)
    semantic_similarity_score = Column(Float)  # Based on embedding cosine similarity
    skill_match_score = Column(Float)  # % of required skills present
    experience_relevance_score = Column(Float)  # Based on years and roles
    education_fit_score = Column(Float)  # Based on degree requirements
    
    # Matching details
    matched_skills = Column(JSON)  # Stored as JSON array of skills that matched
    missing_skills = Column(JSON)  # Stored as JSON array of required skills not found
    skill_match_percentage = Column(Float)  # % of required skills candidate has
    
    # Explanation for ranking
    explanation = Column(Text)  # Human-readable reason for score
    reasoning = Column(JSON)  # Detailed scoring breakdown
    
    # Ranking
    rank = Column(Integer, index=True)  # Rank among all candidates for this job
    percentile = Column(Float)  # Percentile score (0-100)
    
    # Metadata
    scored_date = Column(DateTime, default=datetime.utcnow, index=True)
    flagged_for_review = Column(Integer, default=0)  # 1 = needs human review
    
    # Relations
    resume = relationship("Resume", back_populates="scores")
    job = relationship("JobDescription", back_populates="scores")
    candidate = relationship("Candidate", back_populates="scores")
    
    def __repr__(self):
        return f"<CandidateScore(resume={self.resume_id}, job={self.job_id}, score={self.overall_score})>"


class SkillMatch(Base):
    """Model for detailed skill-level matching between candidates and job requirements."""
    __tablename__ = "skill_matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    score_id = Column(String, ForeignKey("candidate_scores.id"), nullable=False)
    
    skill_name = Column(String, nullable=False, index=True)
    required = Column(Integer, default=1)  # 1 if required, 0 if nice-to-have
    candidate_has = Column(Integer, default=0)  # 1 if candidate has skill, 0 otherwise
    candidate_proficiency = Column(String)  # junior, intermediate, senior, expert
    years_of_experience = Column(Float)  # How long candidate has used this skill
    
    # Matching confidence
    confidence_score = Column(Float)  # 0-1 confidence in the match
    
    def __repr__(self):
        return f"<SkillMatch(skill={self.skill_name}, has={self.candidate_has})>"
