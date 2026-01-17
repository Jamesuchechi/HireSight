from django.urls import path
from . import views

app_name = 'interviews'

urlpatterns = [
    path('schedule/<uuid:application_id>/', views.schedule_interview, name='schedule'),
    path('upcoming/', views.upcoming_interviews, name='upcoming'),
    path('<uuid:interview_id>/reschedule/', views.reschedule_interview, name='reschedule'),
    path('<uuid:interview_id>/cancel/', views.cancel_interview, name='cancel'),
    path('<uuid:interview_id>/complete/', views.mark_interview_completed, name='complete'),
]
