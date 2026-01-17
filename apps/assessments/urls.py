from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Browse and discover tests
    path('browse/', views.BrowseTestsView.as_view(), name='browse'),
    path('generate/', views.GenerateQuestionsPageView.as_view(), name='generate_questions_page'),
    path('test/<slug:slug>/generate/', views.GenerateQuestionsView.as_view(), name='generate_questions'),
    path('test/<slug:slug>/', views.TestDetailView.as_view(), name='test_detail'),
    
    # Take assessments
    path('start/<uuid:test_id>/', views.StartTestView.as_view(), name='start'),
    path('take/<uuid:attempt_id>/', views.TakeTestView.as_view(), name='take'),
    path('save-progress/<uuid:attempt_id>/', views.SaveProgressView.as_view(), name='save_progress'),
    
    # Results and certificates
    path('results/<uuid:attempt_id>/', views.ViewResultsView.as_view(), name='results'),
    path('certificate/<uuid:attempt_id>/', views.DownloadCertificateView.as_view(), name='certificate'),
    
    # Badges
    path('my-badges/', views.MyBadgesView.as_view(), name='my_badges'),
    path('verify/<str:verification_code>/', views.VerifyBadgeView.as_view(), name='verify_badge'),
]
