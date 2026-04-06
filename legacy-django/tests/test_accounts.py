from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import PersonalProfile, CompanyProfile
from apps.accounts.forms import PersonalProfileForm, CompanyProfileForm
import json


class ProfileEditTests(TestCase):
    """Ensure personal profile edits persist."""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='jobseeker@example.com',
            password='TestPass123!',
            account_type='personal',
        )

    def test_personal_profile_updates_on_save(self):
        """POSTing to the edit view should mutate the profile."""
        self.client.force_login(self.user)

        url = reverse('accounts:edit_personal_profile')
        payload = {
            'full_name': 'Updated Name',
            'headline': 'Senior Engineer',
            'location': 'Remote',
            'phone': '+1234567890',
            'bio': 'Updated bio.',
            'salary_currency': 'USD',
            'salary_expectation_min': '80000',
            'salary_expectation_max': '120000',
            'availability': 'immediate',
            'profile_visibility': 'public',
            'remote_preference': 'remote',
        }

        response = self.client.post(url, payload, follow=True)
        self.user.personal_profile.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('accounts:personal_profile_view', kwargs={'user_id': str(self.user.id)}),
        )
        self.assertEqual(self.user.personal_profile.full_name, 'Updated Name')
        self.assertEqual(self.user.personal_profile.headline, 'Senior Engineer')
        self.assertEqual(self.user.personal_profile.location, 'Remote')
        self.assertEqual(self.user.personal_profile.bio, 'Updated bio.')


class FormValidationTests(TestCase):
    """Test form validation for personal and company profiles."""

    def setUp(self):
        User = get_user_model()
        self.personal_user = User.objects.create_user(
            email='personal@example.com',
            password='TestPass123!',
            account_type='personal',
        )
        self.company_user = User.objects.create_user(
            email='company@example.com',
            password='TestPass123!',
            account_type='company',
        )

    def test_personal_profile_form_validation(self):
        """Test PersonalProfileForm validation."""
        form_data = {
            'full_name': 'John Doe',
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'phone': '+1234567890',
            'bio': 'Experienced developer',
            'salary_expectation_min': '80000',
            'salary_expectation_max': '120000',
            'salary_currency': 'USD',
            'availability': 'immediate',
            'profile_visibility': 'public',
            'remote_preference': 'remote',
        }
        
        form = PersonalProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_personal_profile_form_invalid_data(self):
        """Test PersonalProfileForm with invalid data."""
        form_data = {
            'full_name': '',  # Required field
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'phone': '+1234567890',
            'bio': 'Experienced developer',
            'salary_expectation_min': '80000',
            'salary_expectation_max': '120000',
            'salary_currency': 'USD',
            'availability': 'immediate',
            'profile_visibility': 'public',
            'remote_preference': 'remote',
        }
        
        form = PersonalProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)

    def test_company_profile_form_validation(self):
        """Test CompanyProfileForm validation."""
        form_data = {
            'company_name': 'Tech Corp',
            'industry': 'Technology',
            'company_size': '51-200',
            'website': 'https://techcorp.com',
            'description': 'Innovative tech company',
            'mission': 'Empower businesses with technology',
            'culture': 'Collaborative environment',
            'founded_year': 2010,
            'verification_status': 'unverified',
        }
        
        form = CompanyProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_company_profile_form_invalid_data(self):
        """Test CompanyProfileForm with invalid data."""
        form_data = {
            'company_name': '',  # Required field
            'industry': 'Technology',
            'company_size': '51-200',
            'website': 'https://techcorp.com',
            'description': 'Innovative tech company',
            'mission': 'Empower businesses with technology',
            'culture': 'Collaborative environment',
            'founded_year': 2010,
            'verification_status': 'unverified',
        }
        
        form = CompanyProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)


class JSONPersistenceTests(TestCase):
    """Test JSON field persistence for profile models."""

    def setUp(self):
        User = get_user_model()
        self.personal_user = User.objects.create_user(
            email='json_personal@example.com',
            password='TestPass123!',
            account_type='personal',
        )
        self.company_user = User.objects.create_user(
            email='json_company@example.com',
            password='TestPass123!',
            account_type='company',
        )

    def test_personal_profile_json_fields_persistence(self):
        """Test that JSON fields persist correctly for PersonalProfile."""
        profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='John Doe',
            headline='Software Engineer',
            skills=[
                {'skill': 'Python', 'proficiency': 'expert'},
                {'skill': 'JavaScript', 'proficiency': 'advanced'}
            ],
            experience=[
                {
                    'role': 'Senior Developer',
                    'company': 'Tech Corp',
                    'start_date': '2020-01',
                    'current': True,
                    'description': 'Lead developer'
                }
            ],
            education=[
                {
                    'institution': 'Stanford University',
                    'degree': 'Bachelor of Science',
                    'field': 'Computer Science',
                    'start_year': '2010',
                    'end_year': '2014'
                }
            ],
            certifications=[
                {
                    'name': 'AWS Certified Developer',
                    'issuer': 'Amazon',
                    'date': '2022-05',
                    'url': 'https://aws.amazon.com/certification'
                }
            ],
            portfolio_links=[
                {
                    'type': 'github',
                    'url': 'https://github.com/johndoe'
                }
            ],
            preferred_job_types=['full-time', 'remote']
        )
        
        # Refresh from database
        profile.refresh_from_db()
        
        # Test skills
        self.assertEqual(len(profile.skills), 2)
        self.assertEqual(profile.skills[0]['skill'], 'Python')
        self.assertEqual(profile.skills[0]['proficiency'], 'expert')
        
        # Test experience
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(profile.experience[0]['role'], 'Senior Developer')
        self.assertTrue(profile.experience[0]['current'])
        
        # Test education
        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0]['institution'], 'Stanford University')
        
        # Test certifications
        self.assertEqual(len(profile.certifications), 1)
        self.assertEqual(profile.certifications[0]['name'], 'AWS Certified Developer')
        
        # Test portfolio links
        self.assertEqual(len(profile.portfolio_links), 1)
        self.assertEqual(profile.portfolio_links[0]['type'], 'github')
        
        # Test preferred job types
        self.assertEqual(len(profile.preferred_job_types), 2)
        self.assertIn('full-time', profile.preferred_job_types)

    def test_company_profile_json_fields_persistence(self):
        """Test that JSON fields persist correctly for CompanyProfile."""
        profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Tech Solutions',
            industry='Technology',
            company_size='51-200',
            locations=[
                {
                    'address': '123 Tech Street',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'country': 'USA',
                    'postal_code': '94105',
                    'lat': 37.7749,
                    'lng': -122.4194,
                    'is_hq': True
                }
            ],
            website='https://techsolutions.com',
            description='Innovative technology solutions',
            benefits=['Health Insurance', 'Remote Work', '401k'],
            team_photos=[
                {
                    'url': '/media/team_photo.jpg',
                    'caption': 'Our amazing team'
                }
            ]
        )
        
        # Refresh from database
        profile.refresh_from_db()
        
        # Test locations
        self.assertEqual(len(profile.locations), 1)
        self.assertEqual(profile.locations[0]['city'], 'San Francisco')
        self.assertTrue(profile.locations[0]['is_hq'])
        
        # Test benefits
        self.assertEqual(len(profile.benefits), 3)
        self.assertIn('Health Insurance', profile.benefits)
        self.assertIn('Remote Work', profile.benefits)
        
        # Test team photos
        self.assertEqual(len(profile.team_photos), 1)
        self.assertEqual(profile.team_photos[0]['caption'], 'Our amazing team')


class ViewRenderingTests(TestCase):
    """Test view rendering for profile views."""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        
        # Create personal user (profile will be created by view)
        self.personal_user = User.objects.create_user(
            email='view_personal@example.com',
            password='TestPass123!',
            account_type='personal',
        )
        
        # Create company user (profile will be created by view)
        self.company_user = User.objects.create_user(
            email='view_company@example.com',
            password='TestPass123!',
            account_type='company',
        )

    def test_personal_profile_view_rendering(self):
        """Test that personal profile view renders correctly."""
        # Create profile first
        profile = PersonalProfile.objects.create(
            user=self.personal_user,
            full_name='John Doe',
            headline='Software Engineer',
            location='San Francisco',
            bio='Experienced developer',
            profile_visibility='public'
        )
        
        url = reverse('accounts:personal_profile_view', kwargs={'user_id': str(self.personal_user.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Software Engineer')
        self.assertContains(response, 'San Francisco')
        self.assertContains(response, 'Experienced developer')

    def test_company_profile_view_rendering(self):
        """Test that company profile view renders correctly."""
        url = reverse('accounts:company_profile_view', kwargs={'user_id': str(self.company_user.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tech Solutions')
        self.assertContains(response, 'Technology')
        self.assertContains(response, 'Innovative technology solutions')
        self.assertContains(response, 'San Francisco')

    def test_edit_personal_profile_view_rendering(self):
        """Test that edit personal profile view renders correctly."""
        self.client.force_login(self.personal_user)
        url = reverse('accounts:edit_personal_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Personal Profile')
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Software Engineer')

    def test_edit_company_profile_view_rendering(self):
        """Test that edit company profile view renders correctly."""
        self.client.force_login(self.company_user)
        url = reverse('accounts:edit_company_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Company Profile')
        self.assertContains(response, 'Tech Solutions')
        self.assertContains(response, 'Technology')


class ProfileCompletionTests(TestCase):
    """Test profile completion score calculation."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email='completion_test@example.com',
            password='TestPass123!',
            account_type='personal',
        )

    def test_profile_completion_score_calculation(self):
        """Test that profile completion score is calculated correctly."""
        profile = PersonalProfile.objects.create(
            user=self.user,
            full_name='John Doe',
            headline='Software Engineer',
            location='San Francisco',
            bio='Experienced developer',
            skills=[
                {'skill': 'Python', 'proficiency': 'expert'},
                {'skill': 'JavaScript', 'proficiency': 'advanced'},
                {'skill': 'Django', 'proficiency': 'expert'}
            ],
            experience=[
                {
                    'role': 'Senior Developer',
                    'company': 'Tech Corp',
                    'start_date': '2020-01',
                    'current': True,
                    'description': 'Lead developer'
                }
            ],
            education=[
                {
                    'institution': 'Stanford University',
                    'degree': 'Bachelor of Science',
                    'field': 'Computer Science',
                    'start_year': '2010',
                    'end_year': '2014'
                }
            ],
            certifications=[
                {
                    'name': 'AWS Certified Developer',
                    'issuer': 'Amazon',
                    'date': '2022-05',
                    'url': 'https://aws.amazon.com/certification'
                }
            ],
            portfolio_links=[
                {
                    'type': 'github',
                    'url': 'https://github.com/johndoe'
                }
            ],
            preferred_job_types=['full-time', 'remote'],
            remote_preference='remote',
            salary_expectation_min=100000,
            salary_expectation_max=150000,
            salary_currency='USD',
            availability='immediate',
            profile_visibility='public'
        )
        
        score = profile.calculate_completion_score()
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        
        # Test with minimal profile
        minimal_profile = PersonalProfile.objects.create(
            user=self.user,
            full_name='Jane Doe'
        )
        minimal_score = minimal_profile.calculate_completion_score()
        self.assertGreater(minimal_score, 0)
        self.assertLess(minimal_score, 50)


class JSONFieldUpdateTests(TestCase):
    """Test updating JSON fields through forms and views."""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='json_update_test@example.com',
            password='TestPass123!',
            account_type='personal',
        )
        self.profile = PersonalProfile.objects.create(
            user=self.user,
            full_name='John Doe',
            headline='Software Engineer',
            location='San Francisco',
            bio='Experienced developer',
            profile_visibility='public'
        )

    def test_json_field_updates_via_form(self):
        """Test updating JSON fields through form submission."""
        self.client.force_login(self.user)
        
        url = reverse('accounts:edit_personal_profile')
        
        # Test updating skills via JSON
        skills_json = json.dumps([
            {'skill': 'Python', 'proficiency': 'expert'},
            {'skill': 'JavaScript', 'proficiency': 'advanced'}
        ])
        
        payload = {
            'full_name': 'John Doe',
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'phone': '+1234567890',
            'bio': 'Experienced developer',
            'salary_currency': 'USD',
            'salary_expectation_min': '100000',
            'salary_expectation_max': '150000',
            'availability': 'immediate',
            'profile_visibility': 'public',
            'remote_preference': 'remote',
            'skills_json': skills_json
        }
        
        response = self.client.post(url, payload, follow=True)
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.profile.skills), 2)
        self.assertEqual(self.profile.skills[0]['skill'], 'Python')
        self.assertEqual(self.profile.skills[0]['proficiency'], 'expert')
