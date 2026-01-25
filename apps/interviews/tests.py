from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from apps.accounts.models import User
from apps.jobs.models import Job, JobStatus, RemoteType, EmploymentType, ExperienceLevel
from apps.applications.models import Application, ApplicationStatus
from .models import (
    Interview,
    InterviewPracticeSession,
    PracticeQuestion,
    PracticeResponse,
    PracticePerformanceReport
)
from .tasks import (
    generate_practice_questions,
    analyze_practice_response,
    generate_practice_report
)
from .models import (
    InterviewPracticeSession,
    PracticeQuestion,
    PracticeResponse,
    PracticePerformanceReport
)


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
            video_link='https://meet.google.com/test',
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
            video_link='https://meet.google.com/test',
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
            video_link='https://meet.google.com/test',
        )
        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse('interviews:upcoming'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interview')


class PracticeTaskTests(TestCase):
    def setUp(self):
        self.candidate_user = User.objects.create_user(
            email='candidate-practice@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='company-practice@example.com',
            password='testpass123',
            account_type='company'
        )
        self.company_profile = self.company_user.company_profile
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Practice Engineer',
            slug='practice-engineer',
            description='Practice job',
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

    @patch('apps.interviews.tasks.ai_generate_questions')
    def test_generate_questions_updates_session(self, mock_generate):
        mock_generate.return_value = [
            {
                'prompt': 'Tell me about leadership.',
                'category': 'Behavioral',
                'difficulty': 'Intermediate',
                'evaluation_criteria': {'clarity': 0.5},
                'request_id': 'req-1'
            }
        ]
        session = InterviewPracticeSession.objects.create(candidate=self.candidate_user)
        generate_practice_questions(session.id)
        session.refresh_from_db()
        self.assertEqual(session.question_generation_state, InterviewPracticeSession.GenerationState.COMPLETED)
        self.assertEqual(session.questions.count(), 1)

    @patch('apps.interviews.tasks.ai_generate_questions')
    def test_generate_questions_handles_empty_result(self, mock_generate):
        mock_generate.return_value = []
        session = InterviewPracticeSession.objects.create(candidate=self.candidate_user)
        generate_practice_questions(session.id)
        session.refresh_from_db()
        self.assertEqual(session.question_generation_state, InterviewPracticeSession.GenerationState.FAILED)

    @patch('apps.interviews.tasks.generate_practice_report.delay')
    @patch('apps.interviews.tasks.ai_score_response')
    def test_analyze_response_triggers_report(self, mock_score, mock_report):
        session = InterviewPracticeSession.objects.create(candidate=self.candidate_user)
        question = PracticeQuestion.objects.create(
            session=session,
            prompt='Sample question',
            evaluation_criteria={}
        )
        response = PracticeResponse.objects.create(question=question, text_response='Answer')
        mock_score.return_value = {
            'score': 88,
            'feedback': 'Well structured',
            'analysis': {'focus': 'steady', 'confidence': 0.8},
            'request_id': 'req-score'
        }
        analyze_practice_response(response.id)
        response.refresh_from_db()
        self.assertEqual(response.ai_score, 88)
        self.assertEqual(response.analysis_status, InterviewPracticeSession.GenerationState.COMPLETED)
        mock_report.assert_called_once()

    @patch('apps.interviews.tasks.ai_summarize_session')
    def test_generate_report_updates_session(self, mock_summarize):
        session = InterviewPracticeSession.objects.create(candidate=self.candidate_user)
        question = PracticeQuestion.objects.create(session=session, prompt='Q', evaluation_criteria={})
        PracticeResponse.objects.create(question=question, ai_score=75)
        mock_summarize.return_value = {
            'overall_score': 76,
            'strengths': ['Detail'],
            'weaknesses': ['Pacing'],
            'recommendations': 'Keep practicing.',
            'request_id': 'req-report'
        }
        generate_practice_report(session.id)
        session.refresh_from_db()
        self.assertEqual(session.status, InterviewPracticeSession.Status.COMPLETED)
        self.assertEqual(session.report_generation_state, InterviewPracticeSession.GenerationState.COMPLETED)
        report = PracticePerformanceReport.objects.get(session=session)
        self.assertEqual(report.ai_request_id, 'req-report')


class PracticeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate_user = User.objects.create_user(
            email='candidate-view@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='company-view@example.com',
            password='testpass123',
            account_type='company'
        )
        self.session = InterviewPracticeSession.objects.create(candidate=self.candidate_user)

    def test_practice_dashboard_personal_access(self):
        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse('interviews:practice_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Practice Interviews')

    def test_practice_dashboard_company_blocked(self):
        self.client.force_login(self.company_user)
        response = self.client.get(reverse('interviews:practice_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_response_analysis_endpoint(self):
        self.client.force_login(self.candidate_user)
        question = PracticeQuestion.objects.create(session=self.session, prompt='Q', evaluation_criteria={})
        response = PracticeResponse.objects.create(question=question)
        payload = {
            'gaze_direction': 'offscreen',
            'head_tilt': 'down',
            'attention_score': 64,
            'analysis': {'focus': 'distracted'}
        }
        res = self.client.post(
            reverse('interviews:practice_response_analysis', kwargs={'response_id': response.id}),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        response.refresh_from_db()
        self.assertEqual(response.gaze_direction, 'offscreen')
        self.assertEqual(response.head_tilt, 'down')
        self.assertEqual(float(response.attention_score), 64.0)
from django.http import JsonResponse
