"""
Resume parsing service - handles file upload, parsing, and storage.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Resume, Candidate
from app.utils.parser import parse_resume
from app.utils.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for handling resume uploads and parsing."""
    
    @staticmethod
    def save_uploaded_file(file, original_filename: str) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file: FastAPI UploadFile object
            original_filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Generate unique filename to avoid collisions
        import uuid
        file_ext = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = settings.UPLOADS_DIR / unique_filename
        
        # Save file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        return str(file_path)
    
    @staticmethod
    def parse_and_store_resume(
        file_path: str,
        original_filename: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Parse resume and store in database.
        
        Args:
            file_path: Path to resume file
            original_filename: Original filename
            db: Database session
            
        Returns:
            Dictionary with resume and candidate data
        """
        import uuid
        from datetime import datetime
        
        logger.info(f"Parsing resume: {original_filename}")
        
        # Parse the file
        parsed_data = parse_resume(file_path)
        
        if not parsed_data.get("success"):
            logger.error(f"Failed to parse resume: {parsed_data.get('error')}")
            raise ValueError(f"Failed to parse resume: {parsed_data.get('error')}")
        
        # Get file size
        file_size = Path(file_path).stat().st_size
        file_ext = Path(file_path).suffix.lower()[1:]  # Remove the dot
        
        try:
            # Create Resume record
            resume = Resume(
                id=str(uuid.uuid4()),
                filename=Path(file_path).name,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_ext,
                name=parsed_data.get("name"),
                email=parsed_data.get("email"),
                phone=parsed_data.get("phone"),
                location=parsed_data.get("location"),
                raw_text=parsed_data.get("raw_text"),
                parsed_data=parsed_data,
                embedding_model=None,  # Will be set when embedding is generated
                processed=1  # Marked as parsed
            )
            
            db.add(resume)
            db.flush()  # Get the ID without committing
            
            # Create Candidate record
            candidate = Candidate(
                id=str(uuid.uuid4()),
                resume_id=resume.id,
                name=parsed_data.get("name") or "Unknown",
                email=parsed_data.get("email"),
                phone=parsed_data.get("phone"),
                location=parsed_data.get("location"),
                skills=parsed_data.get("skills"),
                normalized_skills=parsed_data.get("skills")  # Will be normalized later
            )
            
            db.add(candidate)
            db.commit()
            
            logger.info(f"Successfully stored resume {resume.id} for {candidate.name}")
            
            return {
                "resume": resume,
                "candidate": candidate,
                "parsed_data": parsed_data
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing resume in database: {e}")
            raise
    
    @staticmethod
    def generate_resume_embedding(resume_id: str, db: Session) -> bool:
        """
        Generate and store embedding for a resume.
        
        Args:
            resume_id: ID of resume to embed
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                logger.error(f"Resume {resume_id} not found")
                return False
            
            # Generate embedding from resume text
            embedding_service = get_embedding_service()
            text_to_embed = f"{resume.name} {' '.join(resume.parsed_data.get('skills', []))} {resume.parsed_data.get('raw_text', '')}"
            
            embedding = embedding_service.embed_text(text_to_embed)
            
            # Store embedding (convert numpy array to list for JSON serialization)
            resume.embedding = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
            resume.embedding_model = embedding_service.model_name
            resume.processed = 2  # Mark as embedded
            
            db.commit()
            logger.info(f"Generated embedding for resume {resume_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating embedding for resume {resume_id}: {e}")
            return False
    
    @staticmethod
    def delete_resume(resume_id: str, db: Session) -> bool:
        """
        Delete resume and associated data.
        
        Args:
            resume_id: ID of resume to delete
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                return False
            
            # Delete file from disk
            file_path = Path(resume.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted resume file: {file_path}")
            
            # Delete from database (cascade will handle candidates and scores)
            db.delete(resume)
            db.commit()
            
            logger.info(f"Deleted resume {resume_id} from database")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting resume {resume_id}: {e}")
            return False
