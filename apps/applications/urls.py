from django.urls import path
from .views import (
    # Job Seeker Views
    JobApplyView, ApplicationListView, ApplicationDetailView, ApplicationWithdrawView,
    
    # Company Views
    ApplicationManageView, ApplicantDetailView, ApplicationUpdateStatusView,
    ApplicationBulkActionView, ApplicationNoteCreateView, ApplicationExportView,
    ApplicationResumeDownloadView, ApplicationResumePreviewView, ApplicationRejectView,
    CompanyPipelineDataView,
    
    # Shared Views
    ApplicationStatsView,
    
    # AJAX Views
    ApplicationStatusUpdateView, ApplicationShortlistToggleView, ApplicationNoteCreateAJAXView
)
from apps.resumes.views import ResumeDownloadView, ResumePreviewView


app_name = 'applications'


urlpatterns = [
    # ===========================
    # JOB SEEKER ROUTES (Personal)
    # ===========================
    path('my/', ApplicationListView.as_view(), name='my_applications'),
    path('my/<uuid:pk>/', ApplicationDetailView.as_view(), name='detail'),
    path('apply/<slug:slug>/', JobApplyView.as_view(), name='apply'),
    path('my/<uuid:pk>/withdraw/', ApplicationWithdrawView.as_view(), name='withdraw'),
    
    # ===========================
    # COMPANY ROUTES (Recruiter)
    # ===========================
    # All applications overview
    path('manage/', ApplicationManageView.as_view(), name='manage'),
    
    # Job-specific pipeline view
    path('manage/job/<slug:slug>/', ApplicationManageView.as_view(), name='pipeline'),
    
    # Single applicant detail (with job context)
    path('manage/job/<slug:slug>/applicant/<uuid:pk>/', ApplicantDetailView.as_view(), name='applicant_detail'),
    
    # Status updates
    path('manage/<uuid:pk>/status/', ApplicationUpdateStatusView.as_view(), name='update_status'),
    path('manage/<uuid:pk>/reject/', ApplicationRejectView.as_view(), name='reject_application'),
    
    # Bulk actions
    path('manage/bulk-action/', ApplicationBulkActionView.as_view(), name='bulk_action'),
    
    # Notes
    path('manage/<uuid:pk>/notes/', ApplicationNoteCreateView.as_view(), name='add_note'),
    
    # Export
path('manage/export/', ApplicationExportView.as_view(), name='export'),

# AJAX pipeline data refresh
path('manage/pipeline-data/', CompanyPipelineDataView.as_view(), name='pipeline_data'),

# Company stats
path('manage/stats/', ApplicationStatsView.as_view(), name='company_stats'),
    
    # Resume download and preview for companies
    path('manage/resume/<uuid:pk>/download/', ApplicationResumeDownloadView.as_view(), name='resume_download'),
    path('manage/resume/<uuid:pk>/preview/', ApplicationResumePreviewView.as_view(), name='resume_preview'),
    
    # ===========================
    # SHARED ROUTES
    # ===========================
    path('stats/', ApplicationStatsView.as_view(), name='stats'),
    
    # ===========================
    # AJAX ROUTES (Both account types)
    # ===========================
    path('ajax/<uuid:pk>/status/', ApplicationStatusUpdateView.as_view(), name='ajax_status_update'),
    path('ajax/<uuid:pk>/shortlist/', ApplicationShortlistToggleView.as_view(), name='ajax_shortlist_toggle'),
    path('ajax/<uuid:pk>/notes/', ApplicationNoteCreateAJAXView.as_view(), name='ajax_add_note'),
    # Add new AJAX endpoint for Kanban drag-and-drop
    path('ajax/<uuid:pk>/update-status/', ApplicationStatusUpdateView.as_view(), name='ajax_update_status'),
]
