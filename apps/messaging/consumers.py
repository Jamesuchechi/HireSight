import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for live conversation updates, typing indicators and read receipts.
    """

    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation_{self.conversation_id}"

        logger.debug("ConversationConsumer.connect: user=%s conversation_id=%s", self.user, self.conversation_id)
        if not self.user.is_authenticated:
            logger.debug("ConversationConsumer.connect: unauthenticated user, rejecting")
            await self.close()
            return

        self.conversation = await self.get_conversation()
        if not self.conversation:
            logger.warning(
                "ConversationConsumer.connect: no conversation found for user=%s id=%s",
                self.user.id,
                self.conversation_id
            )
            if not self.conversation:
                await self.close()
                return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("ConversationConsumer.connect: accepted connection for conversation=%s", self.conversation.id)
        await self.notify_presence("online")

    async def disconnect(self, code):
        await self.notify_presence("offline")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        command = content.get("type")
        if command == "typing":
            await self.notify_typing("typing")
        elif command == "stop_typing":
            await self.notify_typing("idle")
        elif command == "read":
            await self.mark_conversation_read()

    async def conversation_typing(self, event):
        await self.send_json({
            "type": "typing",
            "sender_id": event.get("sender_id"),
            "status": event.get("status"),
        })

    async def conversation_message(self, event):
        html = await self.render_message_html(event["message_id"])
        await self.send_json({
            "type": "new_message",
            "html": html,
            "message_id": event["message_id"],
            "sender_id": event.get("sender_id"),
            "sender_name": event.get("sender_name"),
            "preview": event.get("preview"),
        })

    async def notify_typing(self, status):
        await self.channel_layer.group_send(self.group_name, {
            "type": "conversation.typing",
            "sender_id": self.user.id,
            "status": status,
        })

    async def mark_conversation_read(self):
        message_ids = await database_sync_to_async(self.conversation.mark_as_read)(self.user)
        unread_count = await database_sync_to_async(
            lambda: self.conversation.get_unread_count(self.user)
        )()
        await self.channel_layer.group_send(
            f"unread_{self.user.id}",
            {
                "type": "unread.count",
                "unread_count": unread_count
            }
        )
        if message_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "conversation.message_read",
                    "message_ids": message_ids,
                    "reader_id": self.user.id,
                }
            )

    async def get_conversation(self):
        return await database_sync_to_async(
            lambda: Conversation.objects.filter(
                id=self.conversation_id,
                participants=self.user
            ).first()
        )()

    async def render_message_html(self, message_id):
        message = await database_sync_to_async(
            lambda: Message.objects.select_related("sender").prefetch_related("attachments").get(id=message_id)
        )()
        request = HttpRequest()
        request.user = self.user
        other = await database_sync_to_async(lambda: self.conversation.get_other_participant(self.user))()
        message.is_read_by_other = bool(other and message.read_by.filter(id=other.id).exists())
        html = await sync_to_async(render_to_string)(
            "messaging/_message_bubble.html",
            {
                "message": message,
                "other_participant": other,
                "conversation": self.conversation,
            },
            request=request
        )
        return html

    async def notify_presence(self, status):
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "conversation.participant_status",
                "participant_id": self.user.id,
                "status": status,
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def conversation_participant_status(self, event):
        await self.send_json({
            "type": "participant_status",
            "participant_id": event.get("participant_id"),
            "status": event.get("status"),
            "timestamp": event.get("timestamp"),
        })

    async def conversation_message_read(self, event):
        await self.send_json({
            "type": "message_read",
            "message_ids": event.get("message_ids", []),
            "reader_id": event.get("reader_id"),
        })


class UnreadConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that pushes unread message counts to the navigation badge.
    """

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f"unread_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_unread_count()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def unread_count(self, event):
        await self.send_json({
            "type": "unread_count",
            "unread_count": event.get("unread_count", 0)
        })

    async def send_unread_count(self):
        count = await database_sync_to_async(lambda: Message.objects.filter(
            conversation__participants=self.user
        ).exclude(
            sender=self.user
        ).exclude(
            read_by=self.user
        ).count())()
        await self.send_json({
            "type": "unread_count",
            "unread_count": count
        })
