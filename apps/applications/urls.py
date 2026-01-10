from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<int:pk>/', views.application_detail, name='detail'),
    path('apply/<int:job_id>/', views.apply_for_job, name='apply'),
    path('applicants/', views.applicants, name='applicants'),
    # TODO: Add more application-related URLs when Application model is implemented
]