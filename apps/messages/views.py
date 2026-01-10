from django.shortcuts import render, get_object_or_404
from .models import Conversation, Message


def inbox(request):
    conversations = Conversation.objects.filter(participants=request.user)
    return render(request, 'messages/inbox.html', {'conversations': conversations})


def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    return render(request, 'messages/conversation.html', {'conversation': conversation, 'messages': messages})