from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from . import models
from .schemas import (
    UserCreate, PersonalProfileCreate, CompanyProfileCreate,
    JobCreate, ApplicationCreate, ResumeUpload, FollowCreate
)
from .config import settings
from .utils.token_utils import generate_secure_token


def _flatten_skill_entries(items: Any) -> List[str]:
    skills: List[str] = []
    if not items:
        return skills
    for item in items:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                skills.append(cleaned)
        elif isinstance(item, dict):
            for key in ("skill", "name", "label", "title"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    skills.append(value.strip())
                    break
    return skills


# User CRUD
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> models.User:
    from .utils.security import get_password_hash

    user = models.User(
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        account_type=user_data.account_type.value,
    )
    db.add(user)
    db.flush()  # Get user ID without committing

    # Create profile based on account type
    if user_data.account_type.value == "personal":
        profile = models.PersonalProfile(
            user_id=user.id,
            full_name=user_data.name,
        )
    else:  # company
        profile = models.CompanyProfile(
            user_id=user.id,
            company_name=user_data.company_name,
        )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def update_user_verification(db: Session, user_id: str, is_verified: bool) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_verified = is_verified
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    return user


def reset_failed_login_attempts(db: Session, user: models.User) -> models.User:
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def record_failed_login_attempt(db: Session, user: models.User) -> models.User:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# Profile CRUD
def get_personal_profile(db: Session, user_id: str) -> Optional[models.PersonalProfile]:
    return db.query(models.PersonalProfile).filter(models.PersonalProfile.user_id == user_id).first()


def get_company_profile(db: Session, user_id: str) -> Optional[models.CompanyProfile]:
    return db.query(models.CompanyProfile).filter(models.CompanyProfile.user_id == user_id).first()


def get_verified_companies(db: Session, industry: Optional[str] = None, size: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[models.CompanyProfile]:
    query = db.query(models.CompanyProfile).filter(models.CompanyProfile.verification_status == "verified")
    if industry:
        query = query.filter(models.CompanyProfile.industry.ilike(f"%{industry}%"))
    if size:
        query = query.filter(models.CompanyProfile.company_size == size)
    return query.order_by(models.CompanyProfile.company_name.asc()).offset(skip).limit(limit).all()


def get_verified_company_by_id(db: Session, user_id: str) -> Optional[models.CompanyProfile]:
    return db.query(models.CompanyProfile).filter(
        models.CompanyProfile.user_id == user_id,
        models.CompanyProfile.verification_status == "verified"
    ).first()


def get_company_followers_count(db: Session, user_id: str) -> int:
    return db.query(models.Follow).filter(
        models.Follow.following_id == user_id,
        models.Follow.following_type == "company"
    ).count()


def get_company_open_jobs_count(db: Session, user_id: str) -> int:
    return db.query(models.Job).filter(
        models.Job.company_id == user_id,
        models.Job.status == "active"
    ).count()


def update_personal_profile(db: Session, user_id: str, profile_data: PersonalProfileCreate) -> models.PersonalProfile:
    profile = db.query(models.PersonalProfile).filter(models.PersonalProfile.user_id == user_id).first()
    if not profile:
        profile = models.PersonalProfile(user_id=user_id)
        db.add(profile)

    # Update fields
    for field, value in profile_data.dict().items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def update_company_profile(db: Session, user_id: str, profile_data: CompanyProfileCreate) -> models.CompanyProfile:
    profile = db.query(models.CompanyProfile).filter(models.CompanyProfile.user_id == user_id).first()
    if not profile:
        profile = models.CompanyProfile(user_id=user_id)
        db.add(profile)

    # Update fields
    for field, value in profile_data.dict().items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


# Resume CRUD
def create_resume(
    db: Session,
    user_id: str,
    filename: str,
    file_url: str,
    file_size: int,
    version_name: str = "Main Resume",
    parsed_data: Dict[str, Any] = None,
    raw_text: str | None = None
) -> models.Resume:
    # Set as primary if it's the user's first resume
    is_primary = db.query(models.Resume).filter(models.Resume.user_id == user_id).count() == 0

    resume = models.Resume(
        user_id=user_id,
        filename=filename,
        file_url=file_url,
        file_size=file_size,
        version_name=version_name,
        is_primary=is_primary,
        parsed_data=parsed_data or {},
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resume_by_id(db: Session, resume_id: str) -> Optional[models.Resume]:
    return db.query(models.Resume).filter(models.Resume.id == resume_id).first()


def get_user_resumes(db: Session, user_id: str) -> List[models.Resume]:
    return db.query(models.Resume).filter(models.Resume.user_id == user_id).order_by(models.Resume.uploaded_at.desc()).all()


def set_primary_resume(db: Session, user_id: str, resume_id: str) -> bool:
    # Unset all primary flags for user
    db.query(models.Resume).filter(models.Resume.user_id == user_id).update({"is_primary": False})

    # Set this resume as primary
    resume = db.query(models.Resume).filter(
        and_(models.Resume.id == resume_id, models.Resume.user_id == user_id)
    ).first()
    if resume:
        resume.is_primary = True
        db.commit()
        return True
    return False


def delete_resume(db: Session, user_id: str, resume_id: str) -> bool:
    resume = db.query(models.Resume).filter(
        and_(models.Resume.id == resume_id, models.Resume.user_id == user_id)
    ).first()
    if resume:
        db.delete(resume)
        db.commit()
        return True
    return False


# Job CRUD
def create_job(db: Session, company_id: str, job_data: JobCreate) -> models.Job:
    job = models.Job(
        company_id=company_id,
        **job_data.dict()
    )
    if job.status == "active":
        job.expires_at = datetime.utcnow() + timedelta(days=30)

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_by_id(db: Session, job_id: str) -> Optional[models.Job]:
    return db.query(models.Job).filter(models.Job.id == job_id).first()


def get_company_jobs(db: Session, company_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Job]:
    query = db.query(models.Job).filter(models.Job.company_id == company_id)
    if status:
        query = query.filter(models.Job.status == status)
    return query.order_by(models.Job.created_at.desc()).offset(skip).limit(limit).all()


def update_job(db: Session, job_id: str, company_id: str, job_data: JobCreate) -> Optional[models.Job]:
    job = db.query(models.Job).filter(
        and_(models.Job.id == job_id, models.Job.company_id == company_id)
    ).first()
    if job:
        for field, value in job_data.dict().items():
            setattr(job, field, value)
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job


def close_job(db: Session, job_id: str, company_id: str) -> Optional[models.Job]:
    job = db.query(models.Job).filter(
        and_(models.Job.id == job_id, models.Job.company_id == company_id)
    ).first()
    if job:
        job.status = "closed"
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job


def duplicate_job(db: Session, job_id: str, company_id: str) -> Optional[models.Job]:
    original = db.query(models.Job).filter(
        and_(models.Job.id == job_id, models.Job.company_id == company_id)
    ).first()
    if not original:
        return None

    copied_requirements = dict(original.requirements) if isinstance(original.requirements, dict) else {}
    copied_screening = list(original.screening_questions) if isinstance(original.screening_questions, list) else []

    duplicate = models.Job(
        company_id=company_id,
        title=f"Copy of {original.title}",
        description=original.description,
        requirements=copied_requirements,
        location=original.location,
        remote_type=original.remote_type,
        employment_type=original.employment_type,
        salary_min=original.salary_min,
        salary_max=original.salary_max,
        salary_currency=original.salary_currency,
        screening_questions=copied_screening,
        status="draft",
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate


def get_similar_jobs(db: Session, job_id: str, limit: int = 3) -> List[models.Job]:
    base_job = get_job_by_id(db, job_id)
    if not base_job:
        return []

    base_skills = {
        skill.lower()
        for skill in (base_job.requirements.get("skills") if isinstance(base_job.requirements, dict) else [])
        if isinstance(skill, str)
    }
    if not base_skills:
        return []

    candidates = db.query(models.Job).filter(
        models.Job.status == "active",
        models.Job.id != job_id
    ).all()

    scored: List[tuple[int, models.Job]] = []
    for job in candidates:
        job_skills = {
            skill.lower()
            for skill in (job.requirements.get("skills") if isinstance(job.requirements, dict) else [])
            if isinstance(skill, str)
        }
        score = len(base_skills & job_skills)
        if score > 0:
            scored.append((score, job))

    scored.sort(key=lambda item: (-item[0], -item[1].application_count))
    return [job for _, job in scored[:limit]]


def get_saved_jobs(db: Session, user_id: str, limit: int = 10) -> List[models.SavedJob]:
    return (
        db.query(models.SavedJob)
        .options(
            joinedload(models.SavedJob.job)
            .joinedload(models.Job.company)
            .joinedload(models.User.company_profile)
        )
        .filter(models.SavedJob.user_id == user_id)
        .order_by(models.SavedJob.saved_at.desc())
        .limit(limit)
        .all()
    )


def get_recommended_jobs(db: Session, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    profile = get_personal_profile(db, user_id)
    user_skills = {skill.lower() for skill in _flatten_skill_entries(profile.skills)} if profile else set()
    jobs = (
        db.query(models.Job)
        .filter(models.Job.status == "active")
        .order_by(models.Job.application_count.desc(), models.Job.created_at.desc())
        .all()
    )
    scored: List[Dict[str, Any]] = []
    for job in jobs:
        job_requirements = job.requirements if isinstance(job.requirements, dict) else {}
        job_skills = {skill.lower() for skill in _flatten_skill_entries(job_requirements.get("skills"))}
        matched = sorted(list(user_skills & job_skills))
        score = 50 + min(40, len(matched) * 8)
        scored.append({"job": job, "match_score": float(min(95, score)), "skills_match": matched})
    scored.sort(key=lambda item: item["match_score"], reverse=True)
    return scored[:limit]


def get_company_applications(db: Session, company_id: str, status: Optional[str] = None,
                             job_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Application]:
    query = (
        db.query(models.Application)
        .join(models.Job)
        .options(
            joinedload(models.Application.job),
            joinedload(models.Application.user).joinedload(models.User.personal_profile)
        )
        .filter(models.Job.company_id == company_id)
    )
    if job_id:
        query = query.filter(models.Job.id == job_id)
    if status:
        query = query.filter(models.Application.status == status)
    return query.order_by(models.Application.applied_at.desc()).offset(skip).limit(limit).all()


def delete_job(db: Session, job_id: str, company_id: str) -> bool:
    job = db.query(models.Job).filter(
        and_(models.Job.id == job_id, models.Job.company_id == company_id)
    ).first()
    if job:
        job.status = "closed"
        db.commit()
        return True
    return False


def search_jobs(db: Session, query: Optional[str] = None, location: Optional[str] = None,
                remote_type: Optional[str] = None, employment_type: Optional[str] = None,
                salary_min: Optional[int] = None, skills: List[str] = None,
                skip: int = 0, limit: int = 20) -> Dict[str, Any]:

    jobs_query = db.query(models.Job).filter(
        and_(models.Job.status == "active", models.Job.expires_at > datetime.utcnow())
    )

    # Apply filters
    if query:
        jobs_query = jobs_query.filter(
            or_(models.Job.title.ilike(f"%{query}%"), models.Job.description.ilike(f"%{query}%"))
        )

    if location:
        jobs_query = jobs_query.filter(models.Job.location.ilike(f"%{location}%"))

    if remote_type:
        jobs_query = jobs_query.filter(models.Job.remote_type == remote_type)

    if employment_type:
        jobs_query = jobs_query.filter(models.Job.employment_type == employment_type)

    if salary_min:
        jobs_query = jobs_query.filter(models.Job.salary_max >= salary_min)

    def _job_matches_skills(job: models.Job, required_skills: List[str]) -> bool:
        job_skills = job.requirements.get("skills") if isinstance(job.requirements, dict) else None
        if not job_skills:
            return False
        lowered = [skill.lower() for skill in job_skills if isinstance(skill, str)]
        return all(skill.lower() in lowered for skill in required_skills)

    jobs_query = jobs_query.order_by(models.Job.created_at.desc())

    if skills:
        all_jobs = jobs_query.all()
        filtered_jobs = [job for job in all_jobs if _job_matches_skills(job, skills)]
        total = len(filtered_jobs)
        jobs = filtered_jobs[skip:skip + limit]
    else:
        total = jobs_query.count()
        jobs = jobs_query.offset(skip).limit(limit).all()

    return {"jobs": jobs, "total": total}


def increment_job_view_count(db: Session, job_id: str):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if job:
        job.view_count += 1
        db.commit()


# Application CRUD
def create_application(db: Session, user_id: str, application_data: ApplicationCreate) -> models.Application:
    # Check for duplicate application
    existing = db.query(models.Application).filter(
        and_(models.Application.job_id == application_data.job_id, models.Application.user_id == user_id)
    ).first()
    if existing:
        raise ValueError("Already applied to this job")

    application = models.Application(
        user_id=user_id,
        **application_data.dict()
    )
    db.add(application)

    # Increment job application count
    job = db.query(models.Job).filter(models.Job.id == application_data.job_id).first()
    if job:
        job.application_count += 1

    db.commit()
    db.refresh(application)
    return application


def get_application_by_id(db: Session, application_id: str) -> Optional[models.Application]:
    return db.query(models.Application).filter(models.Application.id == application_id).first()


def get_user_applications(db: Session, user_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Application]:
    query = (
        db.query(models.Application)
        .options(
            joinedload(models.Application.job).joinedload(models.Job.company),
            joinedload(models.Application.user)
        )
        .filter(models.Application.user_id == user_id)
    )
    if status:
        query = query.filter(models.Application.status == status)
    return query.order_by(models.Application.applied_at.desc()).offset(skip).limit(limit).all()


def get_job_applications(db: Session, job_id: str, company_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.Application]:
    # Verify company owns the job
    job = db.query(models.Job).filter(
        and_(models.Job.id == job_id, models.Job.company_id == company_id)
    ).first()
    if not job:
        return []

    query = db.query(models.Application).filter(models.Application.job_id == job_id)
    if status:
        query = query.filter(models.Application.status == status)
    return query.order_by(models.Application.applied_at.desc()).offset(skip).limit(limit).all()


def update_application_status(db: Session, application_id: str, status: str, rejection_reason: Optional[str] = None) -> Optional[models.Application]:
    application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if application:
        application.status = status
        if rejection_reason:
            application.rejection_reason = rejection_reason
        application.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(application)
    return application


# Follow CRUD
def create_follow(db: Session, follower_id: str, following_id: str, following_type: str) -> models.Follow:
    follow = models.Follow(
        follower_id=follower_id,
        following_id=following_id,
        following_type=following_type
    )
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


def delete_follow(db: Session, follower_id: str, following_id: str) -> bool:
    follow = db.query(models.Follow).filter(
        and_(models.Follow.follower_id == follower_id, models.Follow.following_id == following_id)
    ).first()
    if follow:
        db.delete(follow)
        db.commit()
        return True
    return False


def get_user_followers(db: Session, user_id: str) -> List[models.Follow]:
    return db.query(models.Follow).filter(models.Follow.following_id == user_id).all()


def get_user_following(db: Session, user_id: str) -> List[models.Follow]:
    return db.query(models.Follow).filter(models.Follow.follower_id == user_id).all()


def is_following(db: Session, follower_id: str, following_id: str) -> bool:
    return db.query(models.Follow).filter(
        and_(models.Follow.follower_id == follower_id, models.Follow.following_id == following_id)
    ).count() > 0


# Notification CRUD
def create_notification(db: Session, user_id: str, type: str, title: str, message: str, link: Optional[str] = None) -> models.Notification:
    notification = models.Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_user_notifications(db: Session, user_id: str, is_read: Optional[bool] = None, skip: int = 0, limit: int = 50) -> List[models.Notification]:
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read == is_read)
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_notification_read(db: Session, notification_id: str, user_id: str) -> bool:
    notification = db.query(models.Notification).filter(
        and_(models.Notification.id == notification_id, models.Notification.user_id == user_id)
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
        return True
    return False


def mark_all_notifications_read(db: Session, user_id: str) -> int:
    count = db.query(models.Notification).filter(
        and_(models.Notification.user_id == user_id, models.Notification.is_read == False)
    ).update({"is_read": True})
    db.commit()
    return count


def get_unread_notification_count(db: Session, user_id: str) -> int:
    return db.query(models.Notification).filter(
        and_(models.Notification.user_id == user_id, models.Notification.is_read == False)
    ).count()


# Messaging CRUD
def get_or_create_conversation(db: Session, user1_id: str, user2_id: str) -> models.Conversation:
    # Ensure consistent ordering for unique constraint
    participant_1_id, participant_2_id = sorted([user1_id, user2_id])

    conversation = db.query(models.Conversation).filter(
        and_(models.Conversation.participant_1_id == participant_1_id, models.Conversation.participant_2_id == participant_2_id)
    ).first()

    if not conversation:
        conversation = models.Conversation(
            participant_1_id=participant_1_id,
            participant_2_id=participant_2_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


def create_message(db: Session, conversation_id: str, sender_id: str, receiver_id: str, body: str) -> models.Message:
    message = models.Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        body=body
    )
    db.add(message)

    # Update conversation last_message_at
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if conversation:
        conversation.last_message_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages(db: Session, conversation_id: str, skip: int = 0, limit: int = 50) -> List[models.Message]:
    return db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(
        models.Message.sent_at.desc()
    ).offset(skip).limit(limit).all()


def get_user_conversations(db: Session, user_id: str) -> List[Dict[str, Any]]:
    # This is a complex query that would need to be implemented with joins
    # For now, return empty list - will implement when needed
    return []


def mark_message_read(db: Session, message_id: str, user_id: str) -> bool:
    message = db.query(models.Message).filter(
        and_(models.Message.id == message_id, models.Message.receiver_id == user_id)
    ).first()
    if message:
        message.is_read = True
        db.commit()
        return True
    return False


# Verification Token CRUD
def create_verification_token(db: Session, user_id: str, expires_at: datetime) -> models.VerificationToken:
    token_value = generate_secure_token()
    # Remove previous pending tokens to avoid duplicates
    db.query(models.VerificationToken).filter(models.VerificationToken.user_id == user_id).delete()
    token = models.VerificationToken(
        user_id=user_id,
        expires_at=expires_at,
        token=token_value
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_verification_token(db: Session, token: str) -> Optional[models.VerificationToken]:
    return db.query(models.VerificationToken).filter(models.VerificationToken.token == token).first()


def delete_verification_token(db: Session, token_id: str):
    token = db.query(models.VerificationToken).filter(models.VerificationToken.id == token_id).first()
    if token:
        db.delete(token)
        db.commit()


# Password reset CRUD
def create_password_reset_token(db: Session, user_id: str, expires_at: datetime) -> models.PasswordResetToken:
    token_value = generate_secure_token()
    db.query(models.PasswordResetToken).filter(models.PasswordResetToken.user_id == user_id).delete()
    reset_token = models.PasswordResetToken(
        user_id=user_id,
        expires_at=expires_at,
        token=token_value
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_password_reset_token(db: Session, token: str) -> Optional[models.PasswordResetToken]:
    return db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == token).first()


def delete_password_reset_token(db: Session, token_id: str):
    token = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.id == token_id).first()
    if token:
        db.delete(token)
        db.commit()


# Refresh Token CRUD
def create_refresh_token(db: Session, user_id: str, expires_at: datetime) -> models.RefreshToken:
    token_value = generate_secure_token()
    token = models.RefreshToken(
        user_id=user_id,
        expires_at=expires_at,
        token=token_value
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token(db: Session, token: str) -> Optional[models.RefreshToken]:
    return db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()


def delete_refresh_token(db: Session, token: str):
    refresh_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()
    if refresh_token:
        db.delete(refresh_token)
        db.commit()


def delete_user_refresh_tokens(db: Session, user_id: str):
    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user_id).delete()
    db.commit()
