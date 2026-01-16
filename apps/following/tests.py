from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from .models import Follow


class FollowModelTests(TestCase):
    """Test Follow model functionality"""
    
    def setUp(self):
        """Set up test users"""
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            account_type='personal'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            account_type='personal'
        )
        self.company = User.objects.create_user(
            email='company@test.com',
            password='testpass123',
            account_type='company'
        )
    
    def test_follow_creation(self):
        """Test creating a follow relationship"""
        follow = Follow.objects.create(follower=self.user1, followed=self.user2)
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.followed, self.user2)
    
    def test_cannot_follow_self(self):
        """Test that users cannot follow themselves"""
        with self.assertRaises(ValidationError):
            follow = Follow(follower=self.user1, followed=self.user1)
            follow.save()
    
    def test_company_cannot_follow(self):
        """Test that company accounts cannot follow"""
        with self.assertRaises(ValidationError):
            follow = Follow(follower=self.company, followed=self.user1)
            follow.save()
    
    def test_unique_together_constraint(self):
        """Test that same follow cannot be created twice"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.user1, followed=self.user2)
    
    def test_follower_count(self):
        """Test follower count method"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.company, followed=self.user2)
        
        count = Follow.get_follower_count(self.user2)
        self.assertEqual(count, 2)
    
    def test_following_count(self):
        """Test following count method"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.user1, followed=self.company)
        
        count = Follow.get_following_count(self.user1)
        self.assertEqual(count, 2)
    
    def test_mutual_followers(self):
        """Test mutual followers detection"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.user2, followed=self.user1)
        
        is_mutual = Follow.are_mutual_followers(self.user1, self.user2)
        self.assertTrue(is_mutual)
    
    def test_not_mutual_followers(self):
        """Test non-mutual followers"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        
        is_mutual = Follow.are_mutual_followers(self.user1, self.user2)
        self.assertFalse(is_mutual)


class FollowViewTests(TestCase):
    """Test Follow views"""
    
    def setUp(self):
        """Set up test users and client"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            account_type='personal'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            account_type='personal'
        )
    
    def test_follow_toggle_not_logged_in(self):
        """Test that non-logged-in users are redirected"""
        response = self.client.post(
            reverse('following:toggle', kwargs={'user_id': self.user2.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_follow_user(self):
        """Test following a user"""
        self.client.login(email='user1@test.com', password='testpass123')
        response = self.client.post(
            reverse('following:toggle', kwargs={'user_id': self.user2.id})
        )
        
        # Check follow was created
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user1,
                followed=self.user2
            ).exists()
        )
    
    def test_unfollow_user(self):
        """Test unfollowing a user"""
        # Create initial follow
        Follow.objects.create(follower=self.user1, followed=self.user2)
        
        self.client.login(email='user1@test.com', password='testpass123')
        response = self.client.post(
            reverse('following:toggle', kwargs={'user_id': self.user2.id})
        )
        
        # Check follow was deleted
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user1,
                followed=self.user2
            ).exists()
        )
    
    def test_following_list_view(self):
        """Test following list view"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        
        self.client.login(email='user1@test.com', password='testpass123')
        response = self.client.get(reverse('following:following_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.email)
    
    def test_followers_list_view(self):
        """Test followers list view"""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        
        self.client.login(email='user2@test.com', password='testpass123')
        response = self.client.get(reverse('following:followers_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.email)