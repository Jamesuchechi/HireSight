"""
URL configuration for screening app.
"""
from django.urls import path
from . import views

app_name = 'screening'

urlpatterns = [
    # Job-Based Screening
    path('jobs/<uuid:job_id>/screen/', views.JobApplicationScreeningView.as_view(), name='screen_job_applicants'),
    path('applications/<uuid:application_id>/screen/', views.ScreenSingleApplicationView.as_view(), name='screen_single_application'),

    # Session Management
    path('sessions/', views.ScreeningSessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.ScreeningSessionCreateView.as_view(), name='session_create'),
    path('sessions/<uuid:session_id>/', views.ScreeningSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<uuid:session_id>/update/', views.ScreeningSessionUpdateView.as_view(), name='session_update'),

    # Criteria Setup
    path('sessions/<uuid:session_id>/criteria/', views.ScreeningCriteriaSetupView.as_view(), name='criteria_setup'),
    path('sessions/<uuid:session_id>/criteria/update/', views.ScreeningCriteriaUpdateView.as_view(), name='criteria_update'),

    # Results & Analysis
    path('sessions/<uuid:session_id>/results/', views.ScreeningResultsView.as_view(), name='results'),
    path('sessions/<uuid:session_id>/export/', views.ScreeningResultExportView.as_view(), name='export'),
    path('sessions/<uuid:session_id>/analytics/', views.ScreeningAnalyticsView.as_view(), name='analytics'),
    path('results/<uuid:result_id>/', views.ScreeningResultDetailView.as_view(), name='result_detail'),

    # Pipeline Integration
    path('sessions/<uuid:session_id>/push-pipeline/', views.PushToPipelineView.as_view(), name='push_pipeline'),
    path('sessions/<uuid:session_id>/bulk-push-pipeline/', views.BulkPushToPipelineView.as_view(), name='bulk_push_pipeline'),
    path('pipeline/status-update/', views.PipelineStatusUpdateView.as_view(), name='pipeline_status_update'),

    # Data Supplementation
    path('sessions/<uuid:session_id>/supplement-resumes/', views.SupplementMissingResumesView.as_view(), name='supplement_resumes'),
    path('sessions/<uuid:session_id>/start-processing/', views.ScreeningSessionStartProcessingView.as_view(), name='start_processing'),

    # Real-Time Progress Tracking
    path('sessions/<uuid:session_id>/progress-updates/', views.ProgressUpdateView.as_view(), name='progress_updates'),
    path('sessions/<uuid:session_id>/stats/', views.SessionStatsView.as_view(), name='session_stats'),
    path('sessions/<uuid:session_id>/create-update/', views.CreateProgressUpdateView.as_view(), name='create_update'),

    # AI Insights
    path('sessions/<uuid:session_id>/generate-insight/', views.GenerateInsightView.as_view(), name='generate_insight'),
    path('sessions/<uuid:session_id>/batch-insights/', views.BatchGenerateInsightView.as_view(), name='batch_insights'),
    path('results/<uuid:result_id>/insights/', views.RetrieveInsightView.as_view(), name='retrieve_insights'),
    path('insights/<uuid:pk>/approve/', views.ApproveInsightView.as_view(), name='approve_insight'),
    path('insights/<uuid:pk>/feedback/', views.FeedbackInsightView.as_view(), name='feedback_insight'),

    # API Endpoints
    path('api/sessions/<uuid:session_id>/results/', views.SessionResultsAPIView.as_view(), name='api_session_results'),

    # AJAX Endpoints
    path('ajax/sessions/<uuid:session_id>/progress/', views.ScreeningProgressView.as_view(), name='ajax_progress'),
    path('result/<uuid:pk>/shortlist-toggle/', views.ScreeningResultShortlistToggleView.as_view(), name='shortlist_toggle'),
    path('result/<uuid:pk>/note/', views.ScreeningResultNoteAddView.as_view(), name='add_note'),
    path('bulk-shortlist/', views.BulkShortlistView.as_view(), name='bulk_shortlist'),
]
