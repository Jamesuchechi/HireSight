from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import Job
from apps.resumes.models import Resume
from apps.accounts.models import CompanyProfile, PersonalProfile
from .models import Application, ApplicationStatus, ApplicationNote, ApplicationStatusHistory
from .forms import ApplicationForm, ApplicationReviewForm, ApplicationWithdrawForm
from .validators import validate_status_transition, validate_duplicate_application


User = get_user_model()


class ApplicationModelTest(TestCase):
    """Test Application model functionality."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal'
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )
        
        # Create application
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            cover_letter='Test cover letter',
            status=ApplicationStatus.PENDING
        )

    def test_application_creation(self):
        """Test that application is created correctly."""
        self.assertEqual(self.application.job, self.job)
        self.assertEqual(self.application.applicant, self.personal_user)
        self.assertEqual(self.application.resume, self.resume)
        self.assertEqual(self.application.status, ApplicationStatus.PENDING)
        self.assertEqual(self.application.cover_letter, 'Test cover letter')

    def test_application_str(self):
        """Test application string representation."""
        self.assertEqual(str(self.application), 'personal@example.com applied for Test Job')

    def test_application_status_transition(self):
        """Test status transition validation."""
        # Valid transition
        self.application.update_status(ApplicationStatus.SCREENING, self.company_user)
        self.assertEqual(self.application.status, ApplicationStatus.SCREENING)
        
        # Invalid transition should raise exception
        with self.assertRaises(Exception):
            self.application.update_status(ApplicationStatus.HIRED, self.company_user)

    def test_application_withdrawal(self):
        """Test application withdrawal."""
        # Application can be withdrawn from PENDING status
        self.assertTrue(self.application.can_withdraw)
        
        # Withdraw the application
        self.application.status = ApplicationStatus.WITHDRAWN
        self.application.save()
        
        # Application cannot be withdrawn after withdrawal
        self.assertFalse(self.application.can_withdraw)

    def test_application_properties(self):
        """Test application properties."""
        # Test is_active property
        self.assertTrue(self.application.is_active)
        
        # Test is_terminated property
        self.assertFalse(self.application.is_terminated)
        
        # Test days_since_applied property
        self.assertEqual(self.application.days_since_applied, 0)

    def test_unique_constraint(self):
        """Test unique constraint for job+applicant combination."""
        # Should not be able to create duplicate application
        with self.assertRaises(Exception):
            Application.objects.create(
                job=self.job,
                applicant=self.personal_user,
                resume=self.resume,
                status=ApplicationStatus.PENDING
            )


class ApplicationFormTest(TestCase):
    """Test Application forms."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal',
            is_verified=True
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )

    def test_application_form_valid(self):
        """Test valid application form."""
        form_data = {
            'resume': self.resume.id,
            'cover_letter': 'Test cover letter',
            'portfolio_url': 'https://example.com',
            'screening_answers': {},
            'additional_notes': 'Test notes'
        }
        
        form = ApplicationForm(data=form_data, job=self.job, applicant=self.personal_user)
        self.assertTrue(form.is_valid())

    def test_application_form_duplicate(self):
        """Test duplicate application validation."""
        # Create first application
        Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )
        
        form_data = {
            'resume': self.resume.id,
            'cover_letter': 'Test cover letter'
        }
        
        form = ApplicationForm(data=form_data, job=self.job, applicant=self.personal_user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_application_review_form(self):
        """Test application review form."""
        application = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )
        
        form_data = {
            'status': ApplicationStatus.SCREENING,
            'recruiter_notes': 'Good candidate',
            'rating': 4,
            'is_shortlisted': True,
            'tags': ['python', 'django']
        }
        
        form = ApplicationReviewForm(data=form_data, instance=application, current_user=self.company_user)
        self.assertTrue(form.is_valid())

    def test_withdraw_form(self):
        """Test withdrawal form."""
        application = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )
        
        form_data = {
            'confirmation': True,
            'reason': 'Found another job'
        }
        
        form = ApplicationWithdrawForm(data=form_data, application=application)
        self.assertTrue(form.is_valid())


class ApplicationValidatorTest(TestCase):
    """Test application validators."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal',
            is_verified=True
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )

    def test_status_transition_validation(self):
        """Test status transition validation."""
        # Valid transition
        validate_status_transition(ApplicationStatus.PENDING, ApplicationStatus.SCREENING)
        
        # Invalid transition
        with self.assertRaises(Exception):
            validate_status_transition(ApplicationStatus.PENDING, ApplicationStatus.HIRED)

    def test_duplicate_application_validation(self):
        """Test duplicate application validation."""
        # Create first application
        Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )
        
        # Should raise exception for duplicate
        with self.assertRaises(Exception):
            validate_duplicate_application(self.job, self.personal_user)


class ApplicationManagerTest(TestCase):
    """Test Application manager methods."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal',
            is_verified=True
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )
        
        # Create applications with different statuses
        self.app1 = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )
        
        self.app2 = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.SCREENING,
            match_score=85
        )
        
        self.app3 = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.HIRED
        )

    def test_for_job_manager(self):
        """Test for_job manager method."""
        applications = Application.objects.for_job(self.job)
        self.assertEqual(applications.count(), 3)

    def test_for_applicant_manager(self):
        """Test for_applicant manager method."""
        applications = Application.objects.for_applicant(self.personal_user)
        self.assertEqual(applications.count(), 3)

    def test_active_manager(self):
        """Test active manager method."""
        applications = Application.objects.active()
        self.assertEqual(applications.count(), 2)  # PENDING and SCREENING

    def test_high_priority_manager(self):
        """Test high_priority manager method."""
        applications = Application.objects.high_priority()
        self.assertEqual(applications.count(), 1)  # Only the one with match_score=85

    def test_recent_manager(self):
        """Test recent manager method."""
        applications = Application.objects.recent(days=1)
        self.assertEqual(applications.count(), 3)


class ApplicationNoteTest(TestCase):
    """Test ApplicationNote model."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal',
            is_verified=True
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )
        
        # Create application
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )

    def test_note_creation(self):
        """Test note creation."""
        note = ApplicationNote.objects.create(
            application=self.application,
            author=self.company_user,
            note='Test note content',
            is_important=True
        )
        
        self.assertEqual(note.application, self.application)
        self.assertEqual(note.author, self.company_user)
        self.assertEqual(note.note, 'Test note content')
        self.assertTrue(note.is_important)

    def test_note_str(self):
        """Test note string representation."""
        note = ApplicationNote.objects.create(
            application=self.application,
            author=self.company_user,
            note='Test note content'
        )
        
        self.assertEqual(str(note), f'Note on {self.application} by company@example.com')


class ApplicationStatusHistoryTest(TestCase):
    """Test ApplicationStatusHistory model."""

    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='testpass123',
            account_type='personal',
            is_verified=True
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
        )
        self.personal_profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='Test User'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            user=self.personal_user,
            title='Test Resume',
            file='test.pdf',
            original_filename='test.pdf',
            status='parsed',
            is_primary=True
        )
        
        # Create application
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.personal_user,
            resume=self.resume,
            status=ApplicationStatus.PENDING
        )

    def test_status_history_creation(self):
        """Test status history creation."""
        history = ApplicationStatusHistory.objects.create(
            application=self.application,
            old_status=ApplicationStatus.PENDING,
            new_status=ApplicationStatus.SCREENING,
            changed_by=self.company_user,
            reason='Good candidate',
            notes='Moved to screening'
        )
        
        self.assertEqual(history.application, self.application)
        self.assertEqual(history.old_status, ApplicationStatus.PENDING)
        self.assertEqual(history.new_status, ApplicationStatus.SCREENING)
        self.assertEqual(history.changed_by, self.company_user)
        self.assertEqual(history.reason, 'Good candidate')
        self.assertEqual(history.notes, 'Moved to screening')

    def test_status_history_str(self):
        """Test status history string representation."""
        history = ApplicationStatusHistory.objects.create(
            application=self.application,
            old_status=ApplicationStatus.PENDING,
            new_status=ApplicationStatus.SCREENING,
            changed_by=self.company_user
        )
        
        self.assertEqual(str(history), f'{self.application} status changed from PENDING to SCREENING')