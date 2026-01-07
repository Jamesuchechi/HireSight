from sqlalchemy.orm import Session

from . import models


def create_resume(
    db: Session,
    *,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    file_type: str,
    parsed_data: dict | None = None,
):
    parsed = parsed_data or {}
    db_resume = models.Resume(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        parsed_data=parsed,
        name=parsed.get("name"),
        email=parsed.get("email"),
        phone=parsed.get("mobile_number") or parsed.get("phone"),
        location=parsed.get("location"),
        raw_text=parsed.get("text"),
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


def get_resume(db: Session, resume_id: str):
    return db.query(models.Resume).filter(models.Resume.id == resume_id).first()


def create_job(
    db: Session,
    *,
    title: str,
    description: str,
    company: str | None = None,
    requirements: str | None = None,
    required_skills: list[str] | None = None,
    required_experience_years: int | None = None,
    required_education: str | None = None,
):
    job = models.JobDescription(
        title=title,
        company=company,
        description=description,
        requirements=requirements,
        required_skills=required_skills or [],
        required_experience_years=required_experience_years,
        required_education=required_education,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_resumes(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Resume)
        .order_by(models.Resume.upload_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_jobs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.JobDescription)
        .order_by(models.JobDescription.created_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
