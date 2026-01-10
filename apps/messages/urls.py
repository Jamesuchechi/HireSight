from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
]