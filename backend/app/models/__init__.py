"""
SQLAlchemy ORM models for database tables.
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


# Authentication & User Management
class User(Base):
    """User model with role-based access."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    account_type = Column(String(20), nullable=False)  # 'personal' or 'company'
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    personal_profile = relationship("PersonalProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan")
    follows_as_follower = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    follows_as_following = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, account_type={self.account_type})>"


    @property
    def full_name(self):
        """Convenience property to expose personal profile full_name."""
        return self.personal_profile.full_name if self.personal_profile else None

    @property
    def company_name(self):
        """Convenience property to expose company profile company_name."""
        return self.company_profile.company_name if self.company_profile else None

class VerificationToken(Base):
    """Email verification tokens."""
    __tablename__ = "verification_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="verification_tokens")

    def __repr__(self):
        return f"<VerificationToken(user_id={self.user_id}, expires_at={self.expires_at})>"


class PasswordResetToken(Base):
    """Temporary tokens used for password resets."""
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, expires_at={self.expires_at})>"


class RefreshToken(Base):
    """Refresh tokens for JWT authentication."""
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at})>"


# User Profiles
class PersonalProfile(Base):
    """Profile for personal (job seeker) accounts."""
    __tablename__ = "personal_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    full_name = Column(String(255), nullable=False)
    headline = Column(String(255))
    avatar_url = Column(String(512))
    location = Column(String(255))
    phone = Column(String(50))
    bio = Column(Text)
    skills = Column(JSON, default=list)  # [{skill: "React", proficiency: "expert"}]
    experience = Column(JSON, default=list)  # [{company, role, start_date, end_date, description}]
    education = Column(JSON, default=list)  # [{institution, degree, field, start_date, end_date}]
    certifications = Column(JSON, default=list)  # [{name, issuer, date, credential_url}]
    portfolio_links = Column(JSON, default=list)  # [{type: "github", url}]
    preferred_job_types = Column(JSON, default=list)  # ["full-time", "remote"]
    salary_expectation_min = Column(Integer)
    salary_expectation_max = Column(Integer)
    salary_currency = Column(String(10), default="USD")
    availability = Column(String(50))  # "immediate", "2 weeks", "1 month"
    profile_visibility = Column(String(50), default="public")  # 'public', 'verified_companies', 'private'
    resume_primary_id = Column(String, ForeignKey("resumes.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="personal_profile")
    resume_primary = relationship("Resume", foreign_keys=[resume_primary_id])

    def __repr__(self):
        return f"<PersonalProfile(user_id={self.user_id}, full_name={self.full_name})>"


class CompanyProfile(Base):
    """Profile for company accounts."""
    __tablename__ = "company_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    company_name = Column(String(255), nullable=False)
    logo_url = Column(String(512))
    industry = Column(String(100))
    company_size = Column(String(50))  # "1-10", "11-50", "51-200", etc.
    locations = Column(JSON, default=list)  # [{city, state, country, is_hq}]
    website = Column(String(512))
    description = Column(Text)
    mission = Column(Text)
    culture = Column(Text)
    benefits = Column(JSON, default=list)  # ["Health Insurance", "Remote Work", "401k"]
    team_photos = Column(JSON, default=list)  # [{url, caption}]
    founded_year = Column(Integer)
    verification_status = Column(String(50), default="unverified")  # 'unverified', 'pending', 'verified'
    verification_docs_url = Column(String(512))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="company_profile")

    def __repr__(self):
        return f"<CompanyProfile(user_id={self.user_id}, company_name={self.company_name})>"


# Resume Management
class Resume(Base):
    """Resume files uploaded by users."""
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_size = Column(Integer)  # in bytes
    version_name = Column(String(255), default="Main Resume")
    is_primary = Column(Boolean, default=False)
    parsed_data = Column(JSON, default=dict)  # extracted data
    raw_text = Column(Text)  # full text extracted
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


# Job Management
class Job(Base):
    """Job postings by companies."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=dict)  # {skills: [], experience_min: int, education: []}
    location = Column(String(255))
    remote_type = Column(String(50), default="onsite")  # 'remote', 'hybrid', 'onsite'
    employment_type = Column(String(50), default="full-time")  # 'full-time', 'part-time', 'contract', 'internship'
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10), default="USD")
    screening_questions = Column(JSON, default=list)  # [{question: "...", required: bool}]
    status = Column(String(50), default="draft")  # 'draft', 'active', 'closed'
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    company = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, company_id={self.company_id})>"


# Application System
class Application(Base):
    """Job applications from users."""
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    cover_letter = Column(Text)
    status = Column(String(50), default="pending")  # 'pending', 'screening', 'interview', 'offer', 'hired', 'rejected'
    match_score = Column(Float)  # DECIMAL(5,2) equivalent
    match_explanation = Column(JSON, default=dict)
    rejection_reason = Column(Text)
    applied_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint to prevent duplicate applications
    __table_args__ = (
        UniqueConstraint('job_id', 'user_id', name='unique_job_user_application'),
    )

    # Relationships
    job = relationship("Job", back_populates="applications")
    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.id}, job_id={self.job_id}, user_id={self.user_id}, status={self.status})>"


# Following System
class Follow(Base):
    """User following relationships."""
    __tablename__ = "follows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_type = Column(String(50), nullable=False)  # 'user' or 'company'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate follows
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', 'following_type', name='unique_follow'),
    )

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="follows_as_follower")
    following = relationship("User", foreign_keys=[following_id], back_populates="follows_as_following")

    def __repr__(self):
        return f"<Follow(follower_id={self.follower_id}, following_id={self.following_id})>"


# Notifications
class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'application', 'message', 'job', 'follow', 'interview'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(512))  # URL to relevant page
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"


# Messaging System
class Conversation(Base):
    """Message conversations between users."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    participant_1_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_2_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_message_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint for conversations
    __table_args__ = (
        UniqueConstraint('participant_1_id', 'participant_2_id', name='unique_conversation'),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, p1={self.participant_1_id}, p2={self.participant_2_id})>"


class Message(Base):
    """Individual messages in conversations."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    conversation = relationship("Conversation")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"


# Indexes for performance
Index('idx_users_account_type', User.account_type)
Index('idx_personal_profiles_user_id', PersonalProfile.user_id)
Index('idx_company_profiles_user_id', CompanyProfile.user_id)
Index('idx_company_profiles_verification', CompanyProfile.verification_status)
Index('idx_resumes_user_id', Resume.user_id)
Index('idx_resumes_primary_per_user', Resume.user_id, unique=True, postgresql_where=Resume.is_primary == True)
Index('idx_jobs_company_id', Job.company_id)
Index('idx_jobs_status', Job.status)
Index('idx_jobs_created_at', Job.created_at.desc())
Index('idx_applications_job_id', Application.job_id)
Index('idx_applications_user_id', Application.user_id)
Index('idx_applications_status', Application.status)
Index('idx_follows_follower', Follow.follower_id)
Index('idx_follows_following', Follow.following_id)
Index('idx_notifications_user_id', Notification.user_id)
Index('idx_notifications_is_read', Notification.is_read)
Index('idx_messages_conversation', Message.conversation_id)
Index('idx_messages_sender', Message.sender_id)
