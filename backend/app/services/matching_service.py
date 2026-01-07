"""
Candidate matching and scoring service.
Ranks candidates against job descriptions using semantic similarity and skill matching.
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Resume, Candidate, JobDescription, CandidateScore
from app.utils.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching candidates to jobs."""
    
    @staticmethod
    def calculate_semantic_similarity(job: JobDescription, resume: Resume) -> float:
        """
        Calculate semantic similarity between job and resume.
        
        Args:
            job: JobDescription object
            resume: Resume object
            
        Returns:
            Similarity score (0-100)
        """
        embedding_service = get_embedding_service()
        
        # Generate embeddings if not already present
        if not resume.embedding:
            text = f"{resume.name} {' '.join(resume.parsed_data.get('skills', []))} {resume.parsed_data.get('raw_text', '')}"
            resume_embedding = embedding_service.embed_text(text)
        else:
            resume_embedding = np.array(resume.embedding)
        
        if not job.embedding:
            job_text = f"{job.title} {job.description} {' '.join(job.required_skills or [])}"
            job_embedding = embedding_service.embed_text(job_text)
        else:
            job_embedding = np.array(job.embedding)
        
        # Calculate cosine similarity
        similarity = embedding_service.cosine_similarity(job_embedding, resume_embedding)
        return similarity * 100  # Convert to 0-100 scale
    
    @staticmethod
    def calculate_skill_match(
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skill match percentage and identify matched/missing skills.
        
        Args:
            candidate_skills: List of candidate's skills
            required_skills: List of required skills
            
        Returns:
            Tuple of (match_percentage, matched_skills, missing_skills)
        """
        if not required_skills:
            return 100.0, candidate_skills, []
        
        # Normalize to lowercase for comparison
        candidate_skills_lower = {s.lower() for s in candidate_skills}
        required_skills_lower = {s.lower() for s in required_skills}
        
        # Find matches
        matched = list(candidate_skills_lower & required_skills_lower)
        missing = list(required_skills_lower - candidate_skills_lower)
        
        # Calculate percentage
        match_percentage = (len(matched) / len(required_skills_lower)) * 100 if required_skills_lower else 0
        
        return match_percentage, matched, missing
    
    @staticmethod
    def calculate_experience_relevance(
        candidate_years: Optional[float],
        required_years: Optional[int]
    ) -> float:
        """
        Calculate experience relevance score.
        
        Args:
            candidate_years: Years of experience from resume
            required_years: Required years of experience
            
        Returns:
            Score (0-100)
        """
        if required_years is None or required_years == 0:
            return 100.0
        
        if candidate_years is None:
            return 0.0
        
        # Score: 100 if meets requirement, scale down if below
        if candidate_years >= required_years:
            return 100.0
        else:
            return (candidate_years / required_years) * 100
    
    @staticmethod
    def calculate_education_fit(
        candidate_education: Optional[str],
        required_education: Optional[str]
    ) -> float:
        """
        Calculate education fit score.
        
        Args:
            candidate_education: Candidate's education from resume
            required_education: Required education
            
        Returns:
            Score (0-100)
        """
        # Simple heuristic: look for degree keywords
        if not required_education or not candidate_education:
            return 50.0  # Neutral score if missing data
        
        required_lower = required_education.lower()
        candidate_lower = candidate_education.lower()
        
        # Check for degree level matches
        degree_keywords = {
            'phd': ['phd', 'doctorate'],
            'masters': ['masters', 'master', 'm.s.', 'ms', 'm.a.', 'ma'],
            'bachelor': ['bachelor', 'b.s.', 'bs', 'b.a.', 'ba', 'b.eng', 'b.e.'],
            'associate': ['associate', 'a.s.', 'as']
        }
        
        candidate_degree = None
        required_degree = None
        
        for degree, keywords in degree_keywords.items():
            for kw in keywords:
                if kw in candidate_lower:
                    candidate_degree = degree
                    break
            for kw in keywords:
                if kw in required_lower:
                    required_degree = degree
                    break
        
        # Score based on match
        if candidate_degree == required_degree:
            return 100.0
        elif candidate_degree is None:
            return 40.0  # No degree found
        else:
            # Partial credit for having a degree
            return 60.0
    
    @staticmethod
    def calculate_overall_score(
        semantic_score: float,
        skill_score: float,
        experience_score: float,
        education_score: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall candidate score using weighted average.
        
        Args:
            semantic_score: Semantic similarity (0-100)
            skill_score: Skill match percentage (0-100)
            experience_score: Experience relevance (0-100)
            education_score: Education fit (0-100)
            weights: Optional custom weights (defaults from settings)
            
        Returns:
            Overall score (0-100)
        """
        if weights is None:
            weights = settings.SCORE_WEIGHTS
        
        scores = {
            "semantic_similarity": semantic_score,
            "skill_match": skill_score,
            "experience_relevance": experience_score,
            "education_fit": education_score,
        }
        
        # Calculate weighted average
        total_weight = sum(weights.values())
        overall = sum(scores[key] * weight for key, weight in weights.items()) / total_weight
        
        return float(min(100, max(0, overall)))  # Clamp to 0-100
    
    @staticmethod
    def score_candidate(
        resume: Resume,
        job: JobDescription,
        db: Session
    ) -> CandidateScore:
        """
        Score a single candidate against a job.
        
        Args:
            resume: Resume to score
            job: JobDescription to score against
            db: Database session
            
        Returns:
            CandidateScore object with detailed scoring
        """
        try:
            candidate = resume.candidates[0] if resume.candidates else None
            if not candidate:
                logger.error(f"No candidate found for resume {resume.id}")
                raise ValueError(f"No candidate found for resume {resume.id}")
            
            # Get candidate data
            candidate_skills = candidate.normalized_skills or candidate.skills or []
            candidate_years = candidate.years_of_experience
            candidate_education = candidate.education
            
            # Get job requirements
            required_skills = job.required_skills or []
            required_years = job.required_experience_years
            required_education = job.required_education
            
            # Calculate component scores
            semantic_score = MatchingService.calculate_semantic_similarity(job, resume)
            skill_match_pct, matched_skills, missing_skills = MatchingService.calculate_skill_match(
                candidate_skills, required_skills
            )
            experience_score = MatchingService.calculate_experience_relevance(
                candidate_years, required_years
            )
            education_score = MatchingService.calculate_education_fit(
                candidate_education, required_education
            )
            
            # Calculate overall score
            overall_score = MatchingService.calculate_overall_score(
                semantic_score, skill_match_pct, experience_score, education_score
            )
            
            # Generate explanation
            explanation = MatchingService.generate_explanation(
                matched_skills, missing_skills, experience_score, education_score
            )
            
            # Create CandidateScore record
            import uuid
            score = CandidateScore(
                id=str(uuid.uuid4()),
                resume_id=resume.id,
                job_id=job.id,
                candidate_id=candidate.id,
                overall_score=overall_score,
                semantic_similarity_score=semantic_score,
                skill_match_score=skill_match_pct,
                experience_relevance_score=experience_score,
                education_fit_score=education_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                skill_match_percentage=skill_match_pct,
                explanation=explanation,
                reasoning={
                    "semantic_similarity": semantic_score,
                    "skill_match": {
                        "percentage": skill_match_pct,
                        "matched": matched_skills,
                        "missing": missing_skills
                    },
                    "experience": {
                        "candidate_years": candidate_years,
                        "required_years": required_years,
                        "score": experience_score
                    },
                    "education": {
                        "candidate": candidate_education,
                        "required": required_education,
                        "score": education_score
                    }
                }
            )
            
            db.add(score)
            db.commit()
            
            logger.info(f"Scored resume {resume.id} against job {job.id}: {overall_score:.1f}")
            return score
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error scoring candidate: {e}")
            raise
    
    @staticmethod
    def generate_explanation(
        matched_skills: List[str],
        missing_skills: List[str],
        experience_score: float,
        education_score: float
    ) -> str:
        """
        Generate human-readable explanation of score.
        
        Args:
            matched_skills: Skills that matched
            missing_skills: Skills that are missing
            experience_score: Experience score (0-100)
            education_score: Education score (0-100)
            
        Returns:
            Explanation string
        """
        parts = []
        
        # Skills summary
        if matched_skills:
            parts.append(f"Matches {len(matched_skills)} required skills: {', '.join(matched_skills[:3])}")
        if missing_skills:
            parts.append(f"Missing {len(missing_skills)} skills: {', '.join(missing_skills[:3])}")
        
        # Experience summary
        if experience_score == 100:
            parts.append("Meets or exceeds experience requirements")
        elif experience_score >= 75:
            parts.append("Good experience alignment")
        elif experience_score >= 50:
            parts.append("Moderate experience gap")
        else:
            parts.append("Significant experience gap")
        
        # Education summary
        if education_score == 100:
            parts.append("Education matches requirements")
        elif education_score >= 60:
            parts.append("Education is acceptable")
        else:
            parts.append("Education may not fully meet requirements")
        
        return ". ".join(parts) + "."
    
    @staticmethod
    def rank_candidates(
        job_id: str,
        db: Session,
        limit: Optional[int] = 50
    ) -> List[CandidateScore]:
        """
        Get ranked list of candidates for a job.
        
        Args:
            job_id: Job description ID
            db: Database session
            limit: Maximum number of results to return
            
        Returns:
            List of CandidateScore objects sorted by overall_score descending
        """
        try:
            scores = db.query(CandidateScore).filter(
                CandidateScore.job_id == job_id
            ).order_by(CandidateScore.overall_score.desc()).limit(limit).all()
            
            # Assign ranks
            for rank, score in enumerate(scores, 1):
                score.rank = rank
                score.percentile = ((len(scores) - rank) / len(scores) * 100) if scores else 0
            
            db.commit()
            return scores
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error ranking candidates for job {job_id}: {e}")
            return []
