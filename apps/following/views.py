import csv
import io
import uuid
from collections import Counter
from datetime import datetime, timedelta

from django.views import View
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Exists, OuterRef
from django.db.models.functions import TruncDay
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from apps.accounts.models import User, ProfileView
from apps.following.forms import BulkFollowSelectionForm, BulkFollowCSVForm
from apps.following.tasks import send_follow_notification, process_bulk_follow_operation
from apps.following.models import Follow, Activity, ActivityType
from apps.notifications.models import Notification, NotificationType


class FollowToggleView(LoginRequiredMixin, View):
    """
    Handle both follow and unfollow actions.
    Supports AJAX requests for seamless UI updates.
    """
    
    def post(self, request, user_id):
        # Prevent companies from following
        if request.user.account_type == 'company':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Company accounts cannot follow users'
                }, status=403)
            messages.error(request, "Company accounts cannot follow users")
            return redirect('dashboard')
        
        user_to_follow = get_object_or_404(User, pk=user_id)
        
        # Prevent self-following
        if user_to_follow == request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'You cannot follow yourself'
                }, status=400)
            messages.error(request, "You cannot follow yourself")
            return redirect('dashboard')
        
        # Check if already following
        follow_instance = Follow.objects.filter(
            follower=request.user, 
            followed=user_to_follow
        ).first()
        
        if follow_instance:
            # Unfollow
            follow_instance.delete()
            is_following = False
            message = f"You unfollowed {user_to_follow.get_display_name()}"
        else:
            # Follow
            follow = Follow(follower=request.user, followed=user_to_follow)
            follow._skip_async_notification = True
            follow.save()
            send_follow_notification.delay(
                follower_id=request.user.id,
                followed_id=user_to_follow.id
            )
            is_following = True
            message = f"You are now following {user_to_follow.get_display_name()}"
        
        # AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_following': is_following,
                'follower_count': Follow.get_follower_count(user_to_follow),
                'message': message
            })
        
        # Regular POST redirect
        messages.success(request, message)
        return redirect(request.POST.get('next', 'dashboard'))


class FollowingListView(LoginRequiredMixin, ListView):
    """
    Display list of users that the current user is following.
    """
    model = Follow
    template_name = 'following/following_list.html'
    context_object_name = 'follows'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            follower=self.request.user
        ).select_related(
            'followed',
            'followed__personalprofile',
            'followed__companyprofile'
        ).annotate(
            follower_count=Count('followed__followers', distinct=True),
            is_mutual=Exists(
                Follow.objects.filter(
                    follower=OuterRef('followed'),
                    followed=self.request.user
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['following_count'] = self.get_queryset().count()
        context['page_title'] = 'Following'
        return context


class FollowersListView(LoginRequiredMixin, ListView):
    """
    Display list of users following the current user.
    """
    model = Follow
    template_name = 'following/followers_list.html'
    context_object_name = 'follows'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            followed=self.request.user
        ).select_related(
            'follower',
            'follower__personalprofile',
            'follower__companyprofile'
        ).annotate(
            follower_count=Count('follower__followers', distinct=True),
            is_mutual=Exists(
                Follow.objects.filter(
                    follower=self.request.user,
                    followed=OuterRef('follower')
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followers_count'] = self.get_queryset().count()
        context['page_title'] = 'Followers'
        return context


class MutualFollowersView(LoginRequiredMixin, ListView):
    """
    Display mutual followers between current user and another user.
    """
    model = User
    template_name = 'following/mutual_followers.html'
    context_object_name = 'mutual_followers'
    paginate_by = 20

    def get_queryset(self):
        other_user_id = self.kwargs.get('user_id')
        other_user = get_object_or_404(User, pk=other_user_id)
        return Follow.get_mutual_followers(self.request.user, other_user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_user'] = get_object_or_404(User, pk=self.kwargs.get('user_id'))
        context['mutual_count'] = self.get_queryset().count()
        return context


class SuggestedFollowsView(LoginRequiredMixin, TemplateView):
    """
    Suggest users/companies to follow based on applications, shared skills, and popularity.
    """
    template_name = 'following/suggested_follows.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        already_following = set(
            Follow.objects.filter(follower=self.request.user).values_list('followed_id', flat=True)
        )
        suggested_companies = []
        suggested_users = []

        if self.request.user.account_type == 'personal':
            suggested_companies = self._get_company_suggestions(already_following)
            suggested_users = self._get_personal_suggestions(already_following)

        context['suggested_companies'] = suggested_companies
        context['suggested_users'] = suggested_users
        context['has_personal_account'] = self.request.user.account_type == 'personal'
        return context

    def _normalize_skill_names(self, skills):
        normalized = set()
        for skill in skills or []:
            if isinstance(skill, str):
                value = skill
            elif isinstance(skill, dict):
                value = skill.get('skill') or skill.get('name') or skill.get('label')
            else:
                continue

            if not value:
                continue

            normalized.add(value.strip().lower())
        return normalized

    def _get_company_suggestions(self, already_following):
        from apps.applications.models import Application

        company_ids = Application.objects.filter(user=self.request.user).values_list('job__company_id', flat=True).distinct()
        if company_ids:
            companies = User.objects.filter(
                id__in=company_ids,
                account_type='company'
            ).exclude(
                id__in=already_following
            ).select_related('companyprofile').annotate(
                followers_count=Count('followers')
            ).order_by('-followers_count')[:6]
            return companies

        return User.objects.filter(
            account_type='company'
        ).exclude(
            id__in=already_following
        ).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:6]

    def _get_personal_suggestions(self, already_following):
        user_skills = self._normalize_skill_names(
            getattr(getattr(self.request.user, 'personalprofile', None), 'skills', [])
        )
        base_qs = User.objects.filter(
            account_type='personal'
        ).exclude(
            Q(id=self.request.user.id) | Q(id__in=already_following)
        ).select_related('personalprofile').annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:80]

        recommendations = []
        used_ids = set()

        if user_skills:
            scored = []
            for candidate in base_qs:
                profile = getattr(candidate, 'personalprofile', None)
                candidate_skills = self._normalize_skill_names(getattr(profile, 'skills', []))
                shared = user_skills & candidate_skills
                if shared:
                    scored.append({
                        'user': candidate,
                        'shared_skills': sorted(shared),
                        'score': (len(shared), candidate.followers_count or 0)
                    })
            scored.sort(key=lambda entry: (-entry['score'][0], -entry['score'][1]))
            for entry in scored:
                recommendations.append({
                    'user': entry['user'],
                    'shared_skills': entry['shared_skills'],
                })
                used_ids.add(entry['user'].id)
                if len(recommendations) >= 6:
                    break

        if len(recommendations) < 6:
            fallback = User.objects.filter(
                account_type='personal'
            ).exclude(
                Q(id=self.request.user.id) | Q(id__in=already_following) | Q(id__in=used_ids)
            ).select_related('personalprofile').annotate(
                followers_count=Count('followers')
            ).order_by('-followers_count')[:6]

            for user in fallback:
                if len(recommendations) >= 6:
                    break
                recommendations.append({
                    'user': user,
                    'shared_skills': []
                })
                used_ids.add(user.id)

        return recommendations


class ActivityFeedView(LoginRequiredMixin, ListView):
    """
    Activity feed from followed users with HTMX polling support.
    """
    model = Activity
    template_name = 'following/activity_feed.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_filter_option(self):
        return self.request.GET.get('filter', 'all')

    def get_queryset(self):
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list('followed_id', flat=True)

        qs = Activity.objects.filter(
            user_id__in=following_ids,
            is_public=True
        ).select_related('user')

        filter_option = self.get_filter_option()
        if filter_option == 'companies':
            qs = qs.filter(user__account_type='company')
        elif filter_option == 'people':
            qs = qs.filter(user__account_type='personal')

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_option'] = self.get_filter_option()
        context['ActivityType'] = ActivityType
        context['has_following'] = Follow.objects.filter(follower=self.request.user).exists()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'following/partials/activity_cards.html', context)
        return super().render_to_response(context, **response_kwargs)


class FollowStatsView(LoginRequiredMixin, View):
    """
    API endpoint for follow statistics (for AJAX requests).
    """
    
    def get(self, request, user_id=None):
        target_user = get_object_or_404(User, pk=user_id) if user_id else request.user
        
        stats = {
            'follower_count': Follow.get_follower_count(target_user),
            'following_count': Follow.get_following_count(target_user),
            'is_following': Follow.objects.filter(
                follower=request.user, 
                followed=target_user
            ).exists() if user_id else False,
            'is_mutual': Follow.are_mutual_followers(
                request.user, 
                target_user
            ) if user_id and user_id != request.user.id else False
        }
        
        return JsonResponse(stats)


class FollowAnalyticsMixin:
    DATE_FORMAT = '%Y-%m-%d'
    DEFAULT_WINDOW_DAYS = 30

    def parse_date(self, date_str, fallback):
        try:
            return datetime.strptime(date_str, self.DATE_FORMAT).date()
        except Exception:
            return fallback

    def get_date_range(self, request):
        today = timezone.localdate()
        end_date = self.parse_date(request.GET.get('end_date', ''), today)
        start_date = self.parse_date(request.GET.get('start_date', ''), today - timedelta(days=self.DEFAULT_WINDOW_DAYS))

        if start_date > end_date:
            start_date = end_date - timedelta(days=self.DEFAULT_WINDOW_DAYS)

        return start_date, end_date

    def build_payload(self, user, start_date, end_date):
        start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        total_followers = Follow.get_follower_count(user)
        total_following = Follow.get_following_count(user)

        range_days = (end_date - start_date).days + 1
        previous_end = start_date - timedelta(days=1)
        previous_start = previous_end - timedelta(days=range_days - 1)
        previous_start_dt = timezone.make_aware(datetime.combine(previous_start, datetime.min.time()))
        previous_end_dt = timezone.make_aware(datetime.combine(previous_end, datetime.max.time()))

        current_period_new = Follow.objects.filter(
            followed=user,
            created_at__range=(start_dt, end_dt)
        ).count()
        previous_period_new = Follow.objects.filter(
            followed=user,
            created_at__range=(previous_start_dt, previous_end_dt)
        ).count()

        growth_rate = 0
        if previous_period_new:
            growth_rate = (current_period_new - previous_period_new) / previous_period_new * 100
        elif current_period_new:
            growth_rate = 100.0

        retention_threshold = timezone.now() - timedelta(days=30)
        retained_followers = Follow.objects.filter(
            followed=user,
            created_at__lte=retention_threshold
        ).count()
        retention_rate = (retained_followers / total_followers * 100) if total_followers else 0

        daily_counts = Follow.objects.filter(
            followed=user,
            created_at__range=(start_dt, end_dt)
        ).annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        counts_map = {
            record['day'].date(): record['count'] for record in daily_counts
        }

        labels = []
        data_points = []
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %d'))
            data_points.append(counts_map.get(current, 0))
            current += timedelta(days=1)

        followers_scope = Follow.objects.filter(followed=user)
        top_followers_qs = followers_scope.select_related('follower').annotate(
            influence=Count('follower__followers')
        ).order_by('-influence')[:5]

        top_followers = []
        for follow in top_followers_qs:
            follower = follow.follower
            top_followers.append({
                'name': follower.get_display_name(),
                'influence': follow.influence,
                'profile_url': reverse('accounts:profile_detail', kwargs={'user_id': follower.id}),
                'account_type': follower.account_type,
            })

        follower_ids = list(followers_scope.values_list('follower_id', flat=True))
        geo_counter = Counter()
        if follower_ids:
            follower_users = User.objects.filter(id__in=follower_ids).select_related(
                'personalprofile', 'companyprofile'
            )
            for follower_user in follower_users:
                location = getattr(
                    getattr(follower_user, 'personalprofile', None),
                    'location',
                    ''
                )
                if not location and getattr(follower_user, 'companyprofile', None):
                    locations = getattr(follower_user.companyprofile, 'locations', []) or []
                    if locations:
                        loc = locations[0]
                        location = ', '.join(filter(None, [loc.get('city'), loc.get('country')]))
                geo_counter[location or 'Unknown'] += 1

        geo_distribution = [
            {'location': loc, 'count': count}
            for loc, count in geo_counter.most_common(5)
        ]

        profile_view_qs = ProfileView.objects.filter(profile_user=user)
        if follower_ids:
            profile_view_qs = profile_view_qs.filter(viewer_id__in=follower_ids)
        recent_window = timezone.now() - timedelta(days=30)
        profile_view_qs = profile_view_qs.filter(viewed_at__gte=recent_window)
        profile_views = profile_view_qs.count()
        unique_viewers = profile_view_qs.values('viewer_id').distinct().count()

        unfollow_activities = Activity.objects.filter(
            activity_type=ActivityType.UNFOLLOWED_USER,
            content__unfollowed_user_id=user.id
        ).select_related('user').order_by('-created_at')[:5]

        recent_unfollows = [{
            'name': act.user.get_display_name(),
            'profile_url': act.user.get_profile_url(),
            'when': act.created_at.isoformat()
        } for act in unfollow_activities]

        chart_payload = {
            'labels': labels,
            'values': data_points,
            'total_new_followers': current_period_new,
            'start_date': start_date.strftime(self.DATE_FORMAT),
            'end_date': end_date.strftime(self.DATE_FORMAT),
        }

        return {
            'follower_count': total_followers,
            'following_count': total_following,
            'growth_rate': round(growth_rate, 1),
            'retention_rate': round(retention_rate, 1),
            'current_period_new': current_period_new,
            'previous_period_new': previous_period_new,
            'top_followers': top_followers,
            'geo_distribution': geo_distribution,
            'chart': chart_payload,
            'engagement': {
                'profile_views': profile_views,
                'unique_viewers': unique_viewers,
            },
            'recent_unfollows': recent_unfollows,
        }


class FollowAnalyticsView(LoginRequiredMixin, FollowAnalyticsMixin, TemplateView):
    template_name = 'following/analytics.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.account_type != 'personal':
            messages.warning(request, 'Analytics are available to personal accounts only.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date = self.get_date_range(self.request)
        payload = self.build_payload(self.request.user, start_date, end_date)
        context['selected_start_date'] = start_date.strftime(self.DATE_FORMAT)
        context['selected_end_date'] = end_date.strftime(self.DATE_FORMAT)
        context['analytics_api_url'] = reverse('following:analytics_api')
        context.update(payload)
        return context


class FollowAnalyticsAPIView(LoginRequiredMixin, FollowAnalyticsMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.account_type != 'personal':
            return JsonResponse({'error': 'Personal account required'}, status=403)

        start_date, end_date = self.get_date_range(request)
        payload = self.build_payload(request.user, start_date, end_date)
        return JsonResponse(payload)


class BulkFollowView(LoginRequiredMixin, TemplateView):
    template_name = 'following/bulk_follow.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.account_type != 'personal':
            messages.warning(request, 'Bulk follow tools are reserved for personal accounts.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selection_form'] = BulkFollowSelectionForm()
        context['csv_form'] = BulkFollowCSVForm()
        context['candidate_users'] = self._get_candidate_users()
        context['bulk_progress_url'] = reverse('following:bulk_follow_progress')
        context['progress_data'] = cache.get(self._progress_cache_key(), {})
        context['last_result'] = cache.get(self._result_cache_key(), {})
        return context

    def post(self, request, *args, **kwargs):
        if 'csv_file' in request.FILES:
            return self._handle_csv_upload(request)
        return self._handle_bulk_selection(request)

    def _get_candidate_users(self):
        queryset = User.objects.filter(account_type='personal').exclude(id=self.request.user.id)
        term = self.request.GET.get('q')
        if term:
            queryset = queryset.filter(
                Q(personalprofile__full_name__icontains=term) |
                Q(email__icontains=term)
            )
        return queryset.select_related('personalprofile').annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:30]

    def _handle_bulk_selection(self, request):
        form = BulkFollowSelectionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please select up to 50 users.")
            return redirect('following:bulk_follow')

        if not self._can_start_operation():
            messages.warning(request, "Please wait a moment before running another bulk action.")
            return redirect('following:bulk_follow')

        user_ids = [uid for uid in form.cleaned_data['user_ids'] if uid != request.user.id]
        action = form.cleaned_data['action']
        result = self._execute_bulk_action(request.user, user_ids, action)
        cache.set(self._result_cache_key(), result, 3600)
        cache.set(self._progress_cache_key(), {
            'status': 'complete',
            'action': action,
            'processed': len(user_ids),
            'success': len(result['success']),
            'errors': result['errors'],
            'timestamp': timezone.now().isoformat()
        }, 3600)
        cache.set(self._lock_cache_key(), True, 60)
        messages.success(request, result['message'])
        return redirect('following:bulk_follow')

    def _handle_csv_upload(self, request):
        form = BulkFollowCSVForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Upload a valid CSV file (max 50 rows).")
            return redirect('following:bulk_follow')

        csv_file = form.cleaned_data['csv_file']
        try:
            decoded = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            messages.error(request, "CSV must be UTF-8 encoded.")
            return redirect('following:bulk_follow')

        reader = csv.DictReader(io.StringIO(decoded))
        identifiers = []
        for row in reader:
            if len(identifiers) >= 50:
                break
            email = row.get('email') or row.get('Email')
            user_id = row.get('user_id') or row.get('id')
            if email:
                identifiers.append({'email': email.strip().lower()})
            elif user_id:
                try:
                    identifiers.append({'user_id': int(user_id)})
                except ValueError:
                    continue

        if not identifiers:
            messages.error(request, "CSV must contain an email or user_id column.")
            return redirect('following:bulk_follow')

        user_ids = []
        errors = []
        emails = [entry['email'] for entry in identifiers if 'email' in entry]
        if emails:
            matched_users = list(User.objects.filter(email__in=emails).values('id', 'email'))
            user_ids.extend(entry['id'] for entry in matched_users)
            found_emails = {entry['email'].lower() for entry in matched_users}
            missing = [email for email in emails if email not in found_emails]
            for email in missing:
                errors.append(f"{email} not found")

        for entry in identifiers:
            if 'user_id' in entry:
                try:
                    if entry['user_id'] != request.user.id:
                        user_ids.append(entry['user_id'])
                except (TypeError, ValueError):
                    errors.append(f"Invalid user_id {entry.get('user_id')}")

        if request.user.id in user_ids:
            user_ids = [uid for uid in user_ids if uid != request.user.id]

        user_ids = list(dict.fromkeys(user_ids))[:50]

        if not user_ids:
            messages.error(request, "No valid users found in the CSV.")
            return redirect('following:bulk_follow')

        operation_id = str(uuid.uuid4())
        cache.set(self._progress_cache_key(), {
            'status': 'queued',
            'action': 'follow',
            'total': len(user_ids),
            'processed': 0,
            'success': 0,
            'errors': errors,
            'operation_id': operation_id,
            'timestamp': timezone.now().isoformat()
        }, 3600)

        process_bulk_follow_operation.delay(
            follower_id=request.user.id,
            user_ids=user_ids,
            action='follow',
            operation_id=operation_id
        )

        messages.success(request, "CSV import queued. You'll receive a notification when processing completes.")
        return redirect('following:bulk_follow')

    def _execute_bulk_action(self, follower, user_ids, action):
        results = {'success': [], 'already_following': [], 'errors': []}
        targets = User.objects.filter(id__in=user_ids)
        target_map = {target.id: target for target in targets}

        for user_id in user_ids:
            target = target_map.get(user_id)
            if not target:
                results['errors'].append(f"User {user_id} not found")
                continue

            if action == 'follow':
                if target == follower:
                    results['errors'].append("Cannot follow yourself.")
                    continue

                obj, created = Follow.objects.get_or_create(
                    follower=follower,
                    followed=target
                )
                if created:
                    results['success'].append(user_id)
                else:
                    results['already_following'].append(user_id)
            else:
                deleted, _ = Follow.objects.filter(
                    follower=follower,
                    followed=target
                ).delete()
                if deleted:
                    results['success'].append(user_id)
                else:
                    results['errors'].append(f"Was not following {target.get_display_name()}")

        Activity.objects.create(
            user=follower,
            activity_type=ActivityType.BULK_OPERATION,
            content={
                'action': action,
                'processed': len(user_ids),
                'successful': len(results['success']),
                'errors': len(results['errors'])
            }
        )

        Notification.objects.create(
            user=follower,
            title="Bulk follow operation complete",
            message=f"Processed {len(user_ids)} users with {len(results['success'])} changes.",
            notification_type=NotificationType.SYSTEM,
            action_url=reverse('following:bulk_follow'),
            action_text="View bulk operations"
        )

        summary_message = (
            f"{len(results['success'])} users updated, "
            f"{len(results['already_following'])} already in desired state, "
            f"{len(results['errors'])} errors."
        )

        return {'message': summary_message, **results}

    def _can_start_operation(self):
        return not cache.get(self._lock_cache_key())

    def _progress_cache_key(self):
        return f'bulk_follow_progress_{self.request.user.id}'

    def _result_cache_key(self):
        return f'bulk_follow_result_{self.request.user.id}'

    def _lock_cache_key(self):
        return f'bulk_follow_lock_{self.request.user.id}'


class BulkFollowProgressView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        data = cache.get(f'bulk_follow_progress_{request.user.id}')
        return JsonResponse(data or {'status': 'idle'})
