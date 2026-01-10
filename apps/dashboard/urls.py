from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('landing/', views.landing, name='landing'),
    path('personal/', views.personal_dashboard, name='personal_dashboard'),
    path('company/', views.company_dashboard, name='company_dashboard'),
]