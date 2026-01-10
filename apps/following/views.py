from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Follow
from apps.accounts.models import User


@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, pk=user_id)
    Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
    return redirect('user_profile', user_id=user_id)


@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, pk=user_id)
    Follow.objects.filter(follower=request.user, followed=user_to_unfollow).delete()
    return redirect('user_profile', user_id=user_id)


@login_required
def following_list(request):
    following = Follow.objects.filter(follower=request.user).select_related('followed')
    return render(request, 'following/following_list.html', {'following': following})


@login_required
def followers_list(request):
    followers = Follow.objects.filter(followed=request.user).select_related('follower')
    return render(request, 'following/followers_list.html', {'followers': followers})