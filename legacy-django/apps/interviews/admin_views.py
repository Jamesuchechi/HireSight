"""
Custom admin views for interview practice analytics and operational tooling.
"""

from datetime import timedelta
import json

from decimal import Decimal
from django.conf import settings
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from .models import InterviewPracticeSession, AIUsageLog


class AdminViewMixin:
    """Mixin that injects admin context when registered through AdminSite."""

    admin_site = None

    def get_admin_context(self):
        if self.admin_site:
            return self.admin_site.each_context(self.request)
        return {}


class FailedSessionsView(AdminViewMixin, TemplateView):
    """Display a snapshot of recently failed practice sessions."""

    template_name = 'admin/interviews/practice/failed_sessions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        failed_qs = InterviewPracticeSession.objects.filter(
            status=InterviewPracticeSession.Status.FAILED
        ).select_related('candidate', 'application__job__company').order_by('-created_at')

        context.update({
            'title': 'Failed Practice Sessions',
            'failed_sessions': failed_qs[:200],
            'total_failed': failed_qs.count(),
        })
        context.update(self.get_admin_context())
        return context


class HighCostUsersView(AdminViewMixin, TemplateView):
    """List users whose AI usage exceeds cost thresholds."""

    template_name = 'admin/interviews/practice/high_cost_users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = Decimal(getattr(settings, 'PRACTICE_HIGH_COST_THRESHOLD_USD', 10))

        high_cost_users = (
            AIUsageLog.objects.filter(user__isnull=False)
            .values('user__id', 'user__email')
            .annotate(
                total_cost=Sum('estimated_cost_usd'),
                total_tokens=Sum('total_tokens'),
                session_count=Count('session')
            )
            .filter(total_cost__gte=threshold)
            .order_by('-total_cost')
        )

        context.update({
            'title': 'High Cost Users',
            'threshold': threshold,
            'high_cost_users': list(high_cost_users),
        })
        context.update(self.get_admin_context())
        return context


class PracticeAnalyticsView(AdminViewMixin, TemplateView):
    """Visualize practice session usage trends over time."""

    template_name = 'admin/interviews/practice/practice_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        window_start = now - timedelta(days=29)

        daily_stats = (
            InterviewPracticeSession.objects.filter(created_at__gte=window_start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                session_count=Count('id'),
                average_score=Avg('overall_score')
            )
            .order_by('day')
        )

        labels = [stat['day'].strftime('%Y-%m-%d') for stat in daily_stats]
        sessions = [stat['session_count'] for stat in daily_stats]
        scores = [
            round(stat['average_score'] or 0, 1)
            for stat in daily_stats
        ]

        context.update({
            'title': 'Practice Analytics',
            'chart_labels': json.dumps(labels),
            'chart_sessions': json.dumps(sessions),
            'chart_scores': json.dumps(scores),
            'total_sessions': sum(sessions),
            'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'window_start': window_start.date(),
            'window_end': now.date(),
        })
        context.update(self.get_admin_context())
        return context
