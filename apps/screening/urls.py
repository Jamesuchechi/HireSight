"""
URL configuration for screening app.
"""
from django.urls import path
from . import views

app_name = 'screening'

urlpatterns = [
    # Session Management
    path('sessions/', views.ScreeningSessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.ScreeningSessionCreateView.as_view(), name='session_create'),
    path('sessions/<uuid:pk>/', views.ScreeningSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<uuid:pk>/update/', views.ScreeningSessionUpdateView.as_view(), name='session_update'),
    
    # Criteria Setup
    path('sessions/<uuid:pk>/criteria/', views.ScreeningCriteriaSetupView.as_view(), name='criteria_setup'),
    path('sessions/<uuid:pk>/criteria/update/', views.ScreeningCriteriaUpdateView.as_view(), name='criteria_update'),
    
    # Resume Upload
    path('sessions/<uuid:pk>/upload/', views.BulkResumeUploadView.as_view(), name='bulk_upload'),
    
    # Results
    path('sessions/<uuid:pk>/results/', views.ScreeningResultsView.as_view(), name='results'),
    path('results/<uuid:pk>/', views.ScreeningResultDetailView.as_view(), name='result_detail'),
    
    # Export
    path('sessions/<uuid:pk>/export/', views.ScreeningResultExportView.as_view(), name='export'),
    
    # Analytics
    path('sessions/<uuid:pk>/analytics/', views.ScreeningAnalyticsView.as_view(), name='analytics'),
    
    # Pipeline Integration
    path('sessions/<uuid:pk>/push-pipeline/', views.PushToPipelineView.as_view(), name='push_pipeline'),
    path('sessions/<uuid:pk>/bulk-push-pipeline/', views.BulkPushToPipelineView.as_view(), name='bulk_push_pipeline'),
    path('pipeline/status-update/', views.PipelineStatusUpdateView.as_view(), name='pipeline_status_update'),
    
    # Real-Time Progress Tracking
    path('sessions/<uuid:pk>/progress-updates/', views.ProgressUpdateView.as_view(), name='progress_updates'),
    path('sessions/<uuid:pk>/stats/', views.SessionStatsView.as_view(), name='session_stats'),
    path('sessions/<uuid:pk>/create-update/', views.CreateProgressUpdateView.as_view(), name='create_update'),
    
    # AI Insights
    path('sessions/<uuid:pk>/generate-insight/', views.GenerateInsightView.as_view(), name='generate_insight'),
    path('sessions/<uuid:pk>/batch-insights/', views.BatchGenerateInsightView.as_view(), name='batch_insights'),
    path('results/<uuid:result_id>/insights/', views.RetrieveInsightView.as_view(), name='retrieve_insights'),
    path('insights/<uuid:pk>/approve/', views.ApproveInsightView.as_view(), name='approve_insight'),
    path('insights/<uuid:pk>/feedback/', views.FeedbackInsightView.as_view(), name='feedback_insight'),
    
    # AJAX Endpoints
    path('ajax/sessions/<uuid:pk>/progress/', views.ScreeningProgressView.as_view(), name='ajax_progress'),
    path('result/<uuid:pk>/shortlist-toggle/', views.ScreeningResultShortlistToggleView.as_view(), name='shortlist_toggle'),
    path('result/<uuid:pk>/note/', views.ScreeningResultNoteAddView.as_view(), name='add_note'),
    path('bulk-shortlist/', views.BulkShortlistView.as_view(), name='bulk_shortlist'),
]