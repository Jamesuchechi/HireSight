import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.resumes.models import Resume
from apps.resumes.advanced_analysis import ResumeComparator, IndustryBenchmarker, OptimizationTracker, AdvancedResumeAdvisor


class AdvancedAnalysisTest(TestCase):
    """Test advanced resume analysis features."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Use force_login to bypass authentication backend issues
        self.client.force_login(self.user)

        # Create test resumes with parsed data
        self.resume1 = Resume.objects.create(
            user=self.user,
            title='Software Engineer Resume',
            original_filename='resume1.pdf',
            status='parsed',
            parsed_text='Experienced software engineer with Python, Django, React skills. 5 years experience.',
            skills=['Python', 'Django', 'React', 'JavaScript'],
            experience_years=5
        )

        self.resume2 = Resume.objects.create(
            user=self.user,
            title='Senior Developer Resume',
            original_filename='resume2.pdf',
            status='parsed',
            parsed_text='Senior developer with Python, Django, React, AWS skills. 8 years experience.',
            skills=['Python', 'Django', 'React', 'AWS', 'Docker'],
            experience_years=8
        )

    def test_resume_comparator(self):
        """Test resume comparison functionality."""
        comparator = ResumeComparator()
        result = comparator.compare_resumes([self.resume1.pk, self.resume2.pk], self.user.id)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['resumes']), 2)
        self.assertIn('common_skills', result)
        self.assertIn('recommendations', result)

    def test_industry_benchmarker(self):
        """Test industry benchmarking."""
        benchmarker = IndustryBenchmarker()
        analysis = {
            'ats': {'overall_score': 75},
            'action_verbs': {'score': 80},
            'keywords': {'density_score': 70},
            'overall_score': 75
        }

        result = benchmarker.benchmark_resume(analysis, 'technology')

        self.assertIn('your_score', result)
        self.assertIn('industry_average', result)
        self.assertIn('performance_gap', result)
        self.assertIn('metrics', result)

    def test_optimization_tracker(self):
        """Test optimization tracking."""
        tracker = OptimizationTracker()

        # Test getting history (should be empty initially)
        history = tracker.get_optimization_history(self.user.id, 30)
        self.assertIn('total_optimizations', history)
        self.assertIn('timeline', history)  # Changed from recent_activity

        # Test getting insights
        insights = tracker.get_user_insights(self.user.id)
        self.assertIn('common_issues', insights)
        self.assertIn('strengths', insights)

    def test_advanced_resume_advisor(self):
        """Test advanced resume advisor."""
        advisor = AdvancedResumeAdvisor()
        user_history = {
            'common_issues': [],
            'strengths': ['Python', 'Django']
        }

        result = advisor.generate_advanced_suggestions(
            self.resume1.parsed_text,
            'Software Engineer position requiring Python and React',
            user_history
        )

        self.assertIn('success', result)
        if result['success']:
            self.assertIn('suggestions', result)

    def test_comparison_view(self):
        """Test resume comparison view."""
        url = reverse('resumes:compare')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resumes/resume_comparison.html')
        self.assertIn('user_resumes', response.context)

    def test_benchmark_view(self):
        """Test industry benchmark view."""
        url = reverse('resumes:benchmark', kwargs={'pk': self.resume1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resumes/resume_benchmark.html')
        self.assertIn('resume', response.context)

    def test_optimization_history_view(self):
        """Test optimization history view."""
        url = reverse('resumes:optimization_history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resumes/optimization_history.html')

    def test_compare_resumes_ajax(self):
        """Test AJAX resume comparison."""
        url = reverse('resumes:compare_run')
        data = {
            'resume_ids[]': [self.resume1.pk, self.resume2.pk]
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('success', response_data)

    def test_benchmark_resume_ajax(self):
        """Test AJAX industry benchmarking."""
        url = reverse('resumes:benchmark_data', kwargs={'pk': self.resume1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('success', response_data)

    def test_advanced_optimize_resume_ajax(self):
        """Test AJAX advanced optimization."""
        url = reverse('resumes:advanced_optimize', kwargs={'pk': self.resume1.pk})
        data = {
            'job_description': 'Software Engineer position'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('success', response_data)