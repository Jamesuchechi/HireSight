from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:pk>/', views.notification_detail, name='detail'),
    path('<int:pk>/toggle-read/', views.toggle_read, name='toggle_read'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
]
