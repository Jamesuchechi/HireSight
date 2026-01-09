from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from . import crud, models
from .config import settings
from .database import get_db
from .schemas import *
from .utils.security import (
    get_current_user, get_current_verified_user,
    get_current_personal_user, get_current_company_user
)
from .utils.parser import parse_resume
from .utils.ratelimit import registration_rate_limiter

router = APIRouter()

def _format_company_location(profile: models.CompanyProfile) -> Optional[str]:
    if profile.locations:
        primary = profile.locations[0]
        parts = [primary.get("city"), primary.get("state")]
        return ", ".join([part for part in parts if part])
    return None


def _build_company_public(profile: models.CompanyProfile, db: Session) -> CompanyPublicOut:
    location = _format_company_location(profile)
    follower_count = crud.get_company_followers_count(db, profile.user_id)
    open_jobs = crud.get_company_open_jobs_count(db, profile.user_id)
    return CompanyPublicOut(
        id=profile.user_id,
        company_name=profile.company_name,
        logo_url=profile.logo_url,
        industry=profile.industry,
        company_size=profile.company_size,
        location=location,
        follower_count=follower_count,
        open_jobs_count=open_jobs
    )

logger = logging.getLogger(__name__)


def _estimate_profile_completion(profile: Optional[models.PersonalProfile]) -> int:
    if not profile:
        return 20
    fields = [
        profile.full_name,
        profile.headline,
        profile.location,
        profile.bio,
        profile.skills,
        profile.experience
    ]
    filled = sum(bool(value) for value in fields)
    return min(100, int((filled / len(fields)) * 100))


def _get_company_name_from_user(user: models.User) -> str:
    profile = user.company_profile
    if profile and profile.company_name:
        return profile.company_name
    return user.company_name or user.email


def _build_interview_payload(app: models.Application, for_company: bool = False) -> InterviewOut:
    job = app.job
    company = job.company if job else None
    scheduled_at = (app.applied_at or datetime.utcnow()) + timedelta(days=1)
    candidate_name = None
    if for_company and app.user:
        candidate_name = app.user.full_name or app.user.email

    return InterviewOut(
        id=str(app.id),
        job_title=job.title if job else None,
        candidate_name=candidate_name,
        company_name=_get_company_name_from_user(company) if company else None,
        scheduled_at=scheduled_at,
        duration_minutes=45,
        location=job.location if job else None,
        meeting_link=None,
        status=app.status
    )


# Profile Routes
@router.get("/users/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get current user's profile."""
    if current_user.account_type == "personal":
        profile = crud.get_personal_profile(db, current_user.id)
    else:
        profile = crud.get_company_profile(db, current_user.id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return UserProfileResponse(user=current_user, profile=profile)


@router.put("/users/me/profile")
def update_my_profile(
    profile_data: PersonalProfileUpdate | CompanyProfileUpdate,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    if current_user.account_type == "personal":
        if not isinstance(profile_data, PersonalProfileUpdate):
            raise HTTPException(status_code=400, detail="Invalid profile data for personal account")
        profile = crud.update_personal_profile(db, current_user.id, profile_data)
    else:
        if not isinstance(profile_data, CompanyProfileUpdate):
            raise HTTPException(status_code=400, detail="Invalid profile data for company account")
        profile = crud.update_company_profile(db, current_user.id, profile_data)

    return {"message": "Profile updated successfully", "profile": profile}


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get public profile of another user."""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check visibility permissions
    if user.account_type == "personal":
        profile = crud.get_personal_profile(db, user_id)
        if profile and profile.profile_visibility == "private":
            if current_user.id != user_id:
                raise HTTPException(status_code=403, detail="Profile is private")
        elif profile and profile.profile_visibility == "verified_companies":
            if current_user.account_type != "company":
                raise HTTPException(status_code=403, detail="Profile visible to verified companies only")
    else:
        profile = crud.get_company_profile(db, user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return UserProfileResponse(user=user, profile=profile)


@router.get("/companies", response_model=List[CompanyPublicOut])
def list_companies(
    industry: Optional[str] = None,
    size: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List verified companies."""
    skip = (page - 1) * limit
    companies = crud.get_verified_companies(db, industry, size, skip, limit)
    return [_build_company_public(profile, db) for profile in companies]


@router.get("/companies/{company_id}", response_model=CompanyPublicOut)
def get_company(
    company_id: str,
    db: Session = Depends(get_db)
):
    """Get public data for a specific verified company."""
    profile = crud.get_verified_company_by_id(db, company_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company not found")
    return _build_company_public(profile, db)


# Resume Routes
@router.post("/resumes/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    version_name: str = "Main Resume",
    current_user: models.User = Depends(get_current_personal_user),
    db: Session = Depends(get_db)
):
    """Upload and parse a resume."""
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Use PDF or DOCX only."
        )

    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400, detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes."
        )

    # Save file
    upload_dir = settings.UPLOADS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    target_filename = f"{uuid4().hex}_{file.filename}"
    file_path = upload_dir / target_filename

    with open(file_path, "wb") as destination:
        destination.write(file_content)

    parsed_data: Dict[str, Any] = {}
    raw_text: Optional[str] = None
    try:
        parsed_result = parse_resume(str(file_path))
        parsed_data = parsed_result
        raw_text = parsed_result.get("raw_text")
    except Exception as exc:
        logger.error("Failed to parse resume %s: %s", file.filename, exc)

    resume = crud.create_resume(
        db,
        user_id=current_user.id,
        filename=target_filename,
        file_url=str(file_path),
        file_size=file_size,
        version_name=version_name,
        parsed_data=parsed_data,
        raw_text=raw_text
    )

    return resume


@router.get("/resumes", response_model=ResumeListResponse)
def list_resumes(current_user: models.User = Depends(get_current_personal_user), db: Session = Depends(get_db)):
    """List user's resumes."""
    resumes = crud.get_user_resumes(db, current_user.id)
    return ResumeListResponse(resumes=resumes, total=len(resumes))


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, current_user: models.User = Depends(get_current_personal_user), db: Session = Depends(get_db)):
    """Get a specific resume."""
    resume = crud.get_resume_by_id(db, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    return resume


@router.put("/resumes/{resume_id}")
def update_resume(
    resume_id: str,
    version_name: str,
    current_user: models.User = Depends(get_current_personal_user),
    db: Session = Depends(get_db)
):
    """Update resume metadata."""
    resume = crud.get_resume_by_id(db, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume.version_name = version_name
    db.commit()

    return {"message": "Resume updated successfully"}


@router.post("/resumes/{resume_id}/set-primary")
def set_primary_resume(resume_id: str, current_user: models.User = Depends(get_current_personal_user), db: Session = Depends(get_db)):
    """Set a resume as primary."""
    success = crud.set_primary_resume(db, current_user.id, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Primary resume updated successfully"}


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: str, current_user: models.User = Depends(get_current_personal_user), db: Session = Depends(get_db)):
    """Delete a resume."""
    success = crud.delete_resume(db, current_user.id, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Resume deleted successfully"}


@router.post("/resumes/{resume_id}/parse", response_model=ResumeOut)
def reparse_resume(resume_id: str, current_user: models.User = Depends(get_current_personal_user), db: Session = Depends(get_db)):
    """Re-parse an existing resume."""
    resume = crud.get_resume_by_id(db, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        parsed_result = parse_resume(resume.file_url)
    except Exception as exc:
        logger.error("Failed to re-parse resume %s: %s", resume_id, exc)
        raise HTTPException(status_code=500, detail="Failed to parse resume")

    resume.parsed_data = parsed_result
    resume.raw_text = parsed_result.get("raw_text")
    db.commit()
    db.refresh(resume)

    return resume


# Job Routes (Company)
@router.post("/jobs", response_model=JobOut)
def create_job(job_data: JobCreate, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Create a new job posting."""
    job = crud.create_job(db, current_user.id, job_data)
    return job


@router.get("/jobs", response_model=List[JobOut])
def list_my_jobs(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """List company's job postings."""
    skip = (page - 1) * limit
    jobs = crud.get_company_jobs(db, current_user.id, status, skip, limit)
    return jobs


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Get a specific job posting."""
    job = crud.get_job_by_id(db, job_id)
    if not job or job.company_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.put("/jobs/{job_id}", response_model=JobOut)
def update_job(
    job_id: str,
    job_data: JobUpdate,
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Update a job posting."""
    job = crud.update_job(db, job_id, current_user.id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Delete a job posting (soft delete)."""
    success = crud.delete_job(db, job_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job deleted successfully"}


@router.post("/jobs/{job_id}/close")
def close_job(job_id: str, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Close a job to new applications."""
    job = crud.close_job(db, job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or already closed")
    return {"message": "Job closed successfully", "job": job}


@router.post("/jobs/{job_id}/duplicate", response_model=JobOut)
def duplicate_job(job_id: str, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Duplicate an existing job posting."""
    duplicate = crud.duplicate_job(db, job_id, current_user.id)
    if not duplicate:
        raise HTTPException(status_code=404, detail="Job not found")
    return duplicate


@router.get("/jobs/{job_id}/similar", response_model=List[JobOut])
def similar_jobs(job_id: str, limit: int = 3, db: Session = Depends(get_db)):
    """Get similar active jobs based on shared skills."""
    similar = crud.get_similar_jobs(db, job_id, limit)
    return similar


@router.get("/jobs/saved", response_model=SavedJobListResponse)
def list_saved_jobs(
    limit: int = 12,
    current_user: models.User = Depends(get_current_personal_user),
    db: Session = Depends(get_db)
):
    """List jobs the personal user has saved."""
    entries = crud.get_saved_jobs(db, current_user.id, limit=limit)
    payload = []
    for entry in entries:
        job = entry.job
        if not job:
            continue
        company = job.company or current_user
        company_name = _get_company_name_from_user(company) if company else None
        company_logo = (
            company.company_profile.logo_url if company and company.company_profile else None
        )
        payload.append(
            SavedJobOut(
                id=entry.id,
                job_id=job.id,
                title=job.title,
                company_name=company_name,
                company_logo=company_logo,
                location=job.location,
                remote_type=job.remote_type,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                saved_at=entry.saved_at,
                status=job.status
            )
        )
    return SavedJobListResponse(saved_jobs=payload)


@router.get("/jobs/recommended", response_model=RecommendedJobListResponse)
def list_recommended_jobs(
    limit: int = 5,
    current_user: models.User = Depends(get_current_personal_user),
    db: Session = Depends(get_db)
):
    """Fetch recommended jobs for a personal user."""
    entries = crud.get_recommended_jobs(db, current_user.id, limit=limit)
    payload = []
    for entry in entries:
        job = entry["job"]
        company = job.company
        payload.append(
            RecommendedJobOut(
                id=job.id,
                title=job.title,
                company_name=_get_company_name_from_user(company) if company else None,
                company_logo=company.company_profile.logo_url if company and company.company_profile else None,
                location=job.location,
                match_score=entry.get("match_score"),
                skills_match=entry.get("skills_match", []),
                posted_date=job.created_at or datetime.utcnow()
            )
        )
    return RecommendedJobListResponse(recommended_jobs=payload)


@router.get("/interviews", response_model=InterviewListResponse)
def list_interviews(
    limit: int = 6,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Return scheduled interviews for both roles."""
    interviews = []
    if current_user.account_type == "personal":
        applications = crud.get_user_applications(db, current_user.id, limit=limit)
        for app in applications:
            if app.status == "interview":
                interviews.append(_build_interview_payload(app, for_company=False))
    else:
        applications = crud.get_company_applications(db, current_user.id, limit=limit)
        for app in applications:
            if app.status == "interview":
                interviews.append(_build_interview_payload(app, for_company=True))
    return InterviewListResponse(interviews=interviews)


@router.get("/candidates", response_model=CandidateListResponse)
def list_candidates(
    limit: int = 10,
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """List candidates for company jobs."""
    applications = crud.get_company_applications(db, current_user.id, limit=limit * 3)
    seen = set()
    candidates = []
    for app in applications:
        if not app.user or app.user.id in seen:
            continue
        seen.add(app.user.id)
        profile = app.user.personal_profile
        skills = _flatten_skill_entries(profile.skills) if profile else []
        candidates.append(
            CandidateOut(
                id=app.user.id,
                name=profile.full_name if profile and profile.full_name else app.user.email,
                role=profile.headline if profile else None,
                score=float(app.match_score or 0),
                skills=skills[:5],
                avatar=profile.avatar_url if profile else None,
                status=app.status,
                applied_at=app.applied_at
            )
        )
        if len(candidates) >= limit:
            break
    return CandidateListResponse(candidates=candidates)


# Job Routes (Public/Personal)
@router.get("/jobs/search", response_model=JobSearchResponse)
def search_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    remote_type: Optional[str] = None,
    employment_type: Optional[str] = None,
    salary_min: Optional[int] = None,
    skills: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search for jobs."""
    skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()] if skills else None
    result = crud.search_jobs(
        db, q, location, remote_type, employment_type,
        salary_min, skills_list, (page-1)*limit, limit
    )
    return JobSearchResponse(
        jobs=result["jobs"],
        total=result["total"],
        page=page,
        limit=limit
    )


@router.post("/jobs/{job_id}/view")
def view_job(job_id: str, db: Session = Depends(get_db)):
    """Increment job view count."""
    crud.increment_job_view_count(db, job_id)
    return {"message": "View recorded"}


# Application Routes
@router.post("/applications", response_model=ApplicationOut)
def create_application(
    application_data: ApplicationCreate,
    current_user: models.User = Depends(get_current_personal_user),
    db: Session = Depends(get_db)
):
    """Apply to a job."""
    try:
        application = crud.create_application(db, current_user.id, application_data)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/applications", response_model=ApplicationListResponse)
def list_applications(
    status: Optional[str] = None,
    job_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List applications (different for personal vs company)."""
    skip = (page - 1) * limit

    if current_user.account_type == "personal":
        applications = crud.get_user_applications(db, current_user.id, status, skip, limit)
    else:
        applications = crud.get_company_applications(
            db, current_user.id, status=status, job_id=job_id, skip=skip, limit=limit
        )

    return ApplicationListResponse(
        applications=applications,
        total=len(applications),
        page=page,
        limit=limit
    )


@router.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get a specific application."""
    application = crud.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check permissions
    if current_user.account_type == "personal" and application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.account_type == "company":
        job = crud.get_job_by_id(db, application.job_id)
        if not job or job.company_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return application


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: str,
    status_update: ApplicationUpdate,
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Update application status (company only)."""
    application = crud.update_application_status(
        db, application_id, status_update.status, status_update.rejection_reason
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"message": "Application status updated", "application": application}


# Follow Routes
@router.post("/follow/{user_id}")
def follow_user(user_id: str, current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Follow a user or company."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target_user = crud.get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    following_type = "user" if target_user.account_type == "personal" else "company"
    crud.create_follow(db, current_user.id, user_id, following_type)

    return {"message": "Followed successfully"}


@router.delete("/follow/{user_id}")
def unfollow_user(user_id: str, current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Unfollow a user or company."""
    success = crud.delete_follow(db, current_user.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")

    return {"message": "Unfollowed successfully"}


@router.get("/follow/followers")
def get_followers(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get users following current user."""
    follows = crud.get_user_followers(db, current_user.id)
    # TODO: Convert to proper response format
    return {"followers": follows}


@router.get("/follow/following")
def get_following(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get users current user is following."""
    follows = crud.get_user_following(db, current_user.id)
    # TODO: Convert to proper response format
    return {"following": follows}


# Notification Routes
@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    is_read: Optional[bool] = None,
    page: int = 1,
    limit: int = 50,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List user notifications."""
    skip = (page - 1) * limit
    notifications = crud.get_user_notifications(db, current_user.id, is_read, skip, limit)
    unread_count = crud.get_unread_notification_count(db, current_user.id)

    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count
    )


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    success = crud.mark_notification_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_read(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    count = crud.mark_all_notifications_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}


# Messaging Routes
@router.post("/messages", response_model=MessageOut)
def send_message(
    message_data: MessageCreate,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Send a message to another user."""
    # Get or create conversation
    conversation = crud.get_or_create_conversation(db, current_user.id, message_data.receiver_id)

    # Create message
    message = crud.create_message(db, conversation.id, current_user.id, message_data.receiver_id, message_data.body)

    return message


@router.get("/messages", response_model=List[ConversationOut])
def list_conversations(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """List user's conversations."""
    # TODO: Implement proper conversation listing
    return []


@router.get("/messages/{conversation_id}", response_model=MessageListResponse)
def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get messages in a conversation."""
    messages = crud.get_conversation_messages(db, conversation_id, 0, limit)
    return MessageListResponse(conversation_id=conversation_id, messages=messages)


# Dashboard Routes
@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    if current_user.account_type == "personal":
        applications = crud.get_user_applications(db, current_user.id, limit=200)
        pending_count = sum(1 for app in applications if app.status in ("pending", "screening"))
        interview_count = sum(1 for app in applications if app.status == "interview")
        offer_count = sum(1 for app in applications if app.status == "offer")
        rejected_count = sum(1 for app in applications if app.status == "rejected")
        profile = crud.get_personal_profile(db, current_user.id)
        recommended = crud.get_recommended_jobs(db, current_user.id, limit=5)

        return DashboardStats(
            total_applications=len(applications),
            pending_count=pending_count,
            interview_count=interview_count,
            offer_count=offer_count,
            rejected_count=rejected_count,
            profile_completion=_estimate_profile_completion(profile),
            profile_views=0,
            recommended_jobs_count=len(recommended)
        )

    jobs = crud.get_company_jobs(db, current_user.id, limit=200)
    active_jobs = sum(1 for job in jobs if job.status == "active")
    applications = crud.get_company_applications(db, current_user.id, limit=500)
    total_applications = len(applications)
    match_scores = [app.match_score for app in applications if app.match_score is not None]
    avg_match_score = float(sum(match_scores) / len(match_scores)) if match_scores else 0.0
    now = datetime.utcnow()
    new_applications_today = sum(
        1 for app in applications if app.applied_at and app.applied_at >= now - timedelta(days=1)
    )
    interviews_scheduled = sum(1 for app in applications if app.status == "interview")

    return DashboardStats(
        active_jobs=active_jobs,
        total_applications=total_applications,
        avg_match_score=avg_match_score,
        time_saved_hours=int(total_applications * 0.5),
        new_applications_today=new_applications_today,
        interviews_scheduled=interviews_scheduled
    )


@router.get("/dashboard/activities", response_model=DashboardActivityListResponse)
def get_recent_activity(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get recent activity for dashboard."""
    activities: List[DashboardActivity] = []

    if current_user.account_type == "personal":
        applications = crud.get_user_applications(db, current_user.id, limit=5)
        for app in applications[:5]:
            job_title = app.job.title if app.job else "a job"
            status_label = app.status.replace("_", " ").title()
            activities.append(
                DashboardActivity(
                    id=str(app.id),
                    type="application",
                    message=f"Your application to {job_title} is now {status_label}.",
                    time=(app.updated_at or app.applied_at or datetime.utcnow()).isoformat(),
                    link=f"/applications/{app.id}"
                )
            )
    else:
        applications = crud.get_company_applications(db, current_user.id, limit=5)
        for app in applications[:5]:
            job_title = app.job.title if app.job else "a role"
            candidate_name = app.user.full_name if app.user and app.user.full_name else "A candidate"
            status_label = app.status.replace("_", " ").title()
            activities.append(
                DashboardActivity(
                    id=str(app.id),
                    type="application",
                    message=f"{candidate_name} is now {status_label} for {job_title}.",
                    time=(app.updated_at or app.applied_at or datetime.utcnow()).isoformat(),
                    link=f"/applications/{app.id}"
                )
            )

    return DashboardActivityListResponse(activities=activities)


# Screening Routes (Company Only)
@router.post("/screening/bulk-upload")
def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    job_id: str = None,
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Bulk upload resumes for screening."""
    # TODO: Implement bulk upload and screening
    return {"message": "Bulk upload not implemented yet"}


@router.post("/screening/process")
def process_screening(
    job_id: str,
    resume_ids: List[str],
    current_user: models.User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Process resumes against a job."""
    # TODO: Implement AI screening
    return {"message": "Screening not implemented yet"}


@router.get("/screening/results/{job_id}")
def get_screening_results(job_id: str, current_user: models.User = Depends(get_current_company_user), db: Session = Depends(get_db)):
    """Get screening results for a job."""
    # TODO: Implement results retrieval
    return {"results": []}
