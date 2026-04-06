from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import CompanyProfile
from apps.assessments.models import SkillTest, SkillAssessmentAttempt
from apps.jobs.models import Job
from apps.resumes.models import Resume
from apps.screening.models import (
    ScreeningSession, ScreeningResult, ScreeningCriteria, ScreeningStatus,
    ScreeningResultStatus
)
from apps.screening.services import ApplicationDataService
from apps.screening.tasks import process_resume_screening
from apps.screening.ai_matcher import AIScreener

User = get_user_model()

DEFAULT_SCREENING_WEIGHTS = dict(
    weight_skills=0.3,
    weight_experience=0.2,
    weight_education=0.2,
    weight_keywords=0.1,
    weight_screening_questions=0.1,
    weight_assessments=0.1
)


def create_company_profile(company_name='Test Company'):
    """
    Create a company user and return the associated company profile.

    Since the accounts signal auto-creates a CompanyProfile for company users,
    we only need to inspect the created record rather than inserting a second.
    """
    user = User.objects.create_user(
        email=f'company-{uuid4()}@example.com',
        password='testpass123',
        account_type='company'
    )
    profile, _ = CompanyProfile.objects.get_or_create(
        user=user,
        defaults={
            'company_name': company_name,
            'industry': 'Tech'
        }
    )
    # Ensure the profile reflects the desired name
    if profile.company_name != company_name:
        profile.company_name = company_name
        profile.save(update_fields=['company_name'])
    return user, profile


class ScreeningFlowTests(TestCase):
    """Integration-like tests for the enhanced screening experience."""

    def setUp(self):
        self.company_user, self.company = create_company_profile('HireSight Labs')
        self.candidate_user = User.objects.create_user(
            email=f'candidate-{uuid4()}@example.com',
            password='testing',
            account_type='personal'
        )
        self.job = Job.objects.create(
            company=self.company,
            title='AI Engineer',
            slug='ai-engineer',
            description='Build ML products',
            location='Remote',
            status='active'
        )
        self.resume = Resume.objects.create(
            user=self.candidate_user,
            title='AI Engineer Resume',
            file='resumes/ai.pdf',
            original_filename='ai.pdf',
            status='parsed',
            is_primary=True
        )
        self.application = self._create_application()
        self.session = ScreeningSession.objects.create(
            company=self.company,
            job=self.job,
            title='Flow Session',
            created_by=self.company_user,
            status=ScreeningStatus.PENDING
        )
        ScreeningCriteria.objects.create(
            session=self.session,
            **DEFAULT_SCREENING_WEIGHTS
        )
        self.skill_test = SkillTest.objects.create(
            title='Engineering Fundamentals',
            slug='eng-fund',
            skill_name='engineering',
            description='Core skills validation',
            test_type='STATIC',
            difficulty='INTERMEDIATE'
        )
        setattr(self.skill_test, 'skills_tested', ['engineering', 'python'])
        self.attempt = SkillAssessmentAttempt.objects.create(
            user=self.candidate_user,
            test=self.skill_test,
            status='COMPLETED',
            score=88,
            passed=True,
            completed_at=timezone.now(),
            question_results={},
            answers={},
            frozen_questions=[]
        )

    def _create_application(self):
        return Job.objects.get(id=self.job.id).applications.create(
            applicant=self.candidate_user,
            resume=self.resume,
            screening_answers=[
                {'question': 'Why HireSight?', 'answer': 'I love hiring', 'question_type': 'text'},
                {'question': 'Remote?', 'answer': 'Yes', 'question_type': 'yes_no'}
            ]
        )

    def test_application_data_service_returns_complete_payload(self):
        data = ApplicationDataService.get_application_screening_data(self.application)
        self.assertEqual(data['candidate_info']['email'], self.candidate_user.email)
        self.assertTrue(data['screening_answers'])
        self.assertEqual(len(data['assessment_results']), 1)
        self.assertIn('applied_at', data['application_metadata'])

    def test_evaluate_screening_answers_reflects_quality(self):
        answers = [
            {'question': 'Remote?', 'answer': 'Yes', 'question_type': 'yes_no'},
            {'question': 'Background', 'answer': 'I have 10 years', 'question_type': 'text'}
        ]
        cree = AIScreener.__new__(AIScreener)
        result = cree.evaluate_screening_answers(answers, {
            'expected_answers': {
                'Remote?': {'value': 'Yes'},
                'Background': {'keywords': ['years']}
            }
        })
        self.assertGreater(result['overall_score'], 70)
        self.assertTrue(result['strengths'])

    def test_evaluate_assessments_handles_missing_entries(self):
        screener = AIScreener.__new__(AIScreener)
        assessments = [
            {'test_name': 'Engineering Fundamentals', 'score': 90, 'skills_validated': ['python'], 'passed': True},
            {'test_name': 'Team Fit', 'score': 45, 'skills_validated': ['communication'], 'passed': False}
        ]
        result = screener.evaluate_assessments(assessments, ['python', 'engineering'])
        self.assertEqual(result['tests_taken'], 2)
        self.assertIn('python', result['skills_validated'])
        self.assertIn('engineering', result['skills_missing'])
        self.assertGreater(result['overall_score'], 45)

    @patch('apps.screening.tasks.ResumeParser.parse_content')
    @patch('apps.screening.tasks.default_storage.open')
    @patch('apps.screening.tasks.ai_screener.calculate_match_score')
    def test_process_resume_screening_resume_only(
        self, mock_score, mock_open, mock_parser
    ):
        session = ScreeningSession.objects.create(
            company=self.company,
            job=self.job,
            title='Legacy Session',
            created_by=self.company_user,
            status=ScreeningStatus.PENDING
        )
        criteria = ScreeningCriteria.objects.create(
            session=session,
            **DEFAULT_SCREENING_WEIGHTS
        )
        result = ScreeningResult.objects.create(
            session=session,
            resume=self.resume,
            job=self.job,
            status=ScreeningResultStatus.PENDING,
            file_path='resumes/ai.pdf'
        )
        mock_open.return_value.__enter__.return_value.read.return_value = b'dummy'
        mock_parser.return_value = {'success': True, 'text': 'parsed text'}
        mock_score.return_value = {'match_score': 42, 'match_details': {}, 'screening_answers_analysis': {}, 'assessments_analysis': {}}

        process_resume_screening(None, result.id)
        result.refresh_from_db()
        self.assertEqual(result.status, ScreeningResultStatus.COMPLETED)
        self.assertEqual(result.match_score, 42)

    def test_screening_result_status_methods(self):
        """Test screening result status methods."""
        # Create a new result in PENDING status
        result = ScreeningResult.objects.create(
            session=self.session,
            resume=self.resume,
            job=self.job,
            match_score=75,
            status=ScreeningResultStatus.PENDING
        )
        
        # Test mark_as_processing
        result.mark_as_processing()
        self.assertEqual(result.status, ScreeningResultStatus.PROCESSING)
        
        # Test mark_as_completed
        result.mark_as_completed()
        self.assertEqual(result.status, ScreeningResultStatus.COMPLETED)
        self.assertIsNotNone(result.processed_at)
        
        # Test mark_as_failed
        result.mark_as_failed('Test error')
        self.assertEqual(result.status, ScreeningResultStatus.FAILED)
        self.assertEqual(result.error_message, 'Test error')


class ScreeningCriteriaTest(TestCase):
    """Test ScreeningCriteria model."""

    def setUp(self):
        self.company_user, self.company_profile = create_company_profile('Criteria Co')
        
        # Create job
        self.job = Job.objects.create(
            company=self.company_profile,
            title='Test Job',
            slug='test-job',
            description='Test job description',
            location='Remote',
            status='active'
        )
        
        # Create screening session
        self.session = ScreeningSession.objects.create(
            company=self.company_profile,
            job=self.job,
            title='Test Screening Session',
            created_by=self.company_user,
            status=ScreeningStatus.PENDING
        )
        
        # Create screening criteria
        self.criteria = ScreeningCriteria.objects.create(
            session=self.session,
            required_skills=['python', 'django'],
            nice_to_have_skills=['javascript', 'react'],
            min_experience_years=3,
            required_education=['bachelor'],
            weight_skills=0.4,
            weight_experience=0.3,
            weight_education=0.2,
            weight_keywords=0.1,
            weight_screening_questions=0.0,
            weight_assessments=0.0
        )

    def test_screening_criteria_creation(self):
        """Test screening criteria creation."""
        self.assertEqual(self.criteria.session, self.session)
        self.assertEqual(self.criteria.required_skills, ['python', 'django'])
        self.assertEqual(self.criteria.min_experience_years, 3)
        self.assertEqual(self.criteria.weight_skills, 0.4)

    def test_screening_criteria_str(self):
        """Test screening criteria string representation."""
        self.assertEqual(str(self.criteria), 'Criteria for Test Screening Session')

    def test_screening_criteria_weight_validation(self):
        """Test screening criteria weight validation."""
        # Valid weights (sum to 1.0)
        criteria = ScreeningCriteria.objects.create(
            session=self.session,
            weight_skills=0.5,
            weight_experience=0.3,
            weight_education=0.1,
            weight_keywords=0.1,
            weight_screening_questions=0.0,
            weight_assessments=0.0
        )
        self.assertEqual(criteria.weight_skills, 0.5)
        
        # Invalid weights should raise exception
        with self.assertRaises(Exception):
            ScreeningCriteria.objects.create(
                session=self.session,
                weight_skills=0.8,  # Sum would be > 1.0
                weight_experience=0.3,
                weight_education=0.1,
                weight_keywords=0.1,
                weight_screening_questions=0.0,
                weight_assessments=0.0
            )


class AIScreenerTest(TestCase):
    """Test AI screener functionality."""

    def setUp(self):
        self.screener = AIScreener()
        
        # Sample resume text
        self.resume_text = """
        John Doe
        Senior Python Developer
        
        Skills: Python, Django, JavaScript, React, AWS, SQL
        Experience: 5+ years of Python development, 3 years with Django
        Education: Bachelor of Science in Computer Science
        
        Work Experience:
        - Senior Python Developer at Tech Corp (3 years)
        - Python Developer at Web Solutions (2 years)
        
        Projects:
        - Built scalable web applications using Django and React
        - Developed RESTful APIs with Django REST Framework
        - Deployed applications on AWS using Docker and Kubernetes
        """
        
        # Sample job description
        self.job_description = """
        Senior Python Developer
        
        We are looking for an experienced Python developer with strong Django skills.
        
        Requirements:
        - 5+ years of Python development experience
        - 3+ years of Django experience
        - Experience with RESTful APIs
        - Bachelor's degree in Computer Science or related field
        - AWS experience is a plus
        
        Responsibilities:
        - Develop and maintain web applications using Django
        - Build scalable APIs
        - Collaborate with frontend developers
        - Deploy applications to cloud platforms
        """

    def test_skill_extraction(self):
        """Test skill extraction from text."""
        skills = self.screener.extract_skills(self.resume_text)
        self.assertIn('python', skills)
        self.assertIn('django', skills)
        self.assertIn('javascript', skills)

    def test_experience_extraction(self):
        """Test experience extraction from text."""
        experience = self.screener.extract_experience_years(self.resume_text)
        self.assertIsNotNone(experience)
        self.assertGreater(experience, 0)

    def test_education_extraction(self):
        """Test education extraction from text."""
        education = self.screener.extract_education_level(self.resume_text)
        self.assertIsNotNone(education)
        self.assertIn('bachelor', education.lower())

    def test_semantic_similarity(self):
        """Test semantic similarity calculation."""
        similarity = self.screener.calculate_semantic_similarity(
            self.resume_text, 
            self.job_description
        )
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)

    def test_skills_match(self):
        """Test skills match calculation."""
        resume_skills = ['python', 'django', 'javascript']
        job_skills = ['python', 'django', 'aws']
        
        match = self.screener.calculate_skills_match(resume_skills, job_skills)
        self.assertEqual(match['match_count'], 2)  # python and django
        self.assertEqual(match['total_required'], 3)
        self.assertGreater(match['match_percentage'], 0)

    def test_experience_match(self):
        """Test experience match calculation."""
        # Test exact match
        score = self.screener.calculate_experience_match(5, 5)
        self.assertEqual(score, 1.0)
        
        # Test underqualified
        score = self.screener.calculate_experience_match(3, 5)
        self.assertLess(score, 1.0)
        self.assertGreater(score, 0)
        
        # Test overqualified
        score = self.screener.calculate_experience_match(8, 5, 6)
        self.assertLess(score, 1.0)

    def test_education_match(self):
        """Test education match calculation."""
        # Test exact match
        score = self.screener.calculate_education_match('bachelor', ['bachelor'])
        self.assertEqual(score, 1.0)
        
        # Test overqualified
        score = self.screener.calculate_education_match('master', ['bachelor'])
        self.assertEqual(score, 1.0)
        
        # Test underqualified
        score = self.screener.calculate_education_match('associate', ['bachelor'])
        self.assertLess(score, 1.0)

    def test_keyword_match(self):
        """Test keyword match calculation."""
        keywords = ['django', 'rest', 'api']
        score = self.screener.calculate_keyword_match(self.resume_text, keywords)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1)

    def test_match_score_calculation(self):
        """Test comprehensive match score calculation."""
        criteria = {
            'required_skills': ['python', 'django'],
            'min_experience_years': 3,
            'required_education': ['bachelor']
        }
        
        result = self.screener.calculate_match_score(
            self.resume_text, 
            self.job_description, 
            criteria
        )
        
        self.assertIn('match_score', result)
        self.assertIn('match_details', result)
        self.assertGreaterEqual(result['match_score'], 0)
        self.assertLessEqual(result['match_score'], 100)

    def test_match_explanation(self):
        """Test match explanation generation."""
        result = self.screener.calculate_match_score(
            self.resume_text, 
            self.job_description
        )
        
        explanation = self.screener.generate_match_explanation(result)
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)
        self.assertIn('match', explanation.lower())


class ScreeningManagerTest(TestCase):
    """Test Screening managers."""

    def setUp(self):
        # Create users
        self.company_user, self.company_profile = create_company_profile('Manager Co')
        self.personal_user = User.objects.create_user(
            email=f'personal-{uuid4()}@example.com',
            password='testpass123',
            account_type='personal'
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
        
        # Create screening sessions
        self.session1 = ScreeningSession.objects.create(
            company=self.company_profile,
            job=self.job,
            title='Session 1',
            created_by=self.company_user,
            status=ScreeningStatus.COMPLETED
        )
        
        self.session2 = ScreeningSession.objects.create(
            company=self.company_profile,
            job=self.job,
            title='Session 2',
            created_by=self.company_user,
            status=ScreeningStatus.PROCESSING
        )
        
        # Create screening results
        self.result1 = ScreeningResult.objects.create(
            session=self.session1,
            resume=self.resume,
            job=self.job,
            match_score=85,
            status=ScreeningResultStatus.COMPLETED
        )
        
        self.result2 = ScreeningResult.objects.create(
            session=self.session1,
            resume=self.resume,
            job=self.job,
            match_score=92,
            status=ScreeningResultStatus.COMPLETED,
            is_shortlisted=True
        )

    def test_screening_session_manager(self):
        """Test ScreeningSession manager methods."""
        # Test for_company
        sessions = ScreeningSession.objects.for_company(self.company_profile)
        self.assertEqual(sessions.count(), 2)
        
        # Test completed
        completed = ScreeningSession.objects.completed()
        self.assertEqual(completed.count(), 1)
        
        # Test in_progress
        in_progress = ScreeningSession.objects.in_progress()
        self.assertEqual(in_progress.count(), 1)

    def test_screening_result_manager(self):
        """Test ScreeningResult manager methods."""
        # Test for_session
        results = ScreeningResult.objects.for_session(self.session1)
        self.assertEqual(results.count(), 2)
        
        # Test completed
        completed = ScreeningResult.objects.completed()
        self.assertEqual(completed.count(), 2)
        
        # Test high_matches
        high_matches = ScreeningResult.objects.high_matches(threshold=90)
        self.assertEqual(high_matches.count(), 1)
        
        # Test by_resume
        by_resume = ScreeningResult.objects.by_resume(self.resume)
        self.assertEqual(by_resume.count(), 2)
