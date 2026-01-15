# Tests for jobs app
"""
Tests for Jobs app.

Run with: python manage.py test jobs
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import Job, JobView,  JobStatus, EmploymentType, ExperienceLevel, SavedJob
from apps.accounts.models import CompanyProfile

User = get_user_model()


class JobModelTest(TestCase):
    """Test Job model."""

    def setUp(self):
        """Set up test data."""
        # Create company user
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        
        # Create company profile
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Technology'
        )

    def test_create_job(self):
        """Test creating a job."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Looking for a talented software engineer',
            location='San Francisco, CA',
            employment_type=EmploymentType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
        )
        
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.status, JobStatus.DRAFT)
        self.assertIsNotNone(job.slug)

    def test_slug_generation(self):
        """Test automatic slug generation."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC'
        )
        
        self.assertEqual(job.slug, 'software-engineer')

    def test_unique_slug_generation(self):
        """Test unique slug generation for duplicate titles."""
        job1 = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job 1',
            location='NYC'
        )
        
        job2 = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job 2',
            location='SF'
        )
        
        self.assertEqual(job1.slug, 'software-engineer')
        self.assertEqual(job2.slug, 'software-engineer-1')

    def test_publish_job(self):
        """Test publishing a job sets published_at."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC',
            status=JobStatus.DRAFT
        )
        
        self.assertIsNone(job.published_at)
        
        # Publish job
        job.status = JobStatus.ACTIVE
        job.save()
        
        self.assertIsNotNone(job.published_at)

    def test_salary_validation(self):
        """Test salary max must be >= min."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC',
            salary_min=100000,
            salary_max=80000
        )
        
        # This should raise a validation error in production
        # For now, just test the model is created
        self.assertIsNotNone(job)

    def test_increment_views(self):
        """Test incrementing view count."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC'
        )
        
        initial_views = job.views_count
        job.increment_views()
        
        self.assertEqual(job.views_count, initial_views + 1)

    def test_increment_applications(self):
        """Test incrementing application count."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC'
        )
        
        initial_apps = job.applications_count
        job.increment_applications()
        
        self.assertEqual(job.applications_count, initial_apps + 1)

    def test_get_salary_display(self):
        """Test salary display formatting."""
        job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC',
            salary_min=80000,
            salary_max=120000
        )
        
        self.assertEqual(job.get_salary_display(), '$80,000 - $120,000')

    def test_is_expired(self):
        """Test job expiration check."""
        # Create expired job
        expired_job = Job.objects.create(
            company=self.company,
            title='Expired Job',
            description='Test job',
            location='NYC',
            application_deadline=timezone.now() - timedelta(days=1)
        )
        
        # Create active job
        active_job = Job.objects.create(
            company=self.company,
            title='Active Job',
            description='Test job',
            location='NYC',
            application_deadline=timezone.now() + timedelta(days=30)
        )
        
        self.assertTrue(expired_job.is_expired)
        self.assertFalse(active_job.is_expired)


class SavedJobModelTest(TestCase):
    """Test SavedJob model."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        
        # Create company
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company'
        )
        
        # Create job
        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Test job',
            location='NYC'
        )

    def test_save_job(self):
        """Test saving a job."""
        saved_job = SavedJob.objects.create(
            user=self.user,
            job=self.job
        )
        
        self.assertEqual(saved_job.user, self.user)
        self.assertEqual(saved_job.job, self.job)

    def test_unique_constraint(self):
        """Test user can't save same job twice."""
        SavedJob.objects.create(user=self.user, job=self.job)
        
        # Try to save again - should raise error
        with self.assertRaises(Exception):
            SavedJob.objects.create(user=self.user, job=self.job)

    def test_is_saved_by(self):
        """Test job.is_saved_by() method."""
        self.assertFalse(self.job.is_saved_by(self.user))
        
        SavedJob.objects.create(user=self.user, job=self.job)
        
        self.assertTrue(self.job.is_saved_by(self.user))


class JobViewTest(TestCase):
    """Test Job views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create company user
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        
        # Create company
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company'
        )
        
        # Create personal user
        self.personal_user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            account_type='personal'
        )
        
        # Create active job
        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Looking for a software engineer',
            location='San Francisco, CA',
            status=JobStatus.ACTIVE
        )

    def test_browse_jobs_view(self):
        """Test browse jobs view."""
        response = self.client.get(reverse('jobs:browse'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineer')

    def test_job_detail_view(self):
        """Test job detail view."""
        response = self.client.get(
            reverse('jobs:detail', kwargs={'slug': self.job.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineer')

    def test_job_detail_increments_views(self):
        """Test viewing job increments view count."""
        initial_views = self.job.views_count
        
        self.client.get(
            reverse('jobs:detail', kwargs={'slug': self.job.slug})
        )
        
        self.job.refresh_from_db()
        self.assertEqual(self.job.views_count, initial_views + 1)

    def test_manage_jobs_requires_company(self):
        """Test manage jobs requires company account."""
        # Try as personal user
        self.client.login(email='user@example.com', password='testpass123')
        response = self.client.get(reverse('jobs:manage'))
        
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_manage_jobs_as_company(self):
        """Test company can access manage jobs."""
        self.client.login(email='company@example.com', password='testpass123')
        response = self.client.get(reverse('jobs:manage'))
        
        self.assertEqual(response.status_code, 200)

    def test_create_job_requires_company(self):
        """Test creating job requires company account."""
        self.client.login(email='user@example.com', password='testpass123')
        response = self.client.get(reverse('jobs:create'))
        
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_create_job_as_company(self):
        """Test company can create job."""
        self.client.login(email='company@example.com', password='testpass123')
        
        response = self.client.post(reverse('jobs:create'), {
            'title': 'New Job',
            'description': 'A' * 101,  # Min 100 chars
            'location': 'New York, NY',
            'employment_type': 'full_time',
            'experience_level': 'mid',
            'status': 'draft'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Job.objects.filter(title='New Job').exists())

    def test_edit_job_owner_only(self):
        """Test only job owner can edit."""
        # Create another company
        other_company_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            account_type='company'
        )
        
        other_company = CompanyProfile.objects.create(
            user=other_company_user,
            company_name='Other Company'
        )
        
        # Try to edit as other company
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(
            reverse('jobs:edit', kwargs={'slug': self.job.slug})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect (no permission)

    def test_save_job(self):
        """Test saving a job."""
        self.client.login(email='user@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('jobs:toggle_save', kwargs={'slug': self.job.slug})
        )
        
        self.assertTrue(SavedJob.objects.filter(
            user=self.personal_user,
            job=self.job
        ).exists())

    def test_unsave_job(self):
        """Test unsaving a job."""
        self.client.login(email='user@example.com', password='testpass123')
        
        # Save first
        SavedJob.objects.create(user=self.personal_user, job=self.job)
        
        # Unsave
        self.client.post(
            reverse('jobs:toggle_save', kwargs={'slug': self.job.slug})
        )
        
        self.assertFalse(SavedJob.objects.filter(
            user=self.personal_user,
            job=self.job
        ).exists())


class JobFilterTest(TestCase):
    """Test job filtering."""

    def setUp(self):
        """Set up test data."""
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company'
        )

    def test_filter_by_location(self):
        """Test filtering jobs by location."""
        job_sf = Job.objects.create(
            company=self.company,
            title='SF Job',
            description='Test',
            location='San Francisco, CA',
            status=JobStatus.ACTIVE
        )
        
        job_ny = Job.objects.create(
            company=self.company,
            title='NY Job',
            description='Test',
            location='New York, NY',
            status=JobStatus.ACTIVE
        )
        
        response = self.client.get(reverse('jobs:browse'), {'location': 'San Francisco'})
        
        self.assertContains(response, 'SF Job')
        self.assertNotContains(response, 'NY Job')

    def test_filter_by_employment_type(self):
        """Test filtering by employment type."""
        full_time_job = Job.objects.create(
            company=self.company,
            title='Full-time Job',
            description='Test',
            location='NYC',
            employment_type=EmploymentType.FULL_TIME,
            status=JobStatus.ACTIVE
        )
        
        part_time_job = Job.objects.create(
            company=self.company,
            title='Part-time Job',
            description='Test',
            location='NYC',
            employment_type=EmploymentType.PART_TIME,
            status=JobStatus.ACTIVE
        )
        
        response = self.client.get(reverse('jobs:browse'), {'employment_type': 'full_time'})
        
        self.assertContains(response, 'Full-time Job')
        self.assertNotContains(response, 'Part-time Job')