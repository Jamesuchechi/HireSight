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
    path('results/<uuid:attempt_id>/export-pdf/', views.ExportResultsPDFView.as_view(), name='export_results_pdf'),
    
    # Badges
    path('my-badges/', views.MyBadgesView.as_view(), name='my_badges'),
    path('verify/<str:verification_code>/', views.VerifyBadgeView.as_view(), name='verify_badge'),
    
    # History & Analytics
    path('history/', views.AssessmentHistoryView.as_view(), name='history'),
    path('learning-path/', views.LearningPathView.as_view(), name='learning_path'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('bookmarks/', views.MyBookmarksView.as_view(), name='my_bookmarks'),
    path('bookmarks/practice/', views.CreateCustomPracticeView.as_view(), name='custom_practice'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    
    # Study Groups
    path('study-groups/', views.StudyGroupListView.as_view(), name='study_groups'),
    path('study-groups/create/', views.CreateStudyGroupView.as_view(), name='create_study_group'),
    path('study-groups/<uuid:group_id>/', views.StudyGroupDetailView.as_view(), name='study_group_detail'),
    path('study-groups/<uuid:group_id>/join/', views.JoinStudyGroupView.as_view(), name='join_study_group'),
    path('study-groups/<uuid:group_id>/leave/', views.LeaveStudyGroupView.as_view(), name='leave_study_group'),
    path('study-groups/<uuid:group_id>/challenges/create/', views.CreateGroupChallengeView.as_view(), name='create_group_challenge'),
    path('study-groups/<uuid:group_id>/challenges/', views.GroupLeaderboardView.as_view(), name='group_leaderboard'),
    path('questions/<uuid:question_id>/bookmark/', views.BookmarkQuestionView.as_view(), name='bookmark_question'),
    path('questions/<uuid:question_id>/discuss/', views.QuestionDiscussionView.as_view(), name='question_discussion'),
    path('questions/<uuid:question_id>/flag/', views.FlagQuestionView.as_view(), name='flag_question'),
    path('questions/<uuid:question_id>/upvote-explanation/', views.UpvoteExplanationView.as_view(), name='upvote_explanation'),
]
