from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    # List and create
    path('', views.ResumeListView.as_view(), name='list'),
    path('upload/', views.ResumeUploadView.as_view(), name='upload'),
    
    # Detail and edit
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ResumeEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ResumeDeleteView.as_view(), name='delete'),
    
    # Actions
    path('<int:pk>/download/', views.ResumeDownloadView.as_view(), name='download'),
    path('<int:pk>/preview/', views.ResumePreviewView.as_view(), name='preview'),
    path('<int:pk>/set-primary/', views.SetPrimaryResumeView.as_view(), name='set_primary'),
    path('<int:pk>/replace-file/', views.ResumeReplaceFileView.as_view(), name='replace_file'),
    path('<int:pk>/reparse/', views.resume_reparse_view, name='reparse'),
    
    # Bulk actions
    path('bulk-delete/', views.resume_bulk_delete_view, name='bulk_delete'),
    
    # API endpoints
    path('api/stats/', views.resume_stats_api, name='stats_api'),
    
    # Optimization
    path('<int:pk>/optimize/', views.ResumeOptimizationView.as_view(), name='optimize'),
    path('<int:pk>/optimize/run/', views.optimize_resume, name='optimize_run'),
    path('<int:pk>/optimize/report/', views.resume_optimization_report, name='optimization_report'),
    path('<int:pk>/rewrite/', views.resume_rewrite_preview, name='rewrite_preview'),
    path('<int:pk>/rewrite/save/', views.save_resume_rewrite, name='rewrite_save'),
    path('<int:pk>/rewrite/discard/', views.discard_resume_rewrite, name='rewrite_discard'),
    path('<int:pk>/rewrite/load/<int:draft_pk>/', views.load_saved_resume_rewrite, name='rewrite_load'),
    path('<int:pk>/rewrite/delete/<int:draft_pk>/', views.delete_saved_resume_rewrite, name='rewrite_delete'),
    path('<int:pk>/rewrite/apply/', views.apply_resume_rewrite, name='rewrite_apply'),
    path('<int:pk>/rewrite/apply/<int:draft_pk>/', views.apply_resume_rewrite, name='rewrite_apply_draft'),
    
    # Advanced Features
    path('compare/', views.ResumeComparisonView.as_view(), name='compare'),
    path('<int:pk>/benchmark/', views.IndustryBenchmarkView.as_view(), name='benchmark'),
    path('history/', views.OptimizationHistoryView.as_view(), name='optimization_history'),
    path('compare/run/', views.compare_resumes, name='compare_run'),
    path('<int:pk>/benchmark/data/', views.benchmark_resume, name='benchmark_data'),
    path('<int:pk>/optimize/advanced/', views.advanced_optimize_resume, name='advanced_optimize'),
]
