from datetime import timedelta

from django.db.models import Avg, ExpressionWrapper, DurationField, F, Count
from django.utils import timezone

from .models import Application, ApplicationStatus, ApplicationStatusHistory


def pipeline_stats(queryset):
    totals = {status.value: queryset.filter(status=status.value).count() for status in ApplicationStatus}
    stats = {
        'total': queryset.count(),
        'pending': totals.get(ApplicationStatus.PENDING.value, 0),
        'screening': totals.get(ApplicationStatus.SCREENING.value, 0),
        'interview': totals.get(ApplicationStatus.INTERVIEW.value, 0),
        'offer': totals.get(ApplicationStatus.OFFER.value, 0),
        'hired': totals.get(ApplicationStatus.HIRED.value, 0),
        'rejected': totals.get(ApplicationStatus.REJECTED.value, 0),
        'shortlisted': queryset.filter(is_shortlisted=True).count(),
        'avg_match_score': queryset.exclude(match_score__isnull=True).aggregate(avg=Avg('match_score'))['avg'] or 0,
    }
    return stats


def stage_summary(queryset):
    total_applications = queryset.count()
    now = timezone.now()
    summary = []

    for status in ApplicationStatus:
        stage_qs = queryset.filter(status=status.value)
        count = stage_qs.count()
        percent = round((count / total_applications) * 100, 1) if total_applications else 0
        duration_expr = ExpressionWrapper(now - F('status_changed_at'), output_field=DurationField())
        avg_duration = stage_qs.aggregate(avg_time=Avg(duration_expr))['avg_time']
        avg_days = round(avg_duration.total_seconds() / 86400, 1) if avg_duration else 0
        summary.append({
            'label': status.label,
            'value': status.value,
            'count': count,
            'percent': percent,
            'avg_days': avg_days,
        })

    return summary


def history_summary(queryset, days=7):
    cutoff = timezone.now() - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)
    app_ids = list(queryset.values_list('id', flat=True))

    recent_history = ApplicationStatusHistory.objects.filter(
        application_id__in=app_ids,
        changed_at__gte=cutoff
    ).values('new_status').annotate(count=Count('id'))

    previous_history = ApplicationStatusHistory.objects.filter(
        application_id__in=app_ids,
        changed_at__gte=prev_cutoff,
        changed_at__lt=cutoff
    ).values('new_status').annotate(count=Count('id'))

    previous_map = {item['new_status']: item['count'] for item in previous_history}
    summary = []

    for status in ApplicationStatus:
        current_count = next((item['count'] for item in recent_history if item['new_status'] == status.value), 0)
        prev_count = previous_map.get(status.value, 0)
        change = None
        if prev_count:
            change = round(((current_count - prev_count) / prev_count) * 100, 1)

        summary.append({
            'label': status.label,
            'value': status.value,
            'count': current_count,
            'change': change,
        })

    return summary


def build_pipeline_data(queryset):
    return {
        'stats': pipeline_stats(queryset),
        'stage_summary': stage_summary(queryset),
        'history_summary': history_summary(queryset),
    }
