# apps/messages/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Max, Prefetch
from django.contrib import messages as django_messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    Conversation, Message, MessageTemplate, 
    BlockedUser, MessageReport, MessageAttachment
)
from .forms import (
    ComposeMessageForm, ReplyMessageForm, MessageTemplateForm,
    MessageReportForm, SearchMessagesForm
)
from apps.accounts.models import User


class InboxView(LoginRequiredMixin, ListView):
    """
    Display all conversations for the logged-in user
    """
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'
    paginate_by = 20

    def get_queryset(self):
        queryset = Conversation.objects.filter(
            participants=self.request.user
        ).exclude(
            archived_by=self.request.user
        ).select_related().prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender').order_by('-timestamp')
            )
        ).annotate(
            last_message_time=Max('messages__timestamp'),
            unread_count=Count(
                'messages',
                filter=~Q(messages__sender=self.request.user) & 
                       ~Q(messages__read_by=self.request.user)
            )
        ).order_by('-last_message_time')

        # Apply search filter
        search_query = self.request.GET.get('query', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(messages__content__icontains=search_query) |
                Q(participants__email__icontains=search_query) |
                Q(participants__personalprofile__full_name__icontains=search_query) |
                Q(participants__companyprofile__company_name__icontains=search_query)
            ).distinct()

        # Apply filter type
        filter_type = self.request.GET.get('filter_type', 'all')
        if filter_type == 'unread':
            queryset = queryset.filter(unread_count__gt=0)
        elif filter_type == 'archived':
            queryset = Conversation.objects.filter(
                participants=self.request.user,
                archived_by=self.request.user
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchMessagesForm(self.request.GET)
        context['total_unread'] = sum(
            conv.unread_count for conv in context['conversations']
        )
        context['active_filter'] = self.request.GET.get('filter_type', 'all')
        context['compose_form'] = ComposeMessageForm(sender=self.request.user)
        if self.request.user.account_type == 'company':
            context['template_options'] = MessageTemplate.objects.filter(
                user=self.request.user,
                is_active=True
            ).order_by('name')
        else:
            context['template_options'] = MessageTemplate.objects.none()
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """
    Display a single conversation with all messages
    """
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related(
                    'sender'
                ).prefetch_related(
                    'attachments',
                    'read_by'
                ).filter(is_deleted=False)
            )
        )

    def get_object(self):
        obj = super().get_object()
        # Mark all messages in this conversation as read
        obj.mark_as_read(self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reply_form'] = ReplyMessageForm()
        context['other_participant'] = self.object.get_other_participant(self.request.user)
        context['is_archived'] = self.object.archived_by.filter(id=self.request.user.id).exists()
        context['last_message'] = self.object.get_last_message()
        context['compose_form'] = ComposeMessageForm(sender=self.request.user)
        if self.request.user.account_type == 'company':
            context['template_options'] = MessageTemplate.objects.filter(
                user=self.request.user,
                is_active=True
            ).order_by('name')
        else:
            context['template_options'] = MessageTemplate.objects.none()
        
        # Paginate messages (show 50 per page, load more with AJAX)
        messages_list = self.object.messages.all()
        paginator = Paginator(messages_list, 50)
        default_page = paginator.num_pages or 1
        requested_page = self.request.GET.get('page')
        page_number = requested_page if requested_page else default_page
        context['messages_page'] = paginator.get_page(page_number)
        last_page_message = context['messages_page'].object_list[-1] if context['messages_page'].object_list else None
        context['last_page_message_id'] = last_page_message.id if last_page_message else 0

        # Check if other participant is blocked
        context['is_blocked'] = BlockedUser.objects.filter(
            blocker=self.request.user,
            blocked=context['other_participant']
        ).exists()
        other_participant = context['other_participant']
        for message in context['messages_page']:
            message.is_read_by_other = bool(
                other_participant and message.read_by.filter(id=other_participant.id).exists()
            )
        
        return context

    def post(self, request, *args, **kwargs):
        """Handle reply form submission"""
        self.object = self.get_object()
        form = ReplyMessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = self.object
            message.sender = request.user
            message.save()
            
            # Handle attachment if provided
            attachment = form.cleaned_data.get('attachment')
            if attachment:
                MessageAttachment.objects.create(
                    message=message,
                    file=attachment,
                    filename=attachment.name,
                    file_type=attachment.content_type,
                    file_size=attachment.size
                )
            
            # Update conversation timestamp
            self.object.updated_at = timezone.now()
            self.object.save()
            
            django_messages.success(request, "Message sent successfully!")
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message_id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat()
                })
            
            return redirect('messaging:conversation_detail', pk=self.object.pk)
        
        # If form invalid
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        
        context = self.get_context_data()
        context['reply_form'] = form
        return render(request, self.template_name, context)



class ComposeMessageView(LoginRequiredMixin, CreateView):
    """
    Create a new conversation and send the first message
    """
    model = Message
    form_class = ComposeMessageForm
    template_name = 'messaging/compose.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['sender'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill recipient if provided in URL
        recipient_id = self.request.GET.get('recipient')
        if recipient_id:
            try:
                initial['recipient'] = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        recipient = form.cleaned_data['recipient']
        subject = form.cleaned_data.get('subject', '')
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=self.request.user
        ).filter(
            participants=recipient
        ).first()
        
        if existing_conversation:
            # Use existing conversation
            conversation = existing_conversation
        else:
            # Create new conversation
            conversation = Conversation.objects.create(subject=subject)
            conversation.participants.add(self.request.user, recipient)
        
        # Create the message
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = self.request.user
        message.save()
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        django_messages.success(self.request, "Message sent successfully!")
        return redirect('messaging:conversation_detail', pk=conversation.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get suggested recipients (recent conversations, followed companies, etc.)
        recent_conversations = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants').order_by('-updated_at')[:5]
        
        recent_recipients = []
        for conv in recent_conversations:
            other = conv.get_other_participant(self.request.user)
            if other:
                recent_recipients.append(other)
        
        context['recent_recipients'] = recent_recipients
        if self.request.user.account_type == 'company':
            context['template_options'] = MessageTemplate.objects.filter(
                user=self.request.user,
                is_active=True
            ).order_by('name')
        else:
            context['template_options'] = MessageTemplate.objects.none()
        return context


class ArchiveConversationView(LoginRequiredMixin, View):
    """
    Archive a conversation for the current user
    """
    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk=pk,
            participants=request.user
        )
        
        conversation.archived_by.add(request.user)
        django_messages.success(request, "Conversation archived successfully!")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('messaging:inbox')


class UnarchiveConversationView(LoginRequiredMixin, View):
    """
    Unarchive a conversation for the current user
    """
    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk=pk,
            participants=request.user
        )
        
        conversation.archived_by.remove(request.user)
        django_messages.success(request, "Conversation restored to inbox!")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('messaging:inbox')


class DeleteConversationView(LoginRequiredMixin, DeleteView):
    """
    Delete a conversation (removes user from participants)
    """
    model = Conversation
    success_url = reverse_lazy('messaging:inbox')

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def delete(self, request, *args, **kwargs):
        conversation = self.get_object()
        conversation.participants.remove(request.user)
        
        # If no participants left, delete the conversation
        if conversation.participants.count() == 0:
            conversation.delete()
        
        django_messages.success(request, "Conversation deleted successfully!")
        return redirect(self.success_url)


class MarkAsReadView(LoginRequiredMixin, View):
    """
    Mark specific message or all messages in conversation as read
    """
    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk=pk,
            participants=request.user
        )
        
        conversation.mark_as_read(request.user)
        channel_layer = get_channel_layer()
        if channel_layer:
            unread_count = conversation.get_unread_count(request.user)
            async_to_sync(channel_layer.group_send)(
                f"unread_{request.user.id}",
                {
                    "type": "unread.count",
                    "unread_count": unread_count
                }
            )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'unread_count': 0
            })
        
        return redirect('messaging:conversation_detail', pk=pk)


# ==================== MESSAGE TEMPLATES (Company Users Only) ====================

class MessageTemplateListView(LoginRequiredMixin, ListView):
    """
    List all message templates for company users
    """
    model = MessageTemplate
    template_name = 'messaging/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if request.user.account_type != 'company':
            return HttpResponseForbidden("Only company accounts can access templates")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return MessageTemplate.objects.filter(
            user=self.request.user
        ).order_by('category', '-usage_count')


class MessageTemplateCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new message template
    """
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'messaging/template_form.html'
    success_url = reverse_lazy('messaging:template_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.account_type != 'company':
            return HttpResponseForbidden("Only company accounts can create templates")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        django_messages.success(self.request, "Template created successfully!")
        return super().form_valid(form)


class MessageTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing message template
    """
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'messaging/template_form.html'
    success_url = reverse_lazy('messaging:template_list')

    def get_queryset(self):
        return MessageTemplate.objects.filter(user=self.request.user)

    def form_valid(self, form):
        django_messages.success(self.request, "Template updated successfully!")
        return super().form_valid(form)


class MessageTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a message template
    """
    model = MessageTemplate
    success_url = reverse_lazy('messaging:template_list')

    def get_queryset(self):
        return MessageTemplate.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        django_messages.success(request, "Template deleted successfully!")
        return super().delete(request, *args, **kwargs)


class UseTemplateView(LoginRequiredMixin, View):
    """
    Load a template for use in composing a message
    """
    def get(self, request, template_id):
        template = get_object_or_404(
            MessageTemplate,
            id=template_id,
            user=request.user
        )
        
        # Increment usage count
        template.increment_usage()
        
        return JsonResponse({
            'status': 'success',
            'subject': template.subject,
            'content': template.content
        })


# ==================== BLOCK / REPORT FUNCTIONALITY ====================

class BlockUserView(LoginRequiredMixin, View):
    """
    Block a user from sending messages
    """
    def post(self, request, user_id):
        user_to_block = get_object_or_404(User, id=user_id)
        
        if user_to_block == request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'You cannot block yourself'
            }, status=400)
        
        BlockedUser.objects.get_or_create(
            blocker=request.user,
            blocked=user_to_block,
            defaults={'reason': request.POST.get('reason', '')}
        )
        
        django_messages.success(request, f"{user_to_block.email} has been blocked")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('messaging:inbox')


class UnblockUserView(LoginRequiredMixin, View):
    """
    Unblock a previously blocked user
    """
    def post(self, request, user_id):
        user_to_unblock = get_object_or_404(User, id=user_id)
        
        BlockedUser.objects.filter(
            blocker=request.user,
            blocked=user_to_unblock
        ).delete()
        
        django_messages.success(request, f"{user_to_unblock.email} has been unblocked")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('messaging:inbox')


class ReportMessageView(LoginRequiredMixin, CreateView):
    """
    Report an inappropriate message
    """
    model = MessageReport
    form_class = MessageReportForm
    template_name = 'messaging/report_form.html'
    success_url = reverse_lazy('messaging:inbox')

    def form_valid(self, form):
        message_id = self.kwargs.get('message_id')
        message = get_object_or_404(Message, id=message_id)
        
        # Ensure user is part of the conversation
        if self.request.user not in message.conversation.participants.all():
            return HttpResponseForbidden("You cannot report this message")
        
        form.instance.reporter = self.request.user
        form.instance.message = message
        
        django_messages.success(
            self.request,
            "Thank you for your report. We will review it shortly."
        )
        return super().form_valid(form)


# ==================== AJAX / API ENDPOINTS ====================

@login_required
def get_unread_count(request):
    """
    API endpoint to get unread message count
    """
    unread_count = Message.objects.filter(
        conversation__participants=request.user
    ).exclude(
        sender=request.user
    ).exclude(
        read_by=request.user
    ).count()
    
    return JsonResponse({'unread_count': unread_count})


@login_required
def load_more_messages(request, conversation_id):
    """
    Load older messages (pagination)
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    page = request.GET.get('page', 1)
    messages_list = conversation.messages.filter(is_deleted=False).order_by('timestamp')
    paginator = Paginator(messages_list, 50)
    messages_page = paginator.get_page(page)
    
    messages_data = [{
        'id': msg.id,
        'sender': msg.sender.email,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_own': msg.sender == request.user
    } for msg in messages_page]
    
    return JsonResponse({
        'messages': messages_data,
        'has_next': messages_page.has_next(),
        'page': messages_page.number
    })


@login_required
def poll_conversation_messages(request, conversation_id):
    """
    Poll for new messages in a conversation since the provided last message id.
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    last_id = request.GET.get('last_id')
    messages_qs = conversation.messages.filter(is_deleted=False)
    if last_id:
        try:
            last_id_value = int(last_id)
            messages_qs = messages_qs.filter(id__gt=last_id_value)
        except ValueError:
            pass
    messages_qs = messages_qs.order_by('timestamp').prefetch_related('attachments', 'read_by')
    other_participant = conversation.get_other_participant(request.user)

    new_messages = []
    for message in messages_qs:
        message.is_read_by_other = bool(other_participant and message.read_by.filter(id=other_participant.id).exists())
        rendered = render_to_string(
            'messaging/_message_bubble.html',
            {
                'message': message,
                'other_participant': other_participant,
                'conversation': conversation,
            },
            request=request
        )
        new_messages.append({
            'id': message.id,
            'html': rendered
        })

    return JsonResponse({
        'messages': new_messages
    })
