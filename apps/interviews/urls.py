from django.urls import path
from . import views

app_name = 'interviews'

urlpatterns = [
    # Interview scheduling
    path(
        'schedule/<uuid:application_id>/',
        views.InterviewScheduleView.as_view(),
        name='schedule'
    ),
    
    # Interview listing
    path(
        '',
        views.InterviewListView.as_view(),
        name='list'
    ),
    path(
        'upcoming/',
        views.UpcomingInterviewsView.as_view(),
        name='upcoming'
    ),
    
    # Interview detail
    path(
        '<uuid:interview_id>/',
        views.InterviewDetailView.as_view(),
        name='detail'
    ),
    
    # Interview actions
    path(
        '<uuid:interview_id>/reschedule/',
        views.InterviewRescheduleView.as_view(),
        name='reschedule'
    ),
    path(
        '<uuid:interview_id>/cancel/',
        views.InterviewCancelView.as_view(),
        name='cancel'
    ),
    path(
        '<uuid:interview_id>/complete/',
        views.InterviewCompleteView.as_view(),
        name='complete'
    ),
    path(
        '<uuid:interview_id>/no-show/',
        views.InterviewNoShowView.as_view(),
        name='no_show'
    ),
    path(
        '<uuid:interview_id>/respond/',
        views.InterviewRespondView.as_view(),
        name='respond'
    ),
    path(
        'bulk-schedule/',
        views.BulkInterviewScheduleView.as_view(),
        name='bulk_schedule'
    ),
    
    # Export and utilities
    path(
        '<uuid:interview_id>/export/',
        views.InterviewCalendarExportView.as_view(),
        name='export'
    ),
    path(
        'stats/',
        views.InterviewStatsView.as_view(),
        name='stats'
    ),
]
