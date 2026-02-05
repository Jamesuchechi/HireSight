from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.interviews.models import Interview, InterviewVideoSession
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.accounts.models import CompanyProfile

User = get_user_model()

class VideoInterviewTests(TestCase):
    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(
            email='recruiter@example.com', 
            password='password123',
            account_type='company'
        )
        self.candidate_user = User.objects.create_user(
            email='candidate@example.com', 
            password='password123',
            account_type='personal'
        )
        
        # Create profile and job
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            name="Test Corp"
        )
        self.job = Job.objects.create(
            company=self.company_profile,
            title="Developer"
        )
        
        # Create application
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.candidate_user
        )
        
        # Create Interview with in-app video
        self.interview = Interview.objects.create(
            application=self.application,
            interview_type=Interview.InterviewType.VIDEO,
            use_inapp_video=True,
            scheduled_date=timezone.now() + timedelta(days=1),
            interviewer_name="Recruiter",
            interviewer_email="recruiter@example.com",
            created_by=self.company_user
        )

    def test_model_validation(self):
        """Test that validation allows empty video_link if use_inapp_video is True"""
        self.interview.full_clean()  # Should not raise validation error
        
        # Test default creation of session
        session, created = InterviewVideoSession.objects.get_or_create(
            interview=self.interview,
            defaults={'room_name': 'test_room'}
        )
        self.assertTrue(created)
        self.assertEqual(session.interview, self.interview)

    def test_view_access_company(self):
        """Test that company user can access the room"""
        self.client.force_login(self.company_user)
        url = reverse('interviews:room', args=[self.interview.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join Room')
    
    def test_view_access_candidate(self):
        """Test that candidate user can access the room"""
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:room', args=[self.interview.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join Room')

    def test_view_access_denied(self):
        """Test that random user cannot access the room"""
        other_user = User.objects.create_user(email='other@example.com', password='pw')
        self.client.force_login(other_user)
        url = reverse('interviews:room', args=[self.interview.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # Assuming AccessMixin returns 403 or redirects
