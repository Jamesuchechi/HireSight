"""
Pydantic schemas for request/response validation and serialization.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# Enums
class AccountType(str, Enum):
    personal = "personal"
    company = "company"


class UserRole(str, Enum):
    job_seeker = "job_seeker"
    company = "company"


class RemoteType(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"


class EmploymentType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"


class JobStatus(str, Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


class ApplicationStatus(str, Enum):
    pending = "pending"
    screening = "screening"
    interview = "interview"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"


class ProfileVisibility(str, Enum):
    public = "public"
    verified_companies = "verified_companies"
    private = "private"


class VerificationStatus(str, Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"


class NotificationType(str, Enum):
    application = "application"
    message = "message"
    job = "job"
    follow = "follow"
    interview = "interview"


# Authentication Schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    account_type: AccountType

    @validator("company_name", always=True)
    def require_company_name(cls, value, values):
        if values.get("account_type") == AccountType.company and not value:
            raise ValueError("Company accounts require a company name.")
        return value

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password has at least 1 uppercase, 1 number, 1 special char."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    account_type: AccountType
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: str
    account_type: AccountType
    exp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserOut


class EmailVerificationRequest(BaseModel):
    token: str = Field(..., min_length=1)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator("new_password")
    def validate_password_strength(cls, v):
        """Validate password has at least 1 uppercase, 1 number, 1 special char."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


# Profile Schemas
class PersonalProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    headline: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = None
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    portfolio_links: List[Dict[str, Any]] = Field(default_factory=list)
    preferred_job_types: List[str] = Field(default_factory=list)
    salary_expectation_min: Optional[int] = Field(None, ge=0)
    salary_expectation_max: Optional[int] = Field(None, ge=0)
    salary_currency: str = "USD"
    availability: Optional[str] = None
    profile_visibility: ProfileVisibility = ProfileVisibility.public


class PersonalProfileUpdate(PersonalProfileCreate):
    pass


class PersonalProfileOut(PersonalProfileCreate):
    id: str
    user_id: str
    avatar_url: Optional[str] = None
    resume_primary_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    website: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    mission: Optional[str] = None
    culture: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    team_photos: List[Dict[str, Any]] = Field(default_factory=list)
    founded_year: Optional[int] = Field(None, ge=1800, le=datetime.now().year)


class CompanyProfileUpdate(CompanyProfileCreate):
    pass


class CompanyProfileOut(CompanyProfileCreate):
    id: str
    user_id: str
    logo_url: Optional[str] = None
    verification_status: VerificationStatus
    verification_docs_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    user: UserOut
    profile: PersonalProfileOut | CompanyProfileOut

    model_config = ConfigDict(from_attributes=True)


# Resume Schemas
class ResumeUpload(BaseModel):
    version_name: str = Field(default="Main Resume", max_length=255)


class ResumeOut(BaseModel):
    id: str
    user_id: str
    filename: str
    file_url: str
    file_size: Optional[int] = None
    version_name: str
    is_primary: bool
    parsed_data: Dict[str, Any] = Field(default_factory=dict)
    raw_text: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    resumes: List[ResumeOut]
    total: int


# Job Schemas
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[str] = Field(None, max_length=255)
    remote_type: RemoteType = RemoteType.onsite
    employment_type: EmploymentType = EmploymentType.full_time
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: str = "USD"
    screening_questions: List[Dict[str, Any]] = Field(default_factory=list)
    status: JobStatus = JobStatus.draft


class JobUpdate(JobCreate):
    pass


class JobOut(JobCreate):
    id: str
    company_id: str
    view_count: int
    application_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobSearchResponse(BaseModel):
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    limit: int


class CompanyPublicOut(BaseModel):
    id: str
    company_name: str
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    follower_count: int = 0
    open_jobs_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Application Schemas
class ApplicationCreate(BaseModel):
    job_id: str
    resume_id: str
    cover_letter: Optional[str] = None


class ApplicationOut(BaseModel):
    id: str
    job_id: str
    user_id: str
    resume_id: str
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    match_score: Optional[float] = None
    match_explanation: Dict[str, Any] = Field(default_factory=dict)
    rejection_reason: Optional[str] = None
    applied_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus
    rejection_reason: Optional[str] = None


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationOut]
    total: int
    page: int
    limit: int


# Following Schemas
class FollowCreate(BaseModel):
    following_id: str


class FollowOut(BaseModel):
    id: str
    follower_id: str
    following_id: str
    following_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowerOut(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str] = None
    headline: Optional[str] = None
    followed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Notification Schemas
class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: List[NotificationOut]
    unread_count: int


# Messaging Schemas
class MessageCreate(BaseModel):
    receiver_id: str
    body: str = Field(..., min_length=1, max_length=5000)


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    receiver_id: str
    body: str
    is_read: bool
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    id: str
    other_user: Dict[str, Any]
    last_message: Optional[Dict[str, Any]] = None
    unread_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    conversation_id: str
    messages: List[MessageOut]


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_applications: int = 0
    pending_count: int = 0
    interview_count: int = 0
    offer_count: int = 0
    rejected_count: int = 0
    profile_completion: int = 0
    profile_views: int = 0
    recommended_jobs_count: int = 0
    # Company-specific stats
    active_jobs: Optional[int] = None
    avg_match_score: Optional[float] = None
    time_saved_hours: Optional[int] = None
    new_applications_today: Optional[int] = None
    interviews_scheduled: Optional[int] = None


class DashboardActivity(BaseModel):
    id: str
    type: str
    message: str
    time: str
    link: Optional[str] = None


# Screening Schemas
class ScreeningResult(BaseModel):
    resume_id: str
    name: str
    email: Optional[str] = None
    match_score: float
    explanation: Dict[str, Any]


class CandidateResumeSchema(BaseModel):
    """Basic candidate info for screening results."""
    id: str
    name: str
    email: str
    headline: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class BulkScreeningResponse(BaseModel):
    batch_id: str
    total_files: int
    status: str


class ScreeningResultsResponse(BaseModel):
    job_id: str
    job_title: str
    total_resumes_screened: int
    candidates: List[ScreeningResult]
    screening_date: datetime


# Generic Response Schemas
class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database: str


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
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_date: datetime
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    parsed: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


# Generic Response Schemas
class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database: str
