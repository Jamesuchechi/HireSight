from django.urls import path
from . import views

app_name = 'screening'

urlpatterns = [
    path('upload/', views.upload, name='upload'),
    # TODO: Add more screening-related URLs when models are implemented
]