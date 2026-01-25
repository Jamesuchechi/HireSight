# Interview Practice UX - Integration Guide

## Quick Start

### 1. Database Setup
```bash
cd /home/jamesuchechi/Projects/HireSight
source venv/bin/activate
python manage.py migrate interviews
```

### 2. Include Setup Modal in Practice Page
```html
<!-- In any practice initiation template -->
{% include 'interviews/practice/session_setup_modal.html' %}
{% include 'interviews/practice/warmup_flow.html' %}
```

### 3. Add to Existing Practice Question Template
```html
<!-- In practice_question.html -->
{% include 'interviews/practice/session_controls.html' %}

<script>
// Make sure VideoAnalyzer is initialized
// Session controls will automatically integrate with it
</script>
```

### 4. Add Dashboard Link
```html
<!-- In main dashboard or navigation -->
<a href="{% url 'interviews:practice_history' %}">
    <i class="fas fa-chart-line"></i> Practice History
</a>
```

---

## URL Mapping

| Feature | URL | View | Method |
|---------|-----|------|--------|
| Setup | `/interviews/practice/setup/` | PracticeSetupView | GET |
| Save Setup | `/interviews/practice/setup/save/` | SaveSessionSetupView | POST |
| Warmup | `/interviews/practice/warmup/<id>/` | WarmupFlowView | GET |
| Complete Warmup | `/interviews/practice/warmup/<id>/complete/` | CompleteWarmupView | POST |
| History | `/interviews/practice/history/` | PracticeHistoryDashboardView | GET |
| Progress | `/interviews/practice/session/<id>/progress/` | SessionProgressView | GET |
| Controls | `/interviews/practice/session/<id>/controls/` | SessionControlsView | POST |

---

## JavaScript API Reference

### Session Setup
```javascript
// Validate form
validateSetupForm()  // Returns: boolean

// Save configuration
saveSetupData()  // Sends POST to /interviews/practice/setup/save/

// Load data
loadSetupData()  // Retrieves from sessionStorage

// Edit setup
editSetup()  // Shows setup modal again
```

### Warmup Flow
```javascript
// Start tests
startCameraTest()      // Initialize camera stream
startMicTest()         // Capture and visualize audio
startTestQuestion()    // Begin practice question

// Visualize audio
visualizeMicLevel()    // Real-time frequency visualization

// Navigation
nextStep()  // Move to next warmup step
prevStep()  // Go back
```

### Session Controls
```javascript
// Control functions
togglePause()          // Pause/Resume
showSkipModal()        // Show skip confirmation
confirmSkip()          // Skip current question
showRerecordModal()    // Show re-record confirmation
confirmRerecord()      // Re-record response
showExitModal()        // Show exit confirmation
confirmExit()          // Exit session

// Timer management
startTimer()           // Begin question timer
resetTimer()           // Reset to full time
updateTimerDisplay()   // Update UI with time
onTimeExpired()        // Handle timeout

// State access
sessionState           // Global session object with all metrics
```

### Progress Tracking
```javascript
// Polling (HTTP)
fetch('/interviews/practice/session/{id}/progress/')
    .then(r => r.json())
    .then(data => {
        // data.progress.percentage
        // data.current_score
        // data.status
    });

// WebSocket (recommended)
const socket = new WebSocket(`wss://${host}/ws/session/{id}/`);
socket.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    // Handle message.type === 'progress_update'
};
```

### Dashboard
```javascript
// Initialize charts
initProgressChart()    // Load Chart.js

// View session details
viewSession(sessionId) // Open session modal
```

---

## API Request/Response Examples

### Setup Session
**Request**:
```bash
POST /interviews/practice/setup/save/
Content-Type: application/json
X-CSRFToken: <token>

{
    "focus_areas": ["leadership", "technical"],
    "number_of_questions": 5,
    "difficulty": "medium",
    "time_limit_per_question": 2,
    "enable_video": true
}
```

**Response**:
```json
{
    "success": true,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Session setup saved successfully"
}
```

### Get Progress
**Request**:
```bash
GET /interviews/practice/session/{id}/progress/
Authorization: Bearer <token>
```

**Response**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "in_progress",
    "progress": {
        "completed": 2,
        "total": 5,
        "percentage": 40
    },
    "current_score": 75.5,
    "generation_state": "completed"
}
```

### Session Control
**Request**:
```bash
POST /interviews/practice/session/{id}/controls/
Content-Type: application/json
X-CSRFToken: <token>

{
    "action": "skip",
    "question_id": 123
}
```

**Response**:
```json
{
    "success": true,
    "message": "Question skipped",
    "response_id": 456
}
```

---

## Celery Task Reference

### Using Progress Tasks
```python
from apps.interviews.progress_tasks import (
    track_question_generation_progress,
    track_warmup_completion,
    track_response_analysis
)

# Track progress
track_question_generation_progress.delay(
    session_id=session.id,
    progress_data={
        'stage': 'generating',
        'message': 'Generating 5 questions...',
        'progress': 50
    }
)

# Track warmup
track_warmup_completion.delay(
    session_id=session.id,
    warmup_data={
        'camera_test_passed': True,
        'microphone_test_passed': True,
        'test_question_completed': True,
        'camera_quality': 'high',
        'audio_level': -3
    }
)

# Track analysis
track_response_analysis.delay(
    session_id=session.id,
    response_id=response.id,
    analysis_result={
        'overall_score': 82.5,
        'feedback': ['Good content', 'Improve posture']
    }
)
```

---

## Template Integration Examples

### Add to Navigation
```html
<!-- In base navigation template -->
<li>
    <a href="{% url 'interviews:setup' %}">
        <i class="fas fa-rocket"></i>
        Practice Interview
    </a>
</li>
<li>
    <a href="{% url 'interviews:practice_history' %}">
        <i class="fas fa-chart-line"></i>
        Practice History
    </a>
</li>
```

### Dashboard Widget
```html
<!-- Add to dashboard -->
<div class="bg-white p-6 rounded-lg shadow">
    <h3>Practice Statistics</h3>
    <div class="grid grid-cols-4 gap-4 mt-4">
        <div>
            <p class="text-gray-600">Total Sessions</p>
            <p class="text-2xl font-bold">{{ stats.total_sessions }}</p>
        </div>
        <div>
            <p class="text-gray-600">Average Score</p>
            <p class="text-2xl font-bold">{{ stats.average_score }}%</p>
        </div>
        <div>
            <p class="text-gray-600">Current Streak</p>
            <p class="text-2xl font-bold">{{ stats.current_streak }}</p>
        </div>
        <div>
            <p class="text-gray-600">Next Goal</p>
            <p class="text-2xl font-bold">{{ stats.next_goal }}%</p>
        </div>
    </div>
    <a href="{% url 'interviews:practice_history' %}" 
       class="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded">
        View Full History
    </a>
</div>
```

---

## Configuration

### Required Settings
```python
# settings.py

# WebSocket configuration (optional but recommended)
ASGI_APPLICATION = 'hiresight.asgi_channels.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Cache configuration (for progress tracking)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Optional Enhancements
```python
# Rate limiting (django-ratelimit)
RATELIMIT_ENABLE = True

# CORS configuration (if needed)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://yourdomain.com',
]

# Celery configuration (if using tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

---

## Browser Support

**Minimum Requirements**:
- Chrome 75+
- Firefox 68+
- Safari 12+
- Edge 79+

**Features Requiring Modern Browser**:
- MediaDevices API (camera/microphone) - Chrome 53+, Firefox 36+, Safari 11+
- Web Audio API - Chrome 14+, Firefox 25+, Safari 6+
- WebSocket - All modern browsers
- Fetch API - Chrome 42+, Firefox 39+, Safari 10+

---

## Performance Optimization

### Frontend Caching
```javascript
// Cache progress data in memory
const progressCache = new Map();

function getProgressCached(sessionId) {
    if (progressCache.has(sessionId)) {
        return progressCache.get(sessionId);
    }
    // Fetch and cache...
}
```

### Backend Caching
```python
# Cache session stats for 5 minutes
from django.views.decorators.cache import cache_page

@cache_page(300)  # 5 minutes
def practice_history_dashboard(request):
    # View code...
```

### Image Optimization
```html
<!-- Use srcset for responsive images -->
<img src="chart-small.png"
     srcset="chart-small.png 320w,
             chart-medium.png 768w,
             chart-large.png 1200w"
     sizes="(max-width: 320px) 100vw,
            (max-width: 768px) 90vw,
            1200px">
```

---

## Troubleshooting

### Camera/Microphone Not Working
```javascript
// Check browser permissions
if (!navigator.mediaDevices) {
    console.error('MediaDevices API not supported');
}

// Check permissions status
navigator.permissions.query({name: 'camera'})
    .then(result => console.log(result.state));
```

### WebSocket Connection Failed
```javascript
// Fallback to polling
const usePolling = !('WebSocket' in window);

if (usePolling) {
    // Use polling endpoint
    setInterval(() => {
        fetch(`/interviews/practice/session/${id}/progress/`)
            .then(r => r.json())
            .then(updateUI);
    }, 2000);
}
```

### Database Migration Issues
```bash
# Check migration status
python manage.py showmigrations interviews

# Rollback if needed
python manage.py migrate interviews 0004

# Reapply
python manage.py migrate interviews
```

---

## Security Checklist

- ✅ CSRF token required on all POST requests
- ✅ Authentication required on all views
- ✅ HTTPS/WSS enforced in production
- ✅ User can only access own sessions
- ✅ Input validation on client and server
- ✅ No sensitive data in logs
- ✅ Rate limiting enabled
- ✅ CORS properly configured
- ✅ SQL injection prevented via ORM
- ✅ XSS prevented via template escaping

---

## Testing Checklist

- ✅ Test setup modal form validation
- ✅ Test warmup camera/microphone access
- ✅ Test timer functionality
- ✅ Test pause/resume mechanics
- ✅ Test skip/rerecord actions
- ✅ Test dashboard statistics
- ✅ Test progress polling
- ✅ Test WebSocket updates
- ✅ Test error scenarios
- ✅ Test mobile responsiveness

---

## Deployment Checklist

- ✅ Run migrations: `python manage.py migrate interviews`
- ✅ Collect static files: `python manage.py collectstatic --noinput`
- ✅ Configure Redis for cache/channel layer
- ✅ Configure Celery worker
- ✅ Enable HTTPS/WSS
- ✅ Configure CORS if needed
- ✅ Set up monitoring/logging
- ✅ Configure email for notifications
- ✅ Set DEBUG = False
- ✅ Configure allowed hosts

---

## Support Resources

- **Documentation**: See `PRACTICE_UX_IMPROVEMENTS.md`
- **Source Code**: View `apps/interviews/views_ux.py`
- **Tasks**: View `apps/interviews/progress_tasks.py`
- **Models**: View `apps/interviews/models.py`
- **Templates**: View `templates/interviews/practice/`

---

**Last Updated**: January 24, 2026
**Status**: Ready for Production
