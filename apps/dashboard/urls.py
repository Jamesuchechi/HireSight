from django.urls import path
from . import views

urlpatterns = [
    path('personal/', views.personal_dashboard, name='personal_dashboard'),
    path('company/', views.company_dashboard, name='company_dashboard'),
]