from pathlib import Path
from uuid import uuid4
from typing import List, Optional
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models
from .config import settings
from .database import get_db
from .schemas import *
from .utils.security import (
    get_current_user, get_current_verified_user,
    get_current_personal_user, get_current_company_user
)

router = APIRouter()


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
    # TODO: Implement filtering and pagination
    # For now, return empty list
    return []


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

    # TODO: Parse resume content
    parsed_data = {}

    resume = crud.create_resume(
        db,
        user_id=current_user.id,
        filename=target_filename,
        file_url=str(file_path),
        file_size=file_size,
        version_name=version_name,
        parsed_data=parsed_data
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
    skills_list = skills.split(",") if skills else None
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
        # For company, this would need job_id parameter - simplified for now
        applications = []

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
@router.get("/dashboard/stats")
def get_dashboard_stats(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    # TODO: Implement actual stats calculation
    if current_user.account_type == "personal":
        return DashboardStats(
            total_applications=0,
            pending_count=0,
            interview_count=0,
            offer_count=0,
            rejected_count=0,
            profile_completion=50,
            profile_views=0,
            recommended_jobs_count=0
        )
    else:
        return DashboardStats(
            active_jobs=0,
            total_applications=0,
            avg_match_score=0,
            time_saved_hours=0,
            new_applications_today=0,
            interviews_scheduled=0
        )


@router.get("/dashboard/recent-activity")
def get_recent_activity(current_user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    """Get recent activity for dashboard."""
    # TODO: Implement recent activity
    return {"activities": []}


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
