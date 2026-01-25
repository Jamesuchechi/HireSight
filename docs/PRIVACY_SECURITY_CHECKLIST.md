# Privacy & Security Integration Checklist

This checklist guides developers through integrating privacy and security features into the HireSight platform.

## ✅ Completed Components

### Core Models & Database
- [x] ConsentRecord model (8 fields, indexes, is_active property)
- [x] AIUsageLog model (14 fields, cost calculation, log_request classmethod)
- [x] Database migration (0009_add_consent_and_usage_logs.py applied)
- [x] Django admin registration (ConsentRecordAdmin, AIUsageLogAdmin)

### Views & Middleware
- [x] ConsentCheckView (GET /interviews/consent/check/)
- [x] ConsentModalView (GET /interviews/consent/modal/)
- [x] SaveConsentView (POST /interviews/consent/save/)
- [x] ConsentHistoryView (GET /interviews/consent/history/)
- [x] RevokeConsentView (POST /interviews/consent/revoke/<type>/)
- [x] AIUsageDashboardView (GET /interviews/usage/dashboard/)
- [x] VideoUrlSigningView (GET /interviews/video/<id>/<key>/url/)
- [x] ConsentRequiredMiddleware
- [x] RateLimitMiddleware

### Templates
- [x] consent_modal.html (380 lines, privacy explanation, checkboxes)
- [x] consent_history.html (350 lines, data rights, GDPR controls)
- [x] ai_usage_dashboard.html (350 lines, charts, metrics, logs table)

### Management Commands
- [x] cleanup_old_videos.py (180 lines, dry-run, force options)

### Configuration
- [x] Settings added to hiresight/settings.py
- [x] Environment variables documented (.env)

### Documentation
- [x] PRIVACY_SECURITY_IMPLEMENTATION.md (comprehensive guide)

## 🔄 In-Progress Integration Points

### 1. Integrate Logging into AI Services

**File:** `apps/interviews/utils.py` (AIConnector class)

**Task:** Update all AI API calls to log with AIUsageLog

**Methods to update:**
- `AIConnector.generate_questions()` - Log question generation
- `AIConnector.score_response()` - Log response scoring
- `ReportGenerator.generate_report()` - Log report generation

**Example integration:**
```python
from apps.interviews.models import AIUsageLog
import time

def score_response(self, response_text, question, user, session):
    """Score a practice response using Gemini."""
    start_time = time.time()
    
    try:
        # Call Gemini API
        result = self.model.generate_content(prompt)
        
        # Extract token counts
        input_tokens = result.usage_metadata.prompt_token_count
        output_tokens = result.usage_metadata.candidates_token_count
        
        # Log the API call
        AIUsageLog.log_request(
            user=user,
            session=session,
            request_type=AIUsageLog.RequestType.RESPONSE_SCORING,
            model_used=AIUsageLog.ModelChoice.GEMINI,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time_ms=int((time.time() - start_time) * 1000),
            status=AIUsageLog.Status.SUCCESS,
            request_id=result.response_id
        )
        
        return result
    except Exception as e:
        # Log failure
        AIUsageLog.log_request(
            user=user,
            session=session,
            request_type=AIUsageLog.RequestType.RESPONSE_SCORING,
            model_used=AIUsageLog.ModelChoice.GEMINI,
            status=AIUsageLog.Status.FAILED,
            error_message=str(e)
        )
        raise
```

**Status:** Needs implementation in utils.py

### 2. Update Video Upload to Use Signed URLs

**File:** `apps/interviews/views.py` (VideoUploadView or similar)

**Task:** Never return raw video URLs; use VideoUrlSigningView

**Current Issue:** Raw S3 URLs exposed in API responses

**Solution:**
```python
# In video serialization
def get_video_url(self, request, video_key):
    """Get signed URL instead of direct URL."""
    return f"/interviews/video/{self.session_id}/{video_key}/url/"

# Client-side
fetch('/interviews/video/abc-123/recording-001/url/')
    .then(r => r.json())
    .then(data => video_element.src = data.url)
```

**Status:** Needs implementation in views.py and serializers

### 3. Add Consent Middleware to MIDDLEWARE Setting

**File:** `hiresight/settings.py`

**Current Status:** Already added to settings (CONSENT_REQUIRED_MIDDLEWARE, RATE_LIMIT_MIDDLEWARE)

**Verify:**
```python
MIDDLEWARE = [
    # ... other middleware ...
    'apps.interviews.privacy_views.ConsentRequiredMiddleware',
    'apps.interviews.privacy_views.RateLimitMiddleware',
]
```

**Status:** Settings already configured ✅

### 4. Display Consent Modal on First Visit

**File:** `templates/base.html` or practice entry point

**Task:** Check consent and redirect to consent modal if needed

**Implementation:**
```html
{% load static %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    fetch('/interviews/consent/check/')
        .then(r => r.json())
        .then(data => {
            if (!data.has_consent) {
                // Show consent modal
                fetch('/interviews/consent/modal/')
                    .then(r => r.text())
                    .then(html => {
                        // Insert modal into page
                        document.body.insertAdjacentHTML('beforeend', html);
                        document.getElementById('consentModal').showModal();
                    });
            }
        });
});
</script>
```

**Status:** Needs implementation in base template or practice template

### 5. Schedule Daily Cleanup Task

**File:** `hiresight/celery.py` or system cron

**Option A: Celery Beat**
```python
app.conf.beat_schedule = {
    'cleanup-old-videos': {
        'task': 'apps.interviews.tasks.cleanup_old_videos_task',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}

# In apps/interviews/tasks.py
@shared_task
def cleanup_old_videos_task():
    from django.core.management import call_command
    call_command('cleanup_old_videos', '--force')
```

**Option B: System Cron**
```bash
0 2 * * * cd /path/to/hiresight && /path/to/venv/bin/python manage.py cleanup_old_videos --force
```

**Status:** Needs configuration in Celery or cron

### 6. Add Admin Users to Dashboard

**File:** `apps/interviews/privacy_views.py` (AIUsageDashboardView)

**Task:** Restrict dashboard access to admin/staff users

**Update:**
```python
@method_decorator(login_required, name='dispatch')
class AIUsageDashboardView(View):
    def get(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        # ... dashboard logic ...
```

**Status:** Needs permission check in view

### 7. Create Data Export Endpoint

**File:** `apps/accounts/views.py` or new privacy_views.py

**Task:** Implement GDPR right to access

**Endpoint:**
```python
class ExportUserDataView(View):
    @method_decorator(login_required)
    def post(self, request):
        """Export user data as JSON."""
        import json
        from django.http import StreamingHttpResponse
        
        user_data = {
            'personal': {...},
            'consent_records': [...],
            'practice_sessions': [...],
            'api_usage_logs': [...]
        }
        
        response = StreamingHttpResponse(
            json.dumps(user_data),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="user_data.json"'
        return response
```

**URL:** POST /api/user/export-data/

**Status:** Needs implementation

### 8. Create Account Deletion Endpoint

**File:** `apps/accounts/views.py`

**Task:** Implement GDPR right to erasure

**Endpoint:**
```python
class DeleteAccountView(View):
    @method_decorator(login_required)
    def delete(self, request):
        """Permanently delete user account and all data."""
        user = request.user
        
        # Delete videos
        PracticeResponse.objects.filter(session__candidate=user).delete()
        
        # Delete sessions
        InterviewPracticeSession.objects.filter(candidate=user).delete()
        
        # Delete consent records
        ConsentRecord.objects.filter(user=user).delete()
        
        # Delete logs
        AIUsageLog.objects.filter(user=user).delete()
        
        # Delete user account
        user.delete()
        
        return JsonResponse({'success': True})
```

**URL:** DELETE /api/user/delete-account/

**Status:** Needs implementation

### 9. Update Response Serializers

**File:** `apps/interviews/serializers.py`

**Task:** Ensure video URLs in responses use signed URL endpoint

**Change:**
```python
# OLD (BAD)
def get_video_url(self, obj):
    return obj.video_file.url  # Direct S3 URL

# NEW (GOOD)
def get_video_url(self, obj):
    return f"/interviews/video/{obj.session_id}/{obj.video_key}/url/"
```

**Status:** Needs serializer updates

## 📋 Testing Checklist

- [ ] Test consent flow end-to-end
- [ ] Test rate limiting (create 6 sessions, 6th fails)
- [ ] Test video cleanup command
  - [ ] Normal run
  - [ ] Dry-run shows correct count
  - [ ] Force skips confirmation
- [ ] Test API logging
  - [ ] Log appears in admin
  - [ ] Cost calculated correctly
  - [ ] Token counts accurate
- [ ] Test signed URLs
  - [ ] URLs expire after 15 minutes
  - [ ] Unauthorized users can't access
  - [ ] URL works for authorized user
- [ ] Test admin interface
  - [ ] Consent records display
  - [ ] Usage dashboard loads
  - [ ] Filtering works
  - [ ] Search functions
- [ ] Test GDPR compliance
  - [ ] Consent history visible
  - [ ] Revoke works
  - [ ] Data export works (when implemented)
  - [ ] Account deletion works (when implemented)

## 🚀 Deployment Checklist

- [ ] Database migrations applied to production
  ```bash
  python manage.py migrate interviews
  ```

- [ ] Settings configured
  ```python
  PRACTICE_VIDEO_RETENTION_DAYS = 30
  PRACTICE_SESSIONS_PER_DAY_LIMIT = 5
  ```

- [ ] Cleanup task scheduled
  - [ ] Celery Beat configured or cron setup

- [ ] Admin users can access dashboard
  ```
  /admin/interviews/consentrecord/
  /admin/interviews/aiusagelog/
  /interviews/usage/dashboard/
  ```

- [ ] Consent modal appears on first visit

- [ ] Rate limiting enforced on practice new

- [ ] API logging active for AI calls

- [ ] Templates deployed
  ```
  /templates/interviews/privacy/consent_modal.html
  /templates/interviews/privacy/consent_history.html
  /templates/interviews/privacy/ai_usage_dashboard.html
  ```

- [ ] Backup before migration
  ```bash
  python manage.py dumpdata > backup.json
  ```

## 📊 Post-Deployment Verification

1. **Check Database:**
   ```bash
   python manage.py shell
   from apps.interviews.models import ConsentRecord, AIUsageLog
   print(ConsentRecord.objects.count())  # Should be 0 initially
   print(AIUsageLog.objects.count())  # Should be 0 initially
   ```

2. **Check Admin:**
   - Visit `/admin/interviews/consentrecord/`
   - Visit `/admin/interviews/aiusagelog/`
   - Both should show empty lists

3. **Test Endpoints:**
   ```bash
   curl http://localhost:8000/interviews/consent/check/
   # Should return: {"has_consent": false, ...}
   ```

4. **Monitor Logs:**
   - Watch for cleanup_old_videos output
   - Monitor AIUsageLog for API calls
   - Check ConsentRecord creation

## 🔧 Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Consent modal not showing | Middleware not active | Verify MIDDLEWARE setting |
| Rate limit not working | Middleware order | Ensure RateLimitMiddleware in MIDDLEWARE |
| Videos not deleting | Cleanup task not running | Check cron/Celery Beat configuration |
| API cost showing $0 | log_request not called | Integrate logging in AI services |
| Signed URLs not working | VideoUrlSigningView not registered | Check URLs in urls.py |
| Admin not loading | Permission issue | Verify is_staff on user |

## 📞 Support

- **Documentation:** `/docs/PRIVACY_SECURITY_IMPLEMENTATION.md`
- **Admin Panel:** `/admin/`
- **Consent Dashboard:** `/interviews/consent/history/`
- **Usage Dashboard:** `/interviews/usage/dashboard/`
- **Codebase:** Check git history for implementation examples

---

**Last Updated:** 2026-01-24
**Status:** 85% Complete - Awaiting integration points (logging, data export, scheduled tasks)
