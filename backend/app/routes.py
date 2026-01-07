from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud
from .schemas import ResumeOut, JobOut, JobCreate
from .database import get_db, engine
from . import models
from .services.parser import ResumeService, ResumeParsingError
from .services.embeddings import EmbeddingService
import shutil
import os
import json

router = APIRouter()

emb_service = EmbeddingService()


@router.post("/upload-resume/", response_model=ResumeOut)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # parse
    try:
        parsed = ResumeService.parse(file_path)
    except ResumeParsingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_resume = crud.create_resume(db, filename=file.filename, parsed=parsed)

    return db_resume


@router.post("/jobs/", response_model=JobOut)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    job = crud.create_job(db, title=job_in.title, description=job_in.description)
    return job


@router.get("/resumes/", response_model=list[ResumeOut])
def list_resumes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_resumes(db, skip=skip, limit=limit)
