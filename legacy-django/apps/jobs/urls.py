from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # ==================== Public Job Seeker Routes ====================
    # Browse and search jobs
    path('browse/', views.JobBrowseView.as_view(), name='browse'),
    
    # Save/bookmark jobs
    path('saved/', views.SavedJobsView.as_view(), name='saved'),
    
    # ==================== Company/Recruiter Routes ====================
    # Job management dashboard
    path('manage/', views.JobManageView.as_view(), name='manage'),
    
    # Create job
    path('create/', views.JobCreateView.as_view(), name='create'),
    
    # ==================== API Endpoints ====================
    # Job stats API (must be before slug patterns)
    path('api/<slug:slug>/stats/', views.job_stats_api, name='stats_api'),
    
    # ==================== Job Detail and Actions ====================
    # IMPORTANT: UUID patterns MUST come before slug patterns
    # Otherwise Django will try to match UUID as a slug
    
    # Support UUID-based URLs for backward compatibility
    path('by-id/<uuid:job_id>/', views.JobDetailView.as_view(), name='detail_by_id'),
    
    # Job detail by slug
    path('<slug:slug>/', views.JobDetailView.as_view(), name='detail'),
    
    # Save/bookmark jobs
    path('<slug:slug>/save/', views.toggle_save_job, name='toggle_save'),
    
    # Edit job
    path('<slug:slug>/edit/', views.JobEditView.as_view(), name='edit'),
    
    # Delete job
    path('<slug:slug>/delete/', views.JobDeleteView.as_view(), name='delete'),
    
    # Duplicate job
    path('<slug:slug>/duplicate/', views.duplicate_job, name='duplicate'),
    
    # Change job status
    path('<slug:slug>/status/', views.change_job_status, name='change_status'),
    
    # Job analytics
    path('<slug:slug>/stats/', views.JobStatsView.as_view(), name='stats'),
]