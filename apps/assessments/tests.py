from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.assessments.models import SkillTest

User = get_user_model()


class SkillAssessmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='candidate@test.com', password='test123', account_type='personal')
        self.test = SkillTest.objects.create(
            title='Python Basics',
            skill_name='Python',
            description='Test your Python knowledge',
            test_type='MULTIPLE_CHOICE',
            difficulty='BEGINNER',
            duration_minutes=15,
            passing_score=70,
            questions=[
                {'id': 1, 'type': 'multiple_choice', 'question': '2+2?', 'options': ['3', '4'], 'correct_answer': '1', 'points': 10}
            ]
        )

    def test_browse_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('assessments:browse'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Skill Assessments')
