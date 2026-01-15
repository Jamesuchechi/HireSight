# apps/messages/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Main inbox and conversation views
    path('', views.InboxView.as_view(), name='inbox'),
    path('compose/', views.ComposeMessageView.as_view(), name='compose'),
    path('conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    
    # Conversation actions
    path('conversation/<int:pk>/archive/', views.ArchiveConversationView.as_view(), name='archive_conversation'),
    path('conversation/<int:pk>/unarchive/', views.UnarchiveConversationView.as_view(), name='unarchive_conversation'),
    path('conversation/<int:pk>/delete/', views.DeleteConversationView.as_view(), name='delete_conversation'),
    path('conversation/<int:pk>/mark-read/', views.MarkAsReadView.as_view(), name='mark_as_read'),
    
    # Message templates (company only)
    path('templates/', views.MessageTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.MessageTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.MessageTemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.MessageTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<int:template_id>/use/', views.UseTemplateView.as_view(), name='use_template'),
    
    # Block/Report functionality
    path('block/<uuid:user_id>/', views.BlockUserView.as_view(), name='block_user'),
    path('unblock/<uuid:user_id>/', views.UnblockUserView.as_view(), name='unblock_user'),
    path('report/<int:message_id>/', views.ReportMessageView.as_view(), name='report_message'),
    
    # AJAX/API endpoints
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/conversation/<int:conversation_id>/load-more/', views.load_more_messages, name='load_more_messages'),
    path('api/conversation/<int:conversation_id>/poll/', views.poll_conversation_messages, name='poll_conversation'),
]
