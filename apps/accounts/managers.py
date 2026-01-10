from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    Replaces the default Django username-based authentication.
    """
    
    def create_user(self, email, password=None, account_type='personal', **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: User's email address (required)
            password: User's password (required)
            account_type: 'personal' or 'company' (default: 'personal')
            **extra_fields: Additional fields for the user model
        
        Returns:
            User instance
        
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        # Normalize email (lowercase domain part)
        email = self.normalize_email(email)
        
        # Create user instance
        user = self.model(
            email=email,
            account_type=account_type,
            **extra_fields
        )
        
        # Set password (hashed)
        user.set_password(password)
        
        # Save to database
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        
        Args:
            email: Superuser's email address (required)
            password: Superuser's password (required)
            **extra_fields: Additional fields for the user model
        
        Returns:
            User instance with superuser privileges
        
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        # Set default values for superuser
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('account_type', 'personal')
        
        # Validate superuser fields
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        """
        Get user by email (natural key for authentication).
        
        Args:
            email: User's email address
        
        Returns:
            User instance or None
        """
        return self.get(email__iexact=email)
    
    def personal_users(self):
        """Return queryset of personal (job seeker) users."""
        return self.filter(account_type='personal')
    
    def company_users(self):
        """Return queryset of company (recruiter) users."""
        return self.filter(account_type='company')
    
    def verified_users(self):
        """Return queryset of verified users."""
        return self.filter(is_verified=True)
    
    def active_users(self):
        """Return queryset of active users."""
        return self.filter(is_active=True)