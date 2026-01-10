from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    # Resume management
    path('', views.ResumeListView.as_view(), name='list'),
    path('upload/', views.ResumeUploadView.as_view(), name='upload'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ResumeDetailView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ResumeDeleteView.as_view(), name='delete'),
    path('<int:pk>/download/', views.ResumeDownloadView.as_view(), name='download'),
    path('<int:pk>/preview/', views.ResumePreviewView.as_view(), name='preview'),
    path('<int:pk>/set-primary/', views.SetPrimaryResumeView.as_view(), name='set_primary'),
]