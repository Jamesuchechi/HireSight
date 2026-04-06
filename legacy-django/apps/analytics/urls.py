"""
URL configuration for analytics app.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('skill-proficiency/', views.SkillProficiencyDashboard.as_view(), name='skill_proficiency'),
    
    # Job-specific analytics (company only)
    path('job/<uuid:job_id>/', views.JobAnalyticsDetailView.as_view(), name='job_detail'),
    
    # Export functionality
    path('export/', views.ExportAnalyticsView.as_view(), name='export'),

    # Report builder
    path('reports/', views.AnalyticsReportBuilderView.as_view(), name='report_builder'),

    # Export API
    path('api/export/', views.AnalyticsDataExportView.as_view(), name='api_export'),
    
    # API endpoints for AJAX requests
    path('api/metric/', views.AnalyticsAPIView.as_view(), name='api_metric'),
]
