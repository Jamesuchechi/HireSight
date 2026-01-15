from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.messaging.models import Conversation, Message


class MessagingViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='alice@example.com', password='password123')
        self.user2 = User.objects.create_user(email='bob@example.com', password='password123')
        self.conversation = Conversation.objects.create(subject='Test thread')
        self.conversation.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content='Hello there!'
        )

    def test_poll_conversation_messages_returns_new_items(self):
        self.client.force_login(self.user1)
        url = reverse('messaging:poll_conversation', args=[self.conversation.pk])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('messages', data)
        self.assertEqual(len(data['messages']), 1)
        last_id = data['messages'][0]['id']

        next_response = self.client.get(url, {'last_id': last_id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(next_response.status_code, 200)
        self.assertEqual(next_response.json().get('messages'), [])

    def test_unread_count_endpoint_respects_read_status(self):
        self.client.force_login(self.user1)
        unread_url = reverse('messaging:unread_count')
        response = self.client.get(unread_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json().get('unread_count'), 1)

        self.message.read_by.add(self.user1)
        response = self.client.get(unread_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json().get('unread_count'), 0)
