from sqlalchemy.orm import Session
from . import models, schemas
import json


def create_resume(db: Session, filename: str, parsed: dict = None):
    parsed_json = json.dumps(parsed or {})
    db_resume = models.Resume(filename=filename, parsed=parsed_json)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


def get_resume(db: Session, resume_id: int):
    return db.query(models.Resume).filter(models.Resume.id == resume_id).first()


def create_job(db: Session, title: str, description: str):
    job = models.JobDescription(title=title, description=description)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_resumes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Resume).offset(skip).limit(limit).all()
