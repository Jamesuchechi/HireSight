# Privacy & Security Implementation Guide

## Overview

This document details the comprehensive privacy and security implementation for the HireSight interview practice platform, including video consent management, data retention policies, encryption, rate limiting, and comprehensive API usage logging.

## Table of Contents

1. [Consent Management](#consent-management)
2. [Video Retention Policy](#video-retention-policy)
3. [Rate Limiting](#rate-limiting)
4. [API Usage Logging](#api-usage-logging)
5. [Video Security](#video-security)
6. [Admin Management](#admin-management)
7. [Configuration](#configuration)

---

## Consent Management

### Overview
The consent system ensures users explicitly agree to video recording, AI analysis, data storage, and performance tracking before using the practice platform.

### Models

#### ConsentRecord
Tracks all user consent actions with audit trail capabilities.

**Fields:**
- `user` (ForeignKey): User who gave/revoked consent
- `consent_type` (CharField): Type of consent
  - `VIDEO_RECORDING`: Recording practice sessions
  - `AI_ANALYSIS`: Using AI for scoring and feedback
  - `DATA_STORAGE`: Storing user data long-term
  - `PERFORMANCE_TRACKING`: Tracking analytics
- `granted` (BooleanField): True if consent given, False if declined
- `granted_at` (DateTimeField): When consent was recorded (auto-set)
- `expires_at` (DateTimeField, nullable): Optional expiration date
- `ip_address` (GenericIPAddressField): Client IP for security audit
- `user_agent` (TextField): Device information
- `notes` (TextField): Additional context

**Indexes:**
- (user, consent_type) - for quick user consent lookup
- (granted_at) - for auditing

**Methods:**
- `is_active` property: Returns True if consent is still valid

### Views

#### ConsentCheckView (GET /interviews/consent/check/)
Check if user has active consent.

**Response:**
```json
{
    "has_consent": true,
    "consent_granted_at": "2026-01-24T14:30:00Z"
}
```

#### ConsentModalView (GET /interviews/consent/modal/)
Display consent form with privacy explanations.

**Features:**
- 5 information sections
- 4 required checkboxes
- JavaScript validation
- Privacy policy links

#### SaveConsentView (POST /interviews/consent/save/)
Process consent submission.

**Request:**
```json
{
    "consent_types": ["VIDEO_RECORDING", "AI_ANALYSIS", "DATA_STORAGE"],
    "granted": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Consent saved successfully",
    "granted": true
}
```

#### ConsentHistoryView (GET /interviews/consent/history/)
Display user's complete consent history with ability to revoke.

#### RevokeConsentView (POST /interviews/consent/revoke/<consent_type>/)
Revoke specific consent.

**Example:**
```
POST /interviews/consent/revoke/VIDEO_RECORDING/
```

**Response:**
```json
{
    "success": true,
    "message": "Consent revoked successfully"
}
```

### Consent Flow

1. **First Visit**: User redirected to consent modal
2. **Review**: User reads privacy information (5 sections)
3. **Confirm**: User checks 4 required consent boxes
4. **Accept**: Consent saved to ConsentRecord
5. **Access**: User can now access practice sessions
6. **Revoke**: User can revoke consent anytime in history page

---

## Video Retention Policy

### Policy Details

| Data Type | Retention Period | Purpose |
|-----------|------------------|---------|
| Raw Video Files | 30 days (configurable) | Practice playback, initial analysis |
| Performance Metrics | 2 years | Long-term progress tracking |
| Anonymized Analytics | Indefinite | Service improvement |

### Cleanup Process

#### Management Command: cleanup_old_videos

**Purpose:** Automatically delete videos older than retention period

**Usage:**
```bash
# Normal run with confirmation
python manage.py cleanup_old_videos

# Override retention days
python manage.py cleanup_old_videos --days 45

# Dry-run (show what would be deleted)
python manage.py cleanup_old_videos --dry-run

# Force delete without confirmation
python manage.py cleanup_old_videos --force

# All options combined
python manage.py cleanup_old_videos --days 45 --dry-run --force
```

**Logic:**
1. Calculate cutoff_date = now() - timedelta(days=retention_days)
2. Query PracticeResponse records with created_at < cutoff_date
3. Extract video file paths from video_analysis_metrics JSON
4. Delete files from storage (AWS S3, local, etc.)
5. Update database records (remove video references)
6. Log operation with counts and status

**Output Example:**
```
Starting video cleanup process...
Retention period: 30 days
Cutoff date: 2025-12-25 14:53:00
Found 47 videos to delete

Deleting videos:
✓ media/screening_resumes/session-123/video-001.mp4
✓ media/screening_resumes/session-124/video-002.webm
✗ media/screening_resumes/session-125/video-003.mp4 (File not found)
...

Summary:
- Deleted: 46 videos
- Skipped: 1 video
- Total size freed: 2.3 GB
- Time taken: 45 seconds

✓ Cleanup completed successfully
```

### Scheduling

**Option 1: Celery Beat** (if using Celery)
```python
# In celery.py
app.conf.beat_schedule = {
    'cleanup-old-videos': {
        'task': 'apps.interviews.tasks.cleanup_old_videos',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

**Option 2: System Cron**
```bash
# /etc/cron.d/hiresight
0 2 * * * cd /path/to/hiresight && /path/to/venv/bin/python manage.py cleanup_old_videos --force
```

**Option 3: Django APScheduler**
```python
# In apps.py ready()
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_videos, 'cron', hour=2, minute=0)
scheduler.start()
```

---

## Rate Limiting

### Purpose
Prevent abuse and ensure fair platform usage with configurable daily limits.

### Implementation

#### RateLimitMiddleware

**Location:** `apps/interviews/privacy_views.py`

**Configuration:**
```python
# In settings.py
PRACTICE_SESSIONS_PER_DAY_LIMIT = 5  # Default: 5 sessions per day
```

**Logic:**
1. Check if request is to `/interviews/practice/new/`
2. Count sessions created by user today: `InterviewPracticeSession.objects.filter(candidate=user, created_at__date=today).count()`
3. If count >= limit and not premium user, return 429 error
4. Allow unlimited for premium/staff users

**Response (429 Too Many Requests):**
```json
{
    "error": "Too many requests",
    "message": "You have reached your daily practice limit (5 sessions). Please try again tomorrow.",
    "limit": 5,
    "retry_after": 86400
}
```

**Premium User Exemption:**
```python
def _is_premium_user(self, user):
    """Check if user has premium subscription."""
    return (user.is_staff or 
            user.is_superuser or 
            hasattr(user, 'subscription') and user.subscription.is_active)
```

### Monitoring

Track rate limit hits in admin dashboard:
```
/interviews/usage/dashboard/ → AIUsageLog records
```

---

## API Usage Logging

### Overview
Comprehensive logging of all AI API calls for auditing, cost tracking, and performance monitoring.

### AIUsageLog Model

**Fields:**
- `user` (ForeignKey): User who triggered the API call
- `session` (ForeignKey): Practice session context (optional)
- `request_type` (CharField): Type of request
  - `QUESTION_GENERATION`: Generating practice questions
  - `RESPONSE_SCORING`: Scoring user responses
  - `REPORT_GENERATION`: Creating performance reports
  - `FEEDBACK`: Generating feedback
- `model_used` (CharField): Which AI model
  - `GEMINI`: Google Gemini
  - `MISTRAL`: Mistral AI
  - `OPENAI`: OpenAI GPT
- `input_tokens` (PositiveIntegerField): Request token count
- `output_tokens` (PositiveIntegerField): Response token count
- `total_tokens` (PositiveIntegerField): Sum of input + output
- `estimated_cost_usd` (Decimal): Calculated cost ($)
- `response_time_ms` (PositiveIntegerField): Latency in milliseconds
- `status` (CharField): Result status
  - `SUCCESS`: Completed normally
  - `PARTIAL`: Partial response received
  - `FAILED`: Request failed
  - `FALLBACK`: Fallback model used
- `error_message` (TextField): Error details if failed
- `request_id` (CharField): API provider's request ID
- `created_at` (DateTimeField): When request was made

**Indexes:**
- (user, created_at) - for user API usage history
- (session) - for session-specific queries
- (model_used) - for model performance tracking
- (created_at) - for time-based reports

### Logging API Calls

#### Using AIUsageLog.log_request()

**Signature:**
```python
@classmethod
def log_request(cls, user, session, request_type, model_used, 
               input_tokens=0, output_tokens=0, response_time_ms=0, 
               status='SUCCESS', error_message='', request_id=''):
    """Log an AI API request with automatic cost calculation."""
```

**Example:**
```python
from apps.interviews.models import AIUsageLog

# In your AI service handler
try:
    response = gemini_model.generate_content(prompt, generation_config={...})
    input_tokens = response.usage_metadata.prompt_token_count
    output_tokens = response.usage_metadata.candidates_token_count
    
    AIUsageLog.log_request(
        user=request.user,
        session=practice_session,
        request_type=AIUsageLog.RequestType.QUESTION_GENERATION,
        model_used=AIUsageLog.ModelChoice.GEMINI,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        response_time_ms=duration_ms,
        status=AIUsageLog.Status.SUCCESS,
        request_id=response.response_id
    )
except Exception as e:
    AIUsageLog.log_request(
        user=request.user,
        session=practice_session,
        request_type=AIUsageLog.RequestType.QUESTION_GENERATION,
        model_used=AIUsageLog.ModelChoice.GEMINI,
        status=AIUsageLog.Status.FAILED,
        error_message=str(e)
    )
```

### Cost Calculation

**Pricing Model (per 1K tokens):**

| Model | Input Cost | Output Cost | Notes |
|-------|-----------|------------|-------|
| Gemini | $0.001 | $0.001 | Combined rate |
| Mistral | $0.0002 | $0.0002 | Economical option |
| OpenAI | $0.0015 | $0.002 | Premium option |

**Formula:**
```
estimated_cost_usd = (total_tokens / 1000) * cost_per_1k_tokens
```

**Example:**
- 1000 input tokens + 500 output tokens = 1500 total
- Using Gemini: (1500 / 1000) * $0.001 = $0.0015

### Admin Dashboard

#### AIUsageDashboardView (GET /interviews/usage/dashboard/)

**Features:**
- 4 metric cards (requests, tokens, cost, success rate)
- 2 breakdown charts
  - Cost by AI model
  - Cost by request type
- Recent API calls table (50 most recent)
- Date range filtering (7/30/90 days)
- Performance statistics

**Metrics Calculated:**
```python
# Aggregations
total_requests = AIUsageLog.objects.filter(created_at__gte=start_date).count()
total_tokens = AIUsageLog.objects.filter(...).aggregate(Sum('total_tokens'))['total_tokens__sum']
total_cost = AIUsageLog.objects.filter(...).aggregate(Sum('estimated_cost_usd'))['estimated_cost_usd__sum']
success_rate = (success_count / total_count) * 100

# By model breakdown
cost_by_model = AIUsageLog.objects.filter(...).values('model_used').annotate(
    requests=Count('id'),
    tokens=Sum('total_tokens'),
    cost=Sum('estimated_cost_usd')
)

# By request type breakdown
cost_by_type = AIUsageLog.objects.filter(...).values('request_type').annotate(
    requests=Count('id'),
    cost=Sum('estimated_cost_usd')
)
```

### Querying Usage Data

**Example Queries:**

```python
from apps.interviews.models import AIUsageLog
from django.db.models import Sum, Count

# Total cost by user
AIUsageLog.objects\
    .filter(created_at__date='2026-01-24')\
    .values('user__email')\
    .annotate(total_cost=Sum('estimated_cost_usd'))\
    .order_by('-total_cost')

# Failed requests
AIUsageLog.objects.filter(status='FAILED')

# Most used models
AIUsageLog.objects\
    .values('model_used')\
    .annotate(count=Count('id'))\
    .order_by('-count')

# Expensive requests
AIUsageLog.objects\
    .filter(estimated_cost_usd__gt=0.01)\
    .order_by('-estimated_cost_usd')[:10]

# Response time statistics
AIUsageLog.objects\
    .aggregate(
        avg=Avg('response_time_ms'),
        max=Max('response_time_ms'),
        min=Min('response_time_ms')
    )
```

---

## Video Security

### Signed URLs

#### VideoUrlSigningView (GET /interviews/video/<session_id>/<video_key>/url/)

**Purpose:** Generate temporary signed URLs for secure video access

**Features:**
- Verify session ownership
- Generate 15-minute expiring signed URLs
- Prevent direct video access
- Audit access attempts

**Example Request:**
```
GET /interviews/video/abc-123-def/recording-001/url/
```

**Response:**
```json
{
    "url": "https://s3.amazonaws.com/hiresight/video.mp4?X-Amz-Signature=...",
    "expires_in": 900,
    "content_type": "video/mp4"
}
```

**Implementation:**
```python
class VideoUrlSigningView(View):
    """Generate signed URLs for video access."""
    
    def get(self, request, session_id, video_key):
        # 1. Verify session ownership
        session = InterviewPracticeSession.objects.get(id=session_id)
        if session.candidate != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # 2. Generate signed URL
        from django.core.files.storage import default_storage
        url = default_storage.url(
            f'videos/{session_id}/{video_key}',
            parameters={'X-Amz-Expires': 900}
        )
        
        # 3. Log access
        AIUsageLog.objects.create(
            user=request.user,
            session=session,
            request_type='video_access',
            status='SUCCESS'
        )
        
        return JsonResponse({
            'url': url,
            'expires_in': 900
        })
```

### Encryption

**S3 Configuration:**
```python
AWS_S3_ENCRYPTION = {
    'bucket_encryption': {
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'AES256'
            }
        }]
    }
}
```

**TLS/HTTPS:**
- All video URLs use HTTPS
- S3 enforces SSL/TLS
- Browser supports H.264/VP9 codecs with DRM ready

---

## Admin Management

### Consent Records Admin

**URL:** `/admin/interviews/consentrecord/`

**Features:**
- List all consent records with status badges
- Filter by consent type, granted status, date
- Search by user email, IP address
- View full audit trail
- Color-coded badges

**List Display:**
- User (email)
- Consent Type (with color badge)
- Status (Granted/Declined)
- Granted At (date)
- IP Address
- Expires At

**Filtering:**
- By consent type
- By granted status
- By date range
- By expiration date

### API Usage Log Admin

**URL:** `/admin/interviews/aiusagelog/`

**Features:**
- Monitor all API calls
- Track costs and token usage
- Identify failed requests
- Performance analytics
- Sortable columns

**List Display:**
- Request ID (shortened)
- User (email)
- Model Used (with badge)
- Request Type (with icon)
- Total Tokens
- Cost (USD, highlighted)
- Status (Success/Failure/Fallback)
- Response Time (ms)
- Created At

**Filtering:**
- By AI model
- By request type
- By status
- By date range

**Searchable:**
- Request ID
- User email
- Session ID

**Date Hierarchy:**
- By creation date

---

## Configuration

### Required Settings

Add to `hiresight/settings.py`:

```python
# ==================== PRIVACY & SECURITY SETTINGS ====================

# Video retention policy (days)
PRACTICE_VIDEO_RETENTION_DAYS = int(os.environ.get('PRACTICE_VIDEO_RETENTION_DAYS', 30))

# Rate limiting for practice sessions
PRACTICE_SESSIONS_PER_DAY_LIMIT = int(os.environ.get('PRACTICE_SESSIONS_PER_DAY_LIMIT', 5))

# AI model pricing (per 1K tokens)
AI_MODEL_PRICING = {
    'gemini': 0.001,      # $0.001 per 1K tokens
    'mistral': 0.0002,    # $0.0002 per 1K tokens
    'openai': 0.0015,     # $0.0015 per 1K tokens
}

# Consent expiration (days, None = never)
CONSENT_EXPIRATION_DAYS = int(os.environ.get('CONSENT_EXPIRATION_DAYS', 365))

# Video URL signing expiration (seconds)
VIDEO_SIGNED_URL_EXPIRATION_SECONDS = int(os.environ.get('VIDEO_SIGNED_URL_EXPIRATION_SECONDS', 900))

# Consent required paths
CONSENT_REQUIRED_PATHS = [
    '/interviews/practice/',
]

# Consent exempt paths
CONSENT_EXEMPT_PATHS = [
    '/interviews/consent/',
    '/accounts/',
    '/api/auth/',
    '/static/',
    '/media/',
]
```

### Environment Variables

```bash
# .env
PRACTICE_VIDEO_RETENTION_DAYS=30
PRACTICE_SESSIONS_PER_DAY_LIMIT=5
CONSENT_EXPIRATION_DAYS=365
VIDEO_SIGNED_URL_EXPIRATION_SECONDS=900
```

---

## Testing

### Test Consent Flow

```python
from django.test import TestCase, Client
from apps.interviews.models import ConsentRecord
from apps.accounts.models import User

class ConsentFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test@example.com', 'password')
        self.client = Client()
        self.client.login(username='test@example.com', password='password')
    
    def test_consent_check(self):
        response = self.client.get('/interviews/consent/check/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['has_consent'])
    
    def test_save_consent(self):
        response = self.client.post('/interviews/consent/save/', {
            'consent_types': ['VIDEO_RECORDING', 'AI_ANALYSIS'],
            'granted': True
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ConsentRecord.objects.filter(user=self.user, granted=True).exists())
    
    def test_revoke_consent(self):
        ConsentRecord.objects.create(
            user=self.user,
            consent_type='VIDEO_RECORDING',
            granted=True,
            ip_address='127.0.0.1'
        )
        
        response = self.client.post('/interviews/consent/revoke/VIDEO_RECORDING/')
        self.assertEqual(response.status_code, 200)
        
        record = ConsentRecord.objects.get(user=self.user, consent_type='VIDEO_RECORDING')
        self.assertFalse(record.granted)
```

### Test Rate Limiting

```python
def test_rate_limit(self):
    # Create 5 sessions (limit)
    for i in range(5):
        self.client.post('/interviews/practice/new/')
    
    # 6th attempt should fail
    response = self.client.post('/interviews/practice/new/')
    self.assertEqual(response.status_code, 429)
    
    data = response.json()
    self.assertEqual(data['limit'], 5)
```

### Test Logging

```python
def test_api_logging(self):
    from apps.interviews.models import AIUsageLog
    
    AIUsageLog.log_request(
        user=self.user,
        session=self.session,
        request_type='question_gen',
        model_used='gemini',
        input_tokens=1000,
        output_tokens=500,
        response_time_ms=1234,
        status='SUCCESS',
        request_id='req-123'
    )
    
    log = AIUsageLog.objects.latest('created_at')
    self.assertEqual(log.total_tokens, 1500)
    self.assertEqual(float(log.estimated_cost_usd), 0.0015)
```

---

## Troubleshooting

### Consent Not Appearing

**Problem:** Users not seeing consent modal

**Solution:**
1. Check ConsentRecord exists: `ConsentRecord.objects.filter(user=user, granted=True).exists()`
2. Verify middleware is active in settings.py
3. Check template is at `templates/interviews/privacy/consent_modal.html`

### Videos Not Cleaning Up

**Problem:** Videos older than retention period still exist

**Solution:**
1. Check PRACTICE_VIDEO_RETENTION_DAYS setting
2. Verify cleanup_old_videos command runs: `python manage.py cleanup_old_videos --dry-run`
3. Check storage backend is correctly configured
4. Verify database queries: `PracticeResponse.objects.filter(created_at__lt=cutoff_date)`

### High API Costs

**Problem:** Unexpected high cost in usage dashboard

**Solution:**
1. Check AIUsageLog records: `AIUsageLog.objects.order_by('-estimated_cost_usd')[:10]`
2. Identify expensive requests by model
3. Review token usage patterns
4. Implement fallback models for cost reduction

### Rate Limit False Positives

**Problem:** Premium users hitting rate limit

**Solution:**
1. Check `_is_premium_user()` logic
2. Verify subscription status in user record
3. Test: `User.objects.filter(is_staff=True, is_superuser=True)`

---

## Security Best Practices

1. **Always use signed URLs for video access** - Never expose direct S3 URLs
2. **Encrypt videos in transit** - Enforce HTTPS/TLS
3. **Audit consent changes** - Use ConsentRecord for compliance
4. **Monitor API costs** - Review AIUsageLog regularly
5. **Regular cleanup** - Schedule cleanup_old_videos daily
6. **Rate limit enforcement** - Prevent abuse and fair access
7. **GDPR compliance** - Support data export and deletion

---

## Compliance

### GDPR Requirements Met

✅ **Right to Know** - Consent modal explains data usage
✅ **Right to Access** - Users can view consent history and data via dashboard
✅ **Right to Rectify** - Edit personal information in profile
✅ **Right to Erasure** - Delete all personal data and videos
✅ **Right to Withdraw** - Revoke consent anytime
✅ **Data Minimization** - Only collect necessary data
✅ **Storage Limitation** - Automatic video cleanup after 30 days
✅ **Audit Trail** - ConsentRecord tracks all actions with timestamp, IP, device

### CCPA Requirements Met

✅ **Disclosure** - Privacy policy and consent modal
✅ **Access** - Users can view their data
✅ **Deletion** - Request deletion via privacy dashboard
✅ **Opt-out** - Decline consent and revoke anytime
✅ **No Discrimination** - No service degradation for declining optional consents

---

## Support

For issues or questions:
- Admin Dashboard: `/admin/interviews/`
- Consent History: `/interviews/consent/history/`
- Usage Dashboard: `/interviews/usage/dashboard/`
- Documentation: `/docs/`

