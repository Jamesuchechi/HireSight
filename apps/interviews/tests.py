from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.jobs.models import Job, JobStatus, RemoteType, EmploymentType, ExperienceLevel
from apps.applications.models import Application, ApplicationStatus
from .models import Interview


class InterviewModelTests(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.job = Job.objects.create(
            company=self.company_user.company_profile,
            title='Backend Engineer',
            slug='backend-engineer',
            description='Build APIs',
            requirements={},
            location='Remote',
            remote_type=RemoteType.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            status=JobStatus.ACTIVE,
        )
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.candidate_user,
            status=ApplicationStatus.PENDING,
        )

    def test_interview_creation_and_reschedule(self):
        interview = Interview.objects.create(
            application=self.application,
            interview_type=Interview.InterviewType.VIDEO,
            scheduled_date=timezone.now() + timedelta(days=3),
            interviewer_name='Recruiter',
            interviewer_email='recruiter@example.com',
        )
        self.assertEqual(interview.status, Interview.InterviewStatus.SCHEDULED)
        self.assertTrue(interview.can_reschedule())

        interview.original_scheduled_date = interview.scheduled_date
        interview.scheduled_date += timedelta(days=2)
        interview.status = Interview.InterviewStatus.RESCHEDULED
        interview.reschedule_count = 1
        interview.save()
        self.assertEqual(interview.reschedule_count, 1)

    def test_get_end_time(self):
        interview = Interview.objects.create(
            application=self.application,
            interview_type=Interview.InterviewType.VIDEO,
            scheduled_date=timezone.now(),
            duration_minutes=90,
            interviewer_name='Recruiter',
            interviewer_email='recruiter@example.com',
        )
        end_time = interview.get_end_time()
        self.assertEqual((end_time - interview.scheduled_date).seconds, 5400)


class InterviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.job = Job.objects.create(
            company=self.company_user.company_profile,
            title='Backend Engineer',
            slug='backend-engineer',
            description='Build APIs',
            requirements={},
            location='Remote',
            remote_type=RemoteType.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            status=JobStatus.ACTIVE,
        )
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.candidate_user,
            status=ApplicationStatus.PENDING,
        )

    def test_schedule_view_permission(self):
        self.client.force_login(self.company_user)
        url = reverse('interviews:schedule', kwargs={'application_id': self.application.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.candidate_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_upcoming_view(self):
        Interview.objects.create(
            application=self.application,
            interview_type=Interview.InterviewType.VIDEO,
            scheduled_date=timezone.now() + timedelta(days=2),
            interviewer_name='Recruiter',
            interviewer_email='recruiter@example.com',
        )
        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse('interviews:upcoming'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interview')
