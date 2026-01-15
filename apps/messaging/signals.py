# apps/messages/signals.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Message, Conversation


def get_sender_display_name(user):
    if hasattr(user, 'personalprofile') and user.personalprofile.full_name:
        return user.personalprofile.full_name
    if hasattr(user, 'companyprofile') and user.companyprofile.company_name:
        return user.companyprofile.company_name
    return user.email


@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    """
    Send notification when a new message is created
    """
    if not created:
        return
    
    # Get all participants except the sender
    recipients = instance.conversation.participants.exclude(id=instance.sender.id)
    
    for recipient in recipients:
        # Create in-app notification (if you have a notifications app)
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=recipient,
                notification_type='message',
                title='New Message',
                message=f'You have a new message from {instance.sender.email}',
                action_url=settings.SITE_URL + reverse('messaging:conversation_detail', args=[instance.conversation.id]),
                action_text='View Message',
                related_object_id=str(instance.conversation.id)
            )
        except ImportError:
            pass  # Notifications app not available
        
        # Send email notification if user has email notifications enabled
        if hasattr(recipient, 'userprofile') and recipient.userprofile.email_notifications:
            send_message_email_notification(instance, recipient)

    channel_layer = get_channel_layer()
    if channel_layer:
        message_preview = instance.content[:90]
        sender_name = get_sender_display_name(instance.sender)
        async_to_sync(channel_layer.group_send)(
            f"conversation_{instance.conversation.id}",
            {
                "type": "conversation.message",
                "message_id": instance.id,
                "sender_id": instance.sender.id,
                "sender_name": sender_name,
                "preview": message_preview,
            }
        )
        participants = instance.conversation.participants.all()
        for participant in participants:
            unread = instance.conversation.get_unread_count(participant)
            async_to_sync(channel_layer.group_send)(
                f"unread_{participant.id}",
                {
                    "type": "unread.count",
                    "unread_count": unread
                }
            )


def send_message_email_notification(message, recipient):
    """
    Send email notification for new message
    """
    sender_name = get_sender_display_name(message.sender)
    
    subject = f'New message from {sender_name} on HireSight'
    
    context = {
        'recipient': recipient,
        'sender_name': sender_name,
        'message_preview': message.content[:100],
        'conversation_url': f"{settings.SITE_URL}/messages/conversation/{message.conversation.id}/",
    }
    
    html_message = render_to_string('messages/emails/new_message.html', context)
    plain_message = render_to_string('messages/emails/new_message.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't break the flow
        print(f"Failed to send email notification: {e}")


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Update conversation's updated_at timestamp when a new message is added
    """
    if created:
        conversation = instance.conversation
        conversation.save()  # This triggers the auto_now on updated_at


@receiver(m2m_changed, sender=Message.read_by.through)
def handle_message_read_status(sender, instance, action, **kwargs):
    """
    Handle actions when message read status changes
    """
    if action == "post_add":
        # Message was marked as read
        # You can add analytics tracking here
        pass
