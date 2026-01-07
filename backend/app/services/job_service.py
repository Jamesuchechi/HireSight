"""
Job description service.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from app.models import JobDescription
from app.utils.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing job descriptions."""
    
    @staticmethod
    def create_job(
        title: str,
        description: str,
        company: Optional[str] = None,
        requirements: Optional[str] = None,
        required_skills: Optional[list] = None,
        required_experience_years: Optional[int] = None,
        required_education: Optional[str] = None,
        db: Optional[Session] = None
    ) -> JobDescription:
        """
        Create a new job description.
        
        Args:
            title: Job title
            description: Job description text
            company: Company name
            requirements: Additional requirements
            required_skills: List of required skills
            required_experience_years: Years of experience required
            required_education: Education requirements
            db: Database session
            
        Returns:
            JobDescription object
        """
        try:
            # Normalize skills
            normalized_skills = []
            if required_skills:
                normalized_skills = [s.lower().strip() for s in required_skills if s.strip()]
                normalized_skills = list(set(normalized_skills))  # Remove duplicates
            
            job = JobDescription(
                id=str(uuid.uuid4()),
                title=title,
                company=company,
                description=description,
                requirements=requirements,
                required_skills=normalized_skills,
                required_experience_years=required_experience_years,
                required_education=required_education
            )
            
            if db:
                db.add(job)
                db.commit()
                logger.info(f"Created job {job.id}: {job.title}")
            
            return job
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Error creating job: {e}")
            raise
    
    @staticmethod
    def generate_job_embedding(job_id: str, db: Session) -> bool:
        """
        Generate and store embedding for a job.
        
        Args:
            job_id: ID of job to embed
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return False
            
            # Generate embedding from job description
            embedding_service = get_embedding_service()
            text_to_embed = f"{job.title} {job.description} {' '.join(job.required_skills or [])}"
            
            embedding = embedding_service.embed_text(text_to_embed)
            
            # Store embedding
            job.embedding = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
            job.embedding_model = embedding_service.model_name
            
            db.commit()
            logger.info(f"Generated embedding for job {job_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating embedding for job {job_id}: {e}")
            return False
    
    @staticmethod
    def update_job(
        job_id: str,
        db: Session,
        title: Optional[str] = None,
        description: Optional[str] = None,
        company: Optional[str] = None,
        requirements: Optional[str] = None,
        required_skills: Optional[list] = None,
        required_experience_years: Optional[int] = None,
        required_education: Optional[str] = None
    ) -> Optional[JobDescription]:
        """
        Update a job description.
        
        Args:
            job_id: Job ID to update
            db: Database session
            **kwargs: Fields to update
            
        Returns:
            Updated JobDescription object
        """
        try:
            job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return None
            
            # Update fields
            if title is not None:
                job.title = title
            if description is not None:
                job.description = description
            if company is not None:
                job.company = company
            if requirements is not None:
                job.requirements = requirements
            if required_skills is not None:
                job.required_skills = [s.lower().strip() for s in required_skills if s.strip()]
            if required_experience_years is not None:
                job.required_experience_years = required_experience_years
            if required_education is not None:
                job.required_education = required_education
            
            # Re-generate embedding if description changed
            if description is not None or required_skills is not None:
                JobService.generate_job_embedding(job_id, db)
            else:
                db.commit()
            
            logger.info(f"Updated job {job_id}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating job {job_id}: {e}")
            raise
    
    @staticmethod
    def delete_job(job_id: str, db: Session) -> bool:
        """
        Delete a job description.
        
        Args:
            job_id: Job ID to delete
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
            if not job:
                return False
            
            db.delete(job)
            db.commit()
            
            logger.info(f"Deleted job {job_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
