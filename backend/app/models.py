from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsed = Column(Text)  # JSON string of parsed fields
    embedding_id = Column(Integer, ForeignKey("embeddings.id"), nullable=True)
    embedding = relationship("Embedding", back_populates="resume")


class JobDescription(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateScore(Base):
    __tablename__ = "candidate_scores"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    score = Column(Float, nullable=False)
    explanation = Column(Text)


class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    # Store vector as JSON text by default; switch to pgvector + migration for postgres
    vector = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resume = relationship("Resume", uselist=False, back_populates="embedding")
