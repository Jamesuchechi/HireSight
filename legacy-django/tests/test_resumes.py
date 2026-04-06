"""
Tests for Resume app.

Run with: python manage.py test resumes
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.resumes.models import Resume
from apps.resumes.forms import ResumeUploadForm, ResumeEditForm
import os
import tempfile

User = get_user_model()


class ResumeModelTest(TestCase):
    """Test Resume model."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_resume(self):
        """Test creating a resume."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
            file_size=1024
        )
        
        self.assertEqual(resume.title, 'Test Resume')
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.status, 'uploaded')
        # First resume should be primary automatically
        self.assertTrue(resume.is_primary)

    def test_first_resume_becomes_primary(self):
        """Test that first resume becomes primary automatically."""
        resume = Resume.objects.create(
            user=self.user,
            title='First Resume',
            original_filename='resume.pdf',
        )
        
        # Refresh from database
        resume.refresh_from_db()
        self.assertTrue(resume.is_primary)

    def test_only_one_primary_per_user(self):
        """Test that only one resume can be primary per user."""
        resume1 = Resume.objects.create(
            user=self.user,
            title='Resume 1',
            original_filename='resume1.pdf',
            is_primary=True
        )
        
        resume2 = Resume.objects.create(
            user=self.user,
            title='Resume 2',
            original_filename='resume2.pdf',
            is_primary=True
        )
        
        # Refresh from database
        resume1.refresh_from_db()
        resume2.refresh_from_db()
        
        # Only resume2 should be primary
        self.assertFalse(resume1.is_primary)
        self.assertTrue(resume2.is_primary)

    def test_delete_primary_makes_another_primary(self):
        """Test that deleting primary resume makes another one primary."""
        resume1 = Resume.objects.create(
            user=self.user,
            title='Resume 1',
            original_filename='resume1.pdf',
            is_primary=True
        )
        
        resume2 = Resume.objects.create(
            user=self.user,
            title='Resume 2',
            original_filename='resume2.pdf',
        )
        
        # Delete primary resume
        resume1.delete()
        
        # Resume 2 should become primary
        resume2.refresh_from_db()
        self.assertTrue(resume2.is_primary)

    def test_get_parsed_skills_list(self):
        """Test getting parsed skills as list."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
            skills=['Python', 'Django', 'React']
        )
        
        skills = resume.get_parsed_skills_list()
        self.assertEqual(len(skills), 3)
        self.assertIn('Python', skills)

    def test_mark_as_parsing(self):
        """Test marking resume as parsing."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
        )
        
        resume.mark_as_parsing()
        
        self.assertEqual(resume.status, 'parsing')
        self.assertEqual(resume.parse_attempts, 1)
        self.assertIsNotNone(resume.last_parse_attempt)

    def test_mark_as_parsed(self):
        """Test marking resume as successfully parsed."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
        )
        
        parsed_data = {
            'text': 'Sample resume text',
            'skills': ['Python', 'Django'],
            'experience_years': 5,
            'education': [],
            'contact_info': {'email': 'test@example.com'}
        }
        
        resume.mark_as_parsed(parsed_data)
        
        self.assertEqual(resume.status, 'parsed')
        self.assertEqual(len(resume.skills), 2)
        self.assertEqual(resume.experience_years, 5)
        self.assertIsNotNone(resume.parsed_at)

    def test_mark_as_failed(self):
        """Test marking resume as failed."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
        )
        
        resume.mark_as_failed('Test error')
        
        self.assertEqual(resume.status, 'failed')
        self.assertEqual(resume.error_message, 'Test error')


class ResumeFormTest(TestCase):
    """Test Resume forms."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_resume_upload_form_valid(self):
        """Test valid resume upload form."""
        # Create a larger fake PDF content to pass validation
        file_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF'
        uploaded_file = SimpleUploadedFile(
            'resume.pdf',
            file_content,
            content_type='application/pdf'
        )
        
        form = ResumeUploadForm(
            data={'title': 'My Resume', 'is_primary': True},
            files={'file': uploaded_file},
            user=self.user
        )
        
        self.assertTrue(form.is_valid())

    def test_resume_upload_form_missing_file(self):
        """Test form validation when file is missing."""
        form = ResumeUploadForm(
            data={'title': 'My Resume'},
            files={},
            user=self.user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_resume_upload_form_invalid_extension(self):
        """Test form validation for invalid file extension."""
        file_content = b'invalid file content'
        uploaded_file = SimpleUploadedFile(
            'resume.txt',
            file_content,
            content_type='text/plain'
        )
        
        form = ResumeUploadForm(
            data={'title': 'My Resume'},
            files={'file': uploaded_file},
            user=self.user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_resume_edit_form_duplicate_title(self):
        """Test form validation for duplicate titles."""
        # Create existing resume
        Resume.objects.create(
            user=self.user,
            title='Existing Resume',
            original_filename='resume1.pdf'
        )
        
        # Try to create another with same title
        form = ResumeEditForm(
            data={'title': 'Existing Resume', 'is_primary': False},
            user=self.user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class ResumeViewTest(TestCase):
    """Test Resume views."""

    def setUp(self):
        """Set up test user and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Use force_login to bypass authentication backend issues
        self.client.force_login(self.user)

    def test_resume_list_view(self):
        """Test resume list view."""
        # Create test resumes
        Resume.objects.create(
            user=self.user,
            title='Resume 1',
            original_filename='resume1.pdf'
        )
        Resume.objects.create(
            user=self.user,
            title='Resume 2',
            original_filename='resume2.pdf'
        )
        
        response = self.client.get(reverse('resumes:list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resume 1')
        self.assertContains(response, 'Resume 2')

    def test_resume_list_view_requires_login(self):
        """Test that resume list requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('resumes:list'))
        
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_resume_detail_view(self):
        """Test resume detail view."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf',
            skills=['Python', 'Django']
        )
        
        response = self.client.get(
            reverse('resumes:detail', kwargs={'pk': resume.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Resume')

    def test_user_cannot_view_others_resume(self):
        """Test that users cannot view other users' resumes."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        resume = Resume.objects.create(
            user=other_user,
            title='Other Resume',
            original_filename='resume.pdf'
        )
        
        response = self.client.get(
            reverse('resumes:detail', kwargs={'pk': resume.pk})
        )
        
        self.assertEqual(response.status_code, 404)

    def test_set_primary_resume(self):
        """Test setting resume as primary."""
        resume1 = Resume.objects.create(
            user=self.user,
            title='Resume 1',
            original_filename='resume1.pdf',
            is_primary=True
        )
        
        resume2 = Resume.objects.create(
            user=self.user,
            title='Resume 2',
            original_filename='resume2.pdf',
        )
        
        response = self.client.post(
            reverse('resumes:set_primary', kwargs={'pk': resume2.pk})
        )
        
        # Refresh from database
        resume1.refresh_from_db()
        resume2.refresh_from_db()
        
        self.assertFalse(resume1.is_primary)
        self.assertTrue(resume2.is_primary)

    def test_delete_resume(self):
        """Test deleting resume."""
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            original_filename='resume.pdf'
        )
        
        response = self.client.post(
            reverse('resumes:delete', kwargs={'pk': resume.pk})
        )
        
        self.assertFalse(Resume.objects.filter(pk=resume.pk).exists())


class ResumeManagerTest(TestCase):
    """Test Resume custom manager."""

    def setUp(self):
        """Set up test users and resumes."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

    def test_for_user(self):
        """Test for_user manager method."""
        Resume.objects.create(
            user=self.user1,
            title='User1 Resume',
            original_filename='resume1.pdf'
        )
        Resume.objects.create(
            user=self.user2,
            title='User2 Resume',
            original_filename='resume2.pdf'
        )
        
        user1_resumes = Resume.objects.for_user(self.user1)
        
        self.assertEqual(user1_resumes.count(), 1)
        self.assertEqual(user1_resumes.first().title, 'User1 Resume')

    def test_parsed(self):
        """Test parsed manager method."""
        Resume.objects.create(
            user=self.user1,
            title='Parsed Resume',
            original_filename='resume1.pdf',
            status='parsed'
        )
        Resume.objects.create(
            user=self.user1,
            title='Failed Resume',
            original_filename='resume2.pdf',
            status='failed'
        )
        
        parsed_resumes = Resume.objects.parsed()
        
        self.assertEqual(parsed_resumes.count(), 1)
        self.assertEqual(parsed_resumes.first().title, 'Parsed Resume')

    def test_primary_for_user(self):
        """Test primary_for_user manager method."""
        Resume.objects.create(
            user=self.user1,
            title='Resume 1',
            original_filename='resume1.pdf',
            is_primary=False
        )
        primary_resume = Resume.objects.create(
            user=self.user1,
            title='Primary Resume',
            original_filename='resume2.pdf',
            is_primary=True
        )
        
        result = Resume.objects.primary_for_user(self.user1)
        
        self.assertEqual(result, primary_resume)