from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.accounts.models import CompanyProfile
from apps.jobs.models import Job
from apps.resumes.models import Resume
from .models import ScreeningSession, ScreeningResult, ScreeningCriteria, ScreeningStatus, ScreeningResultStatus
from .ai_matcher import AIScreener


User = get_user_model()


class ScreeningModelTest(TestCase):
    """Test Screening models."""

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
        
        # Create screening session
        self.session = ScreeningSession.objects.create(
            company=self.company_profile,
            job=self.job,
            title='Test Screening Session',
            created_by=self.company_user,
            status=ScreeningStatus.PENDING,
            total_resumes=1,
            processed_resumes=0,
            failed_resumes=0
        )

    def test_screening_session_creation(self):
        """Test screening session creation."""
        self.assertEqual(self.session.company, self.company_profile)
        self.assertEqual(self.session.job, self.job)
        self.assertEqual(self.session.title, 'Test Screening Session')
        self.assertEqual(self.session.created_by, self.company_user)
        self.assertEqual(self.session.status, ScreeningStatus.PENDING)

    def test_screening_session_str(self):
        """Test screening session string representation."""
        self.assertEqual(str(self.session), 'Test Screening Session (Pending)')

    def test_screening_session_properties(self):
        """Test screening session properties."""
        # Test progress percentage
        self.assertEqual(self.session.progress_percentage, 0)
        
        # Test success rate
        self.assertEqual(self.session.success_rate, 0)
        
        # Test failure rate
        self.assertEqual(self.session.failure_rate, 0)

    def test_screening_session_status_methods(self):
        """Test screening session status methods."""
        # Test start_processing
        self.session.start_processing()
        self.assertEqual(self.session.status, ScreeningStatus.PROCESSING)
        
        # Test mark_completed
        self.session.mark_completed()
        self.assertEqual(self.session.status, ScreeningStatus.COMPLETED)
        self.assertIsNotNone(self.session.completed_at)
        
        # Test mark_failed
        self.session.mark_failed()
        self.assertEqual(self.session.status, ScreeningStatus.FAILED)


class ScreeningResultTest(TestCase):
    """Test ScreeningResult model."""

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
        
        # Create screening session
        self.session = ScreeningSession.objects.create(
            company=self.company_profile,
            job=self.job,
            title='Test Screening Session',
            created_by=self.company_user,
            status=ScreeningStatus.COMPLETED
        )
        
        # Create screening result
        self.result = ScreeningResult.objects.create(
            session=self.session,
            resume=self.resume,
            job=self.job,
            match_score=85,
            match_details={
                'skills_match': {'matched_skills': ['python', 'django'], 'match_percentage': 100},
                'experience_match': 0.9,
                'education_match': 1.0,
                'semantic_similarity': 0.85
            },
            status=ScreeningResultStatus.COMPLETED
        )

    def test_screening_result_creation(self):
        """Test screening result creation."""
        self.assertEqual(self.result.session, self.session)
        self.assertEqual(self.result.resume, self.resume)
        self.assertEqual(self.result.job, self.job)
        self.assertEqual(self.result.match_score, 85)
        self.assertEqual(self.result.status, ScreeningResultStatus.COMPLETED)

    def test_screening_result_str(self):
        """Test screening result string representation."""
        self.assertEqual(str(self.result), 'personal@example.com - 85% match')

    def test_screening_result_properties(self):
        """Test screening result properties."""
        # Test skills_match property
        self.assertEqual(self.result.skills_match, {'matched_skills': ['python', 'django'], 'match_percentage': 100})
        
        # Test experience_match property
        self.assertEqual(self.result.experience_match, 0.9)
        
        # Test education_match property
        self.assertEqual(self.result.education_match, 1.0)
        
        # Test semantic_similarity property
        self.assertEqual(self.result.semantic_similarity, 0.85)

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
        # Create users
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='testpass123',
            account_type='company'
        )
        
        # Create profiles
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Test Company',
            industry='Tech'
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
            weight_keywords=0.1
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
            weight_keywords=0.1
        )
        self.assertEqual(criteria.weight_skills, 0.5)
        
        # Invalid weights should raise exception
        with self.assertRaises(Exception):
            ScreeningCriteria.objects.create(
                session=self.session,
                weight_skills=0.8,  # Sum would be > 1.0
                weight_experience=0.3,
                weight_education=0.1,
                weight_keywords=0.1
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