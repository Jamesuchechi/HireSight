import asyncio
import json

from channels.testing import ApplicationCommunicator
from django.test import TransactionTestCase

from apps.accounts.models import User
from apps.messaging.consumers import ConversationConsumer, UnreadConsumer
from apps.messaging.models import Conversation, Message


class MessagingConsumersTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.user1 = User.objects.create_user(email='alice@example.com', password='password123')
        self.user2 = User.objects.create_user(email='bob@example.com', password='password123')
        self.conversation = Conversation.objects.create(subject='Realtime test thread')
        self.conversation.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content='Hello from Bob'
        )

    def tearDown(self):
        self.loop.close()
        super().tearDown()

    def _expect_event(self, communicator, expected_type):
        for _ in range(8):
            try:
                data = self._receive_json(communicator, timeout=2)
            except asyncio.TimeoutError:
                continue
            if data.get('type') == expected_type:
                return data
        self.fail(f"Did not receive event of type {expected_type}")

    def _receive_json(self, communicator, timeout=5):
        while True:
            response = self.loop.run_until_complete(communicator.receive_output(timeout=timeout))
            if response.get('type') == 'websocket.send':
                payload = response.get('text') or response.get('bytes')
                if isinstance(payload, bytes):
                    payload = payload.decode('utf-8')
                return json.loads(payload)
            if response.get('type') == 'websocket.close':
                raise asyncio.TimeoutError

    def test_unread_consumer_initial_count(self):
        scope = {
            "type": "websocket",
            "path": "/ws/messaging/unread/",
            "user": self.user1,
        }
        communicator = ApplicationCommunicator(UnreadConsumer.as_asgi(), scope)
        self.loop.run_until_complete(communicator.send_input({"type": "websocket.connect"}))
        response = self.loop.run_until_complete(communicator.receive_output(timeout=5))
        self.assertEqual(response.get('type'), 'websocket.accept')
        data = self._receive_json(communicator, timeout=2)
        self.assertEqual(data.get('type'), 'unread_count')
        self.assertEqual(data.get('unread_count'), 1)
        self.loop.run_until_complete(communicator.send_input({"type": "websocket.disconnect"}))

    def test_conversation_consumer_emits_read_event(self):
        scope = {
            "type": "websocket",
            "path": f"/ws/messaging/conversation/{self.conversation.id}/",
            "user": self.user1,
            "url_route": {"kwargs": {"conversation_id": str(self.conversation.id)}},
        }
        communicator = ApplicationCommunicator(ConversationConsumer.as_asgi(), scope)
        self.loop.run_until_complete(communicator.send_input({"type": "websocket.connect"}))
        response = self.loop.run_until_complete(communicator.receive_output(timeout=5))
        self.assertEqual(response.get('type'), 'websocket.accept')
        try:
            self._receive_json(communicator, timeout=1)
        except asyncio.TimeoutError:
            pass
        self.loop.run_until_complete(communicator.send_json_to({'type': 'read'}))
        data = self._expect_event(communicator, 'message_read')
        self.assertEqual(data.get('reader_id'), self.user1.id)
        self.assertIn(self.message.id, data.get('message_ids', []))
        self.loop.run_until_complete(communicator.send_input({"type": "websocket.disconnect"}))
