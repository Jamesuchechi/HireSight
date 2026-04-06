from django.urls import path
from . import views

app_name = 'following'

urlpatterns = [
    # Follow/Unfollow toggle
    path('toggle/<uuid:user_id>/', views.FollowToggleView.as_view(), name='toggle'),
    
    # Lists
    path('following/', views.FollowingListView.as_view(), name='following_list'),
    path('followers/', views.FollowersListView.as_view(), name='followers_list'),
    path('mutual/<uuid:user_id>/', views.MutualFollowersView.as_view(), name='mutual_followers'),
    
    # Suggestions
    path('suggested/', views.SuggestedFollowsView.as_view(), name='suggested_follows'),
    path('activity/', views.ActivityFeedView.as_view(), name='activity_feed'),
    
    # API endpoints
    path('stats/<uuid:user_id>/', views.FollowStatsView.as_view(), name='follow_stats'),
    path('stats/', views.FollowStatsView.as_view(), name='my_follow_stats'),
    path('analytics/', views.FollowAnalyticsView.as_view(), name='analytics'),
    path('analytics/api/', views.FollowAnalyticsAPIView.as_view(), name='analytics_api'),
    path('bulk/', views.BulkFollowView.as_view(), name='bulk_follow'),
    path('bulk/progress/', views.BulkFollowProgressView.as_view(), name='bulk_follow_progress'),
]
