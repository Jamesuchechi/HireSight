from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import EmailPreferences, EmailChangeToken
from .forms import EmailPreferencesForm, ChangeEmailForm

User = get_user_model()


class EmailPreferencesModelTest(TestCase):
    """Test the EmailPreferences model."""
    
    def setUp(self):
        """Create test users."""
        self.personal_user = User.objects.create_user(
            email='jobseeker@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            account_type='company'
        )
    
    def test_email_preferences_created_on_user_creation(self):
        """Test that EmailPreferences is automatically created when a user is created."""
        # Create a new user
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123',
            account_type='personal'
        )
        
        # Check that EmailPreferences was created
        self.assertTrue(hasattr(new_user, 'email_preferences'))
        self.assertIsNotNone(new_user.email_preferences)
    
    def test_email_preferences_has_unsubscribe_token(self):
        """Test that EmailPreferences has a unique unsubscribe token."""
        prefs = self.personal_user.email_preferences
        self.assertIsNotNone(prefs.unsubscribe_token)
        self.assertGreater(len(prefs.unsubscribe_token), 20)
    
    def test_email_preferences_default_frequency(self):
        """Test that default email frequency is 'instant'."""
        prefs = self.personal_user.email_preferences
        self.assertEqual(prefs.email_frequency, 'instant')
    
    def test_email_preferences_default_notifications_enabled(self):
        """Test that notifications are enabled by default for new users."""
        prefs = self.personal_user.email_preferences
        
        # Check personal account notifications
        self.assertTrue(prefs.notify_new_application)
        self.assertTrue(prefs.notify_application_status_changed)
        self.assertTrue(prefs.notify_new_message)
        self.assertTrue(prefs.notify_profile_viewed)
        self.assertTrue(prefs.notify_new_follower)
    
    def test_get_enabled_notifications_personal(self):
        """Test get_enabled_notifications for personal account."""
        prefs = self.personal_user.email_preferences
        enabled = prefs.get_enabled_notifications()
        
        # Should include personal account notification types
        self.assertIn('new_application', enabled)
        self.assertIn('application_status_changed', enabled)
        self.assertIn('new_message', enabled)
        
        # Should not include company notification types
        self.assertNotIn('new_applicant', enabled)
    
    def test_get_enabled_notifications_company(self):
        """Test get_enabled_notifications for company account."""
        prefs = self.company_user.email_preferences
        enabled = prefs.get_enabled_notifications()
        
        # Should include company account notification types
        self.assertIn('new_applicant', enabled)
        self.assertIn('screening_complete', enabled)
        
        # Should not include personal notification types
        self.assertNotIn('new_application', enabled)
    
    def test_should_send_notification_enabled(self):
        """Test should_send_notification when notification is enabled."""
        prefs = self.personal_user.email_preferences
        prefs.notify_new_message = True
        prefs.save()
        
        self.assertTrue(prefs.should_send_notification('new_message'))
    
    def test_should_send_notification_disabled(self):
        """Test should_send_notification when notification is disabled."""
        prefs = self.personal_user.email_preferences
        prefs.notify_new_message = False
        prefs.save()
        
        self.assertFalse(prefs.should_send_notification('new_message'))
    
    def test_email_frequency_choices(self):
        """Test that email frequency choices are valid."""
        prefs = self.personal_user.email_preferences
        valid_frequencies = ['instant', 'daily', 'weekly', 'off']
        
        for freq in valid_frequencies:
            prefs.email_frequency = freq
            prefs.save()
            self.assertEqual(prefs.email_frequency, freq)


class EmailPreferencesFormTest(TestCase):
    """Test the EmailPreferencesForm."""
    
    def setUp(self):
        """Create test user."""
        self.personal_user = User.objects.create_user(
            email='jobseeker@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            account_type='company'
        )
    
    def test_form_renders_for_personal_account(self):
        """Test that form only shows personal account fields."""
        form = EmailPreferencesForm(instance=self.personal_user.email_preferences)
        form_fields = list(form.fields.keys())
        
        # Should include personal fields
        self.assertIn('notify_new_application', form_fields)
        self.assertIn('notify_profile_viewed', form_fields)
        
        # Should not include company fields
        self.assertNotIn('notify_new_applicant', form_fields)
        self.assertNotIn('notify_screening_complete', form_fields)
    
    def test_form_renders_for_company_account(self):
        """Test that form only shows company account fields."""
        form = EmailPreferencesForm(instance=self.company_user.email_preferences)
        form_fields = list(form.fields.keys())
        
        # Should include company fields
        self.assertIn('notify_new_applicant', form_fields)
        self.assertIn('notify_screening_complete', form_fields)
        
        # Should not include personal fields
        self.assertNotIn('notify_new_application', form_fields)
        self.assertNotIn('notify_profile_viewed', form_fields)
    
    def test_form_valid_with_valid_data(self):
        """Test form validation with valid data."""
        form_data = {
            'email_frequency': 'daily',
            'notify_new_application': True,
            'notify_application_status_changed': False,
            'notify_new_message': True,
            'notify_profile_viewed': True,
            'notify_new_follower': False,
            'notify_followed_company_job': True,
            'notify_interview_scheduled': True,
            'notify_job_recommendations': False,
        }
        
        form = EmailPreferencesForm(data=form_data, instance=self.personal_user.email_preferences)
        self.assertTrue(form.is_valid())
    
    def test_form_saves_data(self):
        """Test that form saves preferences correctly."""
        form_data = {
            'email_frequency': 'weekly',
            'notify_new_application': False,
            'notify_application_status_changed': True,
            'notify_new_message': False,
            'notify_profile_viewed': False,
            'notify_new_follower': True,
            'notify_followed_company_job': False,
            'notify_interview_scheduled': True,
            'notify_job_recommendations': False,
        }
        
        form = EmailPreferencesForm(data=form_data, instance=self.personal_user.email_preferences)
        self.assertTrue(form.is_valid())
        form.save()
        
        # Verify changes were saved
        self.personal_user.email_preferences.refresh_from_db()
        self.assertEqual(self.personal_user.email_preferences.email_frequency, 'weekly')
        self.assertFalse(self.personal_user.email_preferences.notify_new_application)
        self.assertTrue(self.personal_user.email_preferences.notify_application_status_changed)


class EmailPreferencesViewTest(TestCase):
    """Test the EmailPreferences views."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.personal_user = User.objects.create_user(
            email='jobseeker@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            account_type='company'
        )
    
    def test_email_preferences_view_requires_login(self):
        """Test that email preferences view requires authentication."""
        response = self.client.get(reverse('accounts:email_preferences'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_email_preferences_view_accessible_when_logged_in(self):
        """Test that email preferences view is accessible for authenticated users."""
        self.client.force_login(self.personal_user)
        response = self.client.get(reverse('accounts:email_preferences'))
        self.assertEqual(response.status_code, 200)
    
    def test_email_preferences_view_personal_account(self):
        """Test email preferences view for personal account."""
        self.client.force_login(self.personal_user)
        response = self.client.get(reverse('accounts:email_preferences'))
        
        self.assertContains(response, 'Email Preferences')
        self.assertContains(response, 'notify_new_application')
    
    def test_email_preferences_view_company_account(self):
        """Test email preferences view for company account."""
        self.client.force_login(self.company_user)
        response = self.client.get(reverse('accounts:email_preferences'))
        
        self.assertContains(response, 'Email Preferences')
        self.assertContains(response, 'notify_new_applicant')
    
    def test_update_email_preferences_view_post(self):
        """Test updating email preferences via POST."""
        self.client.force_login(self.personal_user)
        
        form_data = {
            'email_frequency': 'weekly',
            'notify_new_application': False,
            'notify_application_status_changed': True,
            'notify_new_message': False,
            'notify_profile_viewed': True,
            'notify_new_follower': False,
            'notify_followed_company_job': True,
            'notify_interview_scheduled': False,
            'notify_job_recommendations': True,
        }
        
        response = self.client.post(
            reverse('accounts:update_email_preferences'),
            data=form_data,
            follow=True
        )
        
        # Should redirect back to email preferences page
        self.assertEqual(response.status_code, 200)
        
        # Verify preferences were updated
        self.personal_user.email_preferences.refresh_from_db()
        self.assertEqual(self.personal_user.email_preferences.email_frequency, 'weekly')
        self.assertFalse(self.personal_user.email_preferences.notify_new_application)
    
    def test_update_email_preferences_success_message(self):
        """Test that success message appears after updating preferences."""
        self.client.force_login(self.personal_user)
        
        form_data = {
            'email_frequency': 'instant',
            'notify_new_application': True,
            'notify_application_status_changed': True,
            'notify_new_message': True,
            'notify_profile_viewed': True,
            'notify_new_follower': True,
            'notify_followed_company_job': True,
            'notify_interview_scheduled': True,
            'notify_job_recommendations': True,
        }
        
        response = self.client.post(
            reverse('accounts:update_email_preferences'),
            data=form_data,
            follow=True
        )
        
        # Check for success message
        messages_list = list(response.context['messages'])
        self.assertTrue(any('preferences' in str(m).lower() for m in messages_list))


class EmailPreferencesIntegrationTest(TestCase):
    """Integration tests for email preferences."""
    
    def setUp(self):
        """Set up test users."""
        self.personal_user = User.objects.create_user(
            email='jobseeker@example.com',
            password='testpass123',
            account_type='personal'
        )
        self.company_user = User.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            account_type='company'
        )
    
    def test_multiple_users_have_independent_preferences(self):
        """Test that each user has independent email preferences."""
        personal_prefs = self.personal_user.email_preferences
        company_prefs = self.company_user.email_preferences
        
        # Update personal user preferences
        personal_prefs.notify_new_message = False
        personal_prefs.save()
        
        # Company user preferences should not be affected
        self.assertTrue(company_prefs.notify_new_applicant)
        
        # Verify personal user's changes
        personal_prefs.refresh_from_db()
        self.assertFalse(personal_prefs.notify_new_message)
    
    def test_unsubscribe_tokens_are_unique(self):
        """Test that each user has a unique unsubscribe token."""
        personal_prefs = self.personal_user.email_preferences
        company_prefs = self.company_user.email_preferences
        
        self.assertNotEqual(
            personal_prefs.unsubscribe_token,
            company_prefs.unsubscribe_token
        )


class EmailChangeTokenModelTest(TestCase):
    """Test the EmailChangeToken model."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_email_change_token_creation(self):
        """Test that EmailChangeToken can be created."""
        token = EmailChangeToken.objects.create(
            user=self.user,
            new_email='new@example.com',
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.new_email, 'new@example.com')
        self.assertEqual(token.token, 'test-token-123')
        self.assertFalse(token.is_expired())
    
    def test_email_change_token_expiration(self):
        """Test token expiration."""
        # Create expired token
        past_time = timezone.now() - timedelta(hours=1)
        token = EmailChangeToken.objects.create(
            user=self.user,
            new_email='new@example.com',
            token='test-token-123',
            expires_at=past_time
        )
        
        self.assertTrue(token.is_expired())
    
    def test_email_change_token_str(self):
        """Test string representation."""
        token = EmailChangeToken.objects.create(
            user=self.user,
            new_email='new@example.com',
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        expected = f"Email change token for {self.user.email} -> new@example.com"
        self.assertEqual(str(token), expected)


class ChangeEmailFormTest(TestCase):
    """Test the ChangeEmailForm."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_form_valid_with_correct_data(self):
        """Test form validation with valid data."""
        form_data = {
            'new_email': 'new@example.com',
            'current_password': 'testpass123'
        }
        
        form = ChangeEmailForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_duplicate_email(self):
        """Test form rejects duplicate email."""
        # Create another user with the email we want to change to
        User.objects.create_user(
            email='new@example.com',
            password='testpass123'
        )
        
        form_data = {
            'new_email': 'new@example.com',
            'current_password': 'testpass123'
        }
        
        form = ChangeEmailForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('new_email', form.errors)
    
    def test_form_invalid_same_email(self):
        """Test form rejects same email."""
        form_data = {
            'new_email': 'test@example.com',  # Same as current
            'current_password': 'testpass123'
        }
        
        form = ChangeEmailForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('new_email', form.errors)
    
    def test_form_invalid_wrong_password(self):
        """Test form rejects wrong password."""
        form_data = {
            'new_email': 'new@example.com',
            'current_password': 'wrongpassword'
        }
        
        form = ChangeEmailForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('current_password', form.errors)


class ChangeEmailViewTest(TestCase):
    """Test the ChangeEmailView."""
    
    def setUp(self):
        """Create test user and client."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_change_email_view_requires_login(self):
        """Test that change email view requires authentication."""
        response = self.client.get(reverse('accounts:change_email'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_change_email_view_accessible_when_logged_in(self):
        """Test that change email view is accessible for authenticated users."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:change_email'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Email Address')
    
    def test_change_email_post_success(self):
        """Test successful email change request."""
        self.client.force_login(self.user)
        
        form_data = {
            'new_email': 'new@example.com',
            'current_password': 'testpass123'
        }
        
        response = self.client.post(reverse('accounts:change_email'), form_data)
        
        # Should redirect back to change email page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:change_email'))
        
        # Should create token
        token = EmailChangeToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(token)
        self.assertEqual(token.new_email, 'new@example.com')
    
    def test_change_email_post_invalid_data(self):
        """Test email change with invalid data."""
        self.client.force_login(self.user)
        
        form_data = {
            'new_email': 'invalid-email',  # Invalid email
            'current_password': 'testpass123'
        }
        
        response = self.client.post(reverse('accounts:change_email'), form_data)
        self.assertEqual(response.status_code, 200)  # Form errors, stays on page
        self.assertContains(response, 'Enter a valid email address')


class ConfirmChangeEmailViewTest(TestCase):
    """Test the ConfirmChangeEmailView."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_confirm_change_email_valid_token(self):
        """Test confirming email change with valid token."""
        # Create token
        token = EmailChangeToken.objects.create(
            user=self.user,
            new_email='new@example.com',
            token='valid-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Confirm change
        response = self.client.get(
            reverse('accounts:confirm_change_email', kwargs={'token': 'valid-token-123'}),
            follow=False  # Don't follow redirects
        )
        
        # Should redirect to settings
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:settings'), fetch_redirect_response=False)
        
        # Email should be updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')
        
        # Token should be deleted
        self.assertFalse(EmailChangeToken.objects.filter(id=token.id).exists())
    
    def test_confirm_change_email_expired_token(self):
        """Test confirming email change with expired token."""
        # Create expired token
        EmailChangeToken.objects.create(
            user=self.user,
            new_email='new@example.com',
            token='expired-token-123',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        # Try to confirm
        response = self.client.get(
            reverse('accounts:confirm_change_email', kwargs={'token': 'expired-token-123'}),
            follow=False
        )
        
        # Should redirect to change email page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:change_email'), fetch_redirect_response=False)
        
        # Email should not be changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@example.com')
    
    def test_confirm_change_email_invalid_token(self):
        """Test confirming email change with invalid token."""
        response = self.client.get(
            reverse('accounts:confirm_change_email', kwargs={'token': 'invalid-token'}),
            follow=False
        )
        
        # Should redirect to change email page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:change_email'), fetch_redirect_response=False)
