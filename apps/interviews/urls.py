from django.urls import path
from . import views
from . import views_ux
from . import privacy_views

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
    
    # Video Interview
    path(
        'room/<uuid:interview_id>/',
        views.InterviewRoomView.as_view(),
        name='room'
    ),
    path(
        'recording/<uuid:interview_id>/upload/',
        views.InterviewRecordingUploadView.as_view(),
        name='upload_recording'
    ),
    path(
        'execute-code/',
        views.execute_code,
        name='execute_code'
    ),
    path(
        'coding-session/<uuid:interview_id>/save/',
        views.save_coding_session,
        name='save_coding_session'
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
    path(
        'practice/',
        views_ux.PracticeHistoryDashboardView.as_view(),
        name='practice_dashboard'
    ),
    path(
        'practice/setup/',
        views_ux.PracticeSetupView.as_view(),
        name='practice_create'
    ),
    path(
        'practice/start/',
        views_ux.PracticeSetupView.as_view(),
        name='start_practice'
    ),
    path(
        'practice/question/<int:question_id>/',
        views.PracticeQuestionView.as_view(),
        name='practice_question'
    ),
    path(
        'practice/session/<int:session_id>/feedback/',
        views.PracticeFeedbackView.as_view(),
        name='practice_feedback'
    ),

    path(
        'practice/response/<int:response_id>/detail/',
        views_ux.PracticeResponseDetailView.as_view(),
        name='practice_response_detail'
    ),
    path(
        'practice/response/<int:response_id>/retry/',
        views_ux.RetryResponseAnalysisView.as_view(),
        name='practice_response_retry'
    ),

    path(
        'practice/session/<int:session_id>/report/',
        views.CachedPracticeReportView.as_view(),
        name='practice_report'
    ),
    path(
        'practice/session/<int:session_id>/report/refresh/',
        views.PracticeReportRefreshView.as_view(),
        name='practice_report_refresh'
    ),
    path(
        'practice/response/<int:response_id>/analysis/',
        views.PracticeResponseAnalysisView.as_view(),
        name='practice_response_analysis'
    ),
    # Chunked video upload endpoint used by practice recording
    path(
        'practice/upload/video/',
        views.PracticeVideoUploadView.as_view(),
        name='practice_upload_video'
    ),
    
    # UX Improvements URLs
    path(
        'practice/setup/',
        views_ux.PracticeSetupView.as_view(),
        name='setup'
    ),
    path(
        'practice/setup/save/',
        views_ux.SaveSessionSetupView.as_view(),
        name='save_session_setup'
    ),
    path(
        'practice/warmup/<int:session_id>/',
        views_ux.WarmupFlowView.as_view(),
        name='warmup'
    ),
    path(
        'practice/warmup/<int:session_id>/complete/',
        views_ux.CompleteWarmupView.as_view(),
        name='complete_warmup'
    ),
    path(
        'practice/warmup/<int:session_id>/status/',
        views_ux.warmup_question_status,
        name='warmup_question_status'
    ),
    path(
        'practice/history/',
        views_ux.PracticeHistoryDashboardView.as_view(),
        name='practice_history'
    ),
    path(
        'practice/session/<uuid:session_id>/progress/',
        views_ux.SessionProgressView.as_view(),
        name='session_progress'
    ),
    path(
        'practice/session/<uuid:session_id>/controls/',
        views_ux.SessionControlsView.as_view(),
        name='session_controls'
    ),
    
    # Privacy and Consent Management
    path(
        'consent/check/',
        privacy_views.ConsentCheckView.as_view(),
        name='consent_check'
    ),
    path(
        'consent/save/',
        privacy_views.SaveConsentView.as_view(),
        name='save_consent'
    ),
    path(
        'consent/history/',
        privacy_views.ConsentHistoryView.as_view(),
        name='consent_history'
    ),
    path(
        'consent/revoke/<str:consent_type>/',
        privacy_views.RevokeConsentView.as_view(),
        name='revoke_consent'
    ),
    path(
        'consent/modal/',
        privacy_views.ConsentModalView.as_view(),
        name='consent_modal'
    ),
    
    # Usage and Analytics
    path(
        'usage/dashboard/',
        privacy_views.AIUsageDashboardView.as_view(),
        name='ai_usage_dashboard'
    ),
    
    # Video Security
    path(
        'video/<uuid:session_id>/<str:video_key>/url/',
        privacy_views.VideoUrlSigningView.as_view(),
        name='video_signed_url'
    ),
]
