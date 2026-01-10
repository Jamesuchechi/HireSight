from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('browse/', views.browse_jobs, name='browse'),
    path('saved/', views.saved_jobs, name='saved'),
    path('<int:pk>/', views.job_detail, name='detail'),
    path('manage/', views.manage_jobs, name='manage'),
    # TODO: Add more job-related URLs when Job model is implemented
]