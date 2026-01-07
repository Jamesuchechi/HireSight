from pathlib import Path
from uuid import uuid4

import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud
from .config import settings
from .schemas import ResumeOut, JobOut, JobCreate
from .database import get_db
from .services.parser import ResumeService, ResumeParsingError
from .services.embeddings import EmbeddingService
from .utils.security import get_current_active_user, get_current_company_user

router = APIRouter()

emb_service = EmbeddingService()


@router.post("/upload-resume/", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Use PDF or DOCX only."
        )

    upload_dir = settings.UPLOADS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    target_filename = f"{uuid4().hex}_{file.filename}"
    file_path = upload_dir / target_filename
    with open(file_path, "wb") as destination:
        shutil.copyfileobj(file.file, destination)

    file_size = file_path.stat().st_size

    try:
        parsed = ResumeService.parse(str(file_path))
    except ResumeParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db_resume = crud.create_resume(
        db,
        filename=target_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_suffix,
        parsed_data=parsed,
    )

    return db_resume


@router.post("/jobs/", response_model=JobOut)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_company_user),
):
    job = crud.create_job(
        db,
        title=job_in.title,
        description=job_in.description,
        company=job_in.company or current_user.company_name,
        requirements=job_in.requirements,
        required_skills=job_in.required_skills,
        required_experience_years=job_in.required_experience_years,
        required_education=job_in.required_education,
    )
    return job


@router.get("/jobs/", response_model=list[JobOut])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_jobs(db, skip=skip, limit=limit)


@router.get("/resumes/", response_model=list[ResumeOut])
def list_resumes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud.list_resumes(db, skip=skip, limit=limit)
