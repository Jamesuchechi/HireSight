"""
Pydantic schemas for request/response validation and serialization.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class SkillMatchSchema(BaseModel):
    """Details about a single skill match."""
    skill_name: str
    required: bool
    candidate_has: bool
    proficiency: Optional[str] = None
    years_of_experience: Optional[float] = None
    confidence_score: float = Field(..., ge=0, le=1)
    
    class Config:
        from_attributes = True


class CandidateResumeSchema(BaseModel):
    """Basic candidate info from parsed resume."""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experience_summary: Optional[str] = None
    education: Optional[str] = None
    years_of_experience: Optional[float] = None
    
    class Config:
        from_attributes = True


class ResumeUploadSchema(BaseModel):
    """Response after uploading a resume."""
    id: str
    filename: str
    original_filename: str
    file_size: int
    upload_date: datetime
    candidate: Optional[CandidateResumeSchema] = None
    message: str
    
    class Config:
        from_attributes = True


class JobDescriptionCreateSchema(BaseModel):
    """Request to create a new job description."""
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=10)
    requirements: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience_years: Optional[int] = Field(None, ge=0, le=70)
    required_education: Optional[str] = None
    
    @validator("required_skills", pre=True, always=True)
    def validate_skills(cls, v):
        """Normalize skills to lowercase and remove duplicates."""
        if v is None:
            return []
        return [skill.lower().strip() for skill in set(v) if skill.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "description": "Looking for an experienced engineer...",
                "required_skills": ["Python", "PostgreSQL", "AWS"],
                "required_experience_years": 5,
                "required_education": "Bachelor's in CS or related"
            }
        }


class JobDescriptionSchema(JobDescriptionCreateSchema):
    """Job description with database ID."""
    id: str
    created_date: datetime
    updated_date: datetime
    embedding_model: Optional[str] = None
    
    class Config:
        from_attributes = True


class CandidateScoreSchema(BaseModel):
    """Candidate score for a job."""
    overall_score: float = Field(..., ge=0, le=100)
    semantic_similarity_score: Optional[float] = Field(None, ge=0, le=100)
    skill_match_score: Optional[float] = Field(None, ge=0, le=100)
    experience_relevance_score: Optional[float] = Field(None, ge=0, le=100)
    education_fit_score: Optional[float] = Field(None, ge=0, le=100)
    
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    skill_match_percentage: float = Field(..., ge=0, le=100)
    
    explanation: str
    rank: int
    percentile: float = Field(..., ge=0, le=100)
    scored_date: datetime
    flagged_for_review: bool = False
    
    class Config:
        from_attributes = True


class RankedCandidateSchema(BaseModel):
    """Candidate with resume info and score."""
    rank: int
    candidate: CandidateResumeSchema
    score: CandidateScoreSchema
    resume_id: str
    job_id: str
    
    class Config:
        from_attributes = True


class ScreeningResultsSchema(BaseModel):
    """Results from screening all resumes against a job."""
    job_id: str
    job_title: str
    total_resumes_screened: int
    top_candidates: List[RankedCandidateSchema]
    screening_date: datetime
    summary_stats: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-123",
                "job_title": "Senior Engineer",
                "total_resumes_screened": 50,
                "top_candidates": [],
                "screening_date": "2026-01-06T12:00:00",
                "summary_stats": {
                    "avg_score": 45.3,
                    "min_score": 10.2,
                    "max_score": 95.7,
                    "median_score": 42.1
                }
            }
        }


class HealthCheckSchema(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    database: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2026-01-06T12:00:00",
                "database": "connected"
            }
        }


class ErrorSchema(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "File size exceeds maximum allowed",
                "timestamp": "2026-01-06T12:00:00"
            }
        }


class ResumeCreate(BaseModel):
    """Legacy DTO used when uploading resumes."""
    filename: str


class ResumeOut(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    parsed: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    """DTO for creating a job."""
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=10)
    requirements: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience_years: Optional[int] = Field(None, ge=0, le=70)
    required_education: Optional[str] = None

    @validator("required_skills", pre=True, always=True)
    def normalize_skills(cls, v):
        if v is None:
            return []
        return [skill.lower().strip() for skill in set(v) if skill.strip()]


class JobOut(BaseModel):
    id: str
    title: str
    company: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience_years: Optional[int] = None
    required_education: Optional[str] = None
    embedding_model: Optional[str] = None
    created_date: datetime
    updated_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateScoreOut(BaseModel):
    resume_id: str
    job_id: str
    score: float
    explanation: Optional[str]

    model_config = ConfigDict(from_attributes=True)
