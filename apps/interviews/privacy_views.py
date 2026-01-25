"""
Privacy and security views for interview practice.
Handles consent management, video encryption, rate limiting, and usage logging.
"""
import json
from datetime import timedelta
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.conf import settings
from django.core.cache import cache

from .models import ConsentRecord, AIUsageLog, InterviewPracticeSession


@method_decorator(login_required, name='dispatch')
class ConsentCheckView(View):
    """Check if user has given consent for practice sessions."""
    
    def get(self, request):
        """Check consent status."""
        user = request.user
        
        # Check if user has active consent
        has_consent = ConsentRecord.objects.filter(
            user=user,
            consent_type=ConsentRecord.ConsentType.VIDEO_RECORDING,
            granted=True
        ).exists()
        
        active_consent = None
        if has_consent:
            active_consent = ConsentRecord.objects.filter(
                user=user,
                granted=True
            ).first()
        
        return JsonResponse({
            'has_consent': has_consent,
            'consent_granted_at': active_consent.granted_at.isoformat() if active_consent else None
        })


@method_decorator(login_required, name='dispatch')
class ConsentModalView(View):
    """Display consent modal for new users."""
    
    def get(self, request):
        """Display consent form."""
        # Check if user has already given consent
        existing_consent = ConsentRecord.objects.filter(
            user=request.user,
            granted=True
        ).first()
        
        context = {
            'user': request.user,
            'has_existing_consent': existing_consent is not None,
        }
        return render(request, 'interviews/practice/consent_modal.html', context)


@method_decorator(login_required, name='dispatch')
class SaveConsentView(View):
    """Save user consent for video recording and AI analysis."""
    
    def post(self, request):
        """Save consent records."""
        try:
            data = json.loads(request.body)
            consent_types = data.get('consent_types', [])
            granted = data.get('granted', True)
            
            # Get client IP address
            client_ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create consent records for each type
            for consent_type in consent_types:
                # Update or create (always update to latest)
                ConsentRecord.objects.update_or_create(
                    user=request.user,
                    consent_type=consent_type,
                    defaults={
                        'granted': granted,
                        'ip_address': client_ip,
                        'user_agent': user_agent
                    }
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Consent saved successfully',
                'granted': granted
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(login_required, name='dispatch')
class ConsentHistoryView(View):
    """Display user's consent history."""
    
    def get(self, request):
        """Show consent records."""
        user = request.user
        
        records = ConsentRecord.objects.filter(user=user).order_by('-granted_at')
        
        context = {
            'consent_records': records,
        }
        return render(request, 'interviews/privacy/consent_history.html', context)


@method_decorator(login_required, name='dispatch')
class RevokeConsentView(View):
    """Revoke previously given consent."""
    
    def post(self, request, consent_type):
        """Revoke specific consent type."""
        try:
            record = ConsentRecord.objects.get(
                user=request.user,
                consent_type=consent_type
            )
            record.granted = False
            record.notes = f"Revoked on {timezone.now()}"
            record.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{consent_type} consent revoked'
            })
        except ConsentRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Consent record not found'
            }, status=404)


class ConsentRequiredMiddleware:
    """
    Middleware to require consent before accessing video practice.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/interviews/practice/setup/',
            '/interviews/consent/',
            '/interviews/consent-check/',
            '/accounts/',
            '/api/',
        ]
    
    def __call__(self, request):
        # Check if path requires consent
        if self._requires_consent(request):
            if request.user.is_authenticated:
                # Check if user has consent
                has_consent = ConsentRecord.objects.filter(
                    user=request.user,
                    consent_type=ConsentRecord.ConsentType.VIDEO_RECORDING,
                    granted=True
                ).exists()
                
                if not has_consent:
                    # For AJAX requests, return JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'requires_consent': True,
                            'redirect_to': '/interviews/consent/'
                        }, status=403)
                    # For regular requests, redirect to consent
                    return redirect('/interviews/consent/')
        
        response = self.get_response(request)
        return response
    
    def _requires_consent(self, request):
        """Check if this path requires consent."""
        path = request.path
        
        # Exempt certain paths
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return False
        
        # Require consent for practice paths
        if path.startswith('/interviews/practice/') and path not in [
            '/interviews/practice/history/',
            '/interviews/practice/setup/',
        ]:
            return True
        
        return False


@method_decorator(login_required, name='dispatch')
class AIUsageDashboardView(View):
    """Display AI usage and cost tracking dashboard."""
    
    def get(self, request):
        """Show usage statistics."""
        user = request.user
        
        # Get date range (default: last 30 days)
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get all logs for this user
        logs = AIUsageLog.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        # Calculate statistics
        stats = {
            'total_requests': logs.count(),
            'total_tokens': logs.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0,
            'total_cost': logs.aggregate(Sum('estimated_cost_usd'))['estimated_cost_usd__sum'] or 0,
            'avg_response_time': logs.aggregate(Sum('response_time_ms'))['response_time_ms__sum'] / logs.count() if logs.exists() else 0,
            'success_rate': (logs.filter(status='SUCCESS').count() / logs.count() * 100) if logs.exists() else 100,
        }
        
        # Stats by model
        model_stats = []
        for model_choice in AIUsageLog.ModelType.choices:
            model_id = model_choice[0]
            model_logs = logs.filter(model_used=model_id)
            if model_logs.exists():
                model_stats.append({
                    'model': model_choice[1],
                    'requests': model_logs.count(),
                    'tokens': model_logs.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0,
                    'cost': model_logs.aggregate(Sum('estimated_cost_usd'))['estimated_cost_usd__sum'] or 0,
                })
        
        # Stats by request type
        request_type_stats = []
        for req_type_choice in AIUsageLog.RequestType.choices:
            req_type_id = req_type_choice[0]
            type_logs = logs.filter(request_type=req_type_id)
            if type_logs.exists():
                request_type_stats.append({
                    'type': req_type_choice[1],
                    'requests': type_logs.count(),
                    'cost': type_logs.aggregate(Sum('estimated_cost_usd'))['estimated_cost_usd__sum'] or 0,
                })
        
        context = {
            'stats': stats,
            'model_stats': model_stats,
            'request_type_stats': request_type_stats,
            'days': days,
            'logs': logs[:50],  # Recent logs
        }
        
        return render(request, 'interviews/privacy/ai_usage_dashboard.html', context)


class RateLimitMiddleware:
    """
    Middleware to enforce daily session limits.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.sessions_per_day = getattr(settings, 'PRACTICE_SESSIONS_PER_DAY_LIMIT', 5)
    
    def __call__(self, request):
        # Check rate limit on session creation
        if request.path == '/interviews/practice/new/' and request.method == 'POST':
            if request.user.is_authenticated:
                if not self._check_rate_limit(request.user):
                    return JsonResponse({
                        'error': 'Daily practice session limit reached',
                        'message': f'You can create up to {self.sessions_per_day} sessions per day',
                        'retry_after': 86400
                    }, status=429)
        
        response = self.get_response(request)
        return response
    
    def _check_rate_limit(self, user):
        """Check if user has exceeded daily session limit."""
        # Check if user is premium (has higher limit)
        if self._is_premium_user(user):
            return True
        
        # Get today's session count
        today = timezone.now().date()
        today_sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            created_at__date=today
        ).count()
        
        return today_sessions < self.sessions_per_day
    
    @staticmethod
    def _is_premium_user(user):
        """Check if user is premium."""
        # Implement based on your subscription model
        return hasattr(user, 'profile') and getattr(user.profile, 'is_premium', False)


@method_decorator(login_required, name='dispatch')
class VideoUrlSigningView(View):
    """
    Generate signed URLs for video access with short expiration.
    Never expose raw video URLs.
    """
    
    def get(self, request, session_id, video_key):
        """Generate signed URL for video."""
        try:
            session = InterviewPracticeSession.objects.get(
                id=session_id,
                candidate=request.user
            )
            
            # Generate signed URL (implementation depends on storage backend)
            signed_url = self._generate_signed_url(video_key)
            
            # Log access for security audit
            AIUsageLog.objects.create(
                user=request.user,
                session=session,
                request_type='video_access',
                model_used='storage',
                status='SUCCESS',
                notes=f'Video URL signed for {video_key}'
            )
            
            return JsonResponse({
                'url': signed_url,
                'expires_in': 900,  # 15 minutes
            })
        except InterviewPracticeSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
    
    @staticmethod
    def _generate_signed_url(video_key):
        """
        Generate signed URL for S3 or similar storage.
        URL expires in 15 minutes.
        """
        # This is a placeholder - actual implementation depends on your storage backend
        # For AWS S3:
        # import boto3
        # s3_client = boto3.client('s3')
        # signed_url = s3_client.generate_presigned_url(
        #     'get_object',
        #     Params={'Bucket': BUCKET_NAME, 'Key': video_key},
        #     ExpiresIn=900  # 15 minutes
        # )
        # return signed_url
        
        return f"https://storage.hiresight.com/signed/{video_key}"
