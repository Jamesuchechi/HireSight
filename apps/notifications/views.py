from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Notification, NotificationType


def _redirect_back(request):
    """Helper to return the user to the originating page after a POST."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect(reverse('notifications:list'))


@login_required
def notification_list(request):
    filter_key = request.GET.get('filter', 'all')
    user_notifications = Notification.objects.filter(user=request.user)
    has_unread = user_notifications.filter(is_read=False).exists()
    total_notifications = user_notifications.count()

    notifications = user_notifications
    if filter_key == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_key in {choice.value for choice in NotificationType}:
        notifications = notifications.filter(notification_type=filter_key)

    notifications = notifications.order_by('-created_at')

    paginator = Paginator(notifications, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()
    query_suffix = f"&{query_string}" if query_string else ''

    filter_options = [
        {'key': 'all', 'label': 'All'},
        {'key': 'unread', 'label': 'Unread'},
        {'key': NotificationType.APPLICATION, 'label': 'Applications'},
        {'key': NotificationType.MESSAGE, 'label': 'Messages'},
        {'key': NotificationType.JOB, 'label': 'Jobs'},
        {'key': NotificationType.SYSTEM, 'label': 'System'},
    ]

    selected_label = next((opt['label'] for opt in filter_options if opt['key'] == filter_key), 'All')

    return render(request, 'notifications/list.html', {
        'notifications': page_obj,
        'filter_options': filter_options,
        'selected_filter': filter_key,
        'selected_filter_label': selected_label,
        'query_suffix': query_suffix,
        'total_notifications': total_notifications,
        'has_unread': has_unread,
    })


@login_required
def unread_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required
@require_POST
def toggle_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = not notification.is_read
    notification.save(update_fields=['is_read'])
    return _redirect_back(request)


@login_required
@require_POST
def mark_all_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return _redirect_back(request)


@login_required
@require_POST
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    return _redirect_back(request)


@login_required
@require_POST
def delete_all_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return _redirect_back(request)


@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    return render(request, 'notifications/detail.html', {'notification': notification})
