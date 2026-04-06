# Interview Practice UX Improvements

## Overview

This implementation adds comprehensive UX enhancements to the interview practice system, including:

1. **Session Setup Modal** - Configure practice sessions before starting
2. **Warmup/Test Flow** - Camera, microphone, and practice question tests
3. **Progress Tracking** - Real-time progress indicators during question generation
4. **Session Controls** - Pause, skip, re-record, and exit functionality
5. **Practice History Dashboard** - Track progress with charts, badges, and streaks

## Features

### 1. Session Setup Modal

**File**: `templates/interviews/practice/session_setup_modal.html`

Appears before starting a practice session, allowing users to customize:

- **Focus Areas** (multi-select): Leadership, Technical, Communication, Problem Solving, Collaboration, Adaptability
- **Number of Questions**: 5, 10, or 15
- **Difficulty Level**: Easy, Medium, Hard, or Mixed
- **Time Limit per Question**: 1, 2, or 3 minutes
- **Video Analysis**: Toggle on/off for AI-powered video analysis

**Usage**:
```html
{% include 'interviews/practice/session_setup_modal.html' %}
```

**Data Flow**:
1. User selects options and clicks "Continue"
2. `validateSetupForm()` checks that at least one focus area is selected
3. `saveSetupData()` stores configuration in sessionStorage and posts to server
4. Server creates `InterviewPracticeSession` with settings

### 2. Warmup/Test Flow

**File**: `templates/interviews/practice/warmup_flow.html`

Four-step process to prepare for practice:

#### Step 1: Camera Test
- Requests camera access
- Shows live video preview
- Confirms camera is working

#### Step 2: Microphone Test
- Requests microphone access
- Displays real-time audio level visualization
- Confirms microphone captures clear audio

#### Step 3: Practice Question (Optional)
- Presents a non-scored practice question
- Allows users to familiarize with recording interface
- Can be skipped if user feels ready

#### Step 4: Final Confirmation
- Reviews all session settings
- Displays configuration summary
- Allows editing setup or starting practice

**JavaScript Features**:
- `startCameraTest()` - Initialize camera stream
- `startMicTest()` - Capture audio and visualize levels
- `visualizeMicLevel()` - Real-time audio level bars
- `nextStep()`/`prevStep()` - Navigation between steps
- `startPractice()` - Begin actual practice session

### 3. Progress Tracking System

**Files**: 
- `apps/interviews/progress_tasks.py` - Celery tasks for tracking
- `apps/interviews/views_ux.py` - `SessionProgressView`

**Real-time Progress Updates**:

```python
# Example: Broadcasting question generation progress
track_question_generation_progress.delay(
    session_id=session.id,
    progress_data={
        'stage': 'analyzing',
        'message': 'Analyzing job requirements...',
        'progress': 20,
        'timestamp': now.isoformat()
    }
)
```

**Stages**:
1. **Analyzing** - Analyzing job requirements
2. **Matching** - Matching questions to skills
3. **Generating** - Generating personalized questions
4. **Validating** - Validating questions
5. **Completed** - Ready!

**Client-Side Integration**:

```javascript
// Polling for progress (fallback method)
fetch(`/interviews/practice/session/${sessionId}/progress/`)
    .then(r => r.json())
    .then(data => {
        updateProgressBar(data.progress.percentage);
    });

// WebSocket connection (preferred method)
const socket = new WebSocket(`wss://${host}/ws/session/${sessionId}/`);
socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'generation_progress') {
        updateProgressUI(data);
    }
};
```

### 4. Session Controls

**File**: `templates/interviews/practice/session_controls.html`

Control panel appears during practice with buttons for:

#### Pause/Resume
- Stops timer and video recording
- Preserves current state
- Resumes from where left off

#### Skip Question
- Confirmation modal required
- Question marked as skipped
- Moves to next question
- Counts skipped questions

#### Re-record
- Deletes previous response
- Allows one re-recording per question
- Timer resets
- Video recording resets

#### Exit Session
- Confirmation modal with progress summary
- Saves all responses and progress
- Redirects to dashboard
- Can be resumed later

**State Management**:
```javascript
let sessionState = {
    currentQuestion: 1,
    totalQuestions: 5,
    timePerQuestion: 120, // seconds
    timeRemaining: 120,
    questionsAnswered: 0,
    questionsSkipped: 0,
    rerecordsUsed: 0,
    maxRerecords: 1
};
```

### 5. Practice History Dashboard

**File**: `templates/interviews/practice/practice_history_dashboard.html`

Comprehensive dashboard showing:

#### Statistics Cards
- **Total Sessions**: Number of practice sessions completed
- **Average Score**: Overall average with trend indicator
- **Current Streak**: Consecutive days with practice
- **Next Goal**: Target score with progress bar

#### Progress Chart
- Line chart showing score progression over time
- Best, lowest, and median scores displayed
- Smooth animations and responsive design

#### Category Performance
- Breakdown of scores by question category
- Progress bars for each category
- Identifies weak and strong areas

#### Badges & Achievements
Earned upon meeting criteria:
- **First Step**: Complete first session
- **5 Sessions**: Complete 5 sessions
- **10 Sessions**: Complete 10 sessions
- **Perfect Score**: Score 100% on a session
- **Consistent**: Maintain 7-day streak
- **Expert**: Maintain 90+ average
- **Improving**: Improve by 10%+ over time
- **Versatile**: Practice all question types

#### Recent Sessions List
- Session type and date
- Score with visual gauge
- Number of questions
- Duration
- Focus areas
- View Report button

#### Personalized Tips
- AI-generated recommendations based on performance
- Suggestions to improve weak areas
- Encouragement for progress

### 6. Model Fields

**InterviewPracticeSession** additions:
```python
focus_areas = JSONField()  # ['leadership', 'technical', ...]
time_limit_per_question = PositiveIntegerField(choices=[(1,2,3)])
video_analysis_enabled = BooleanField(default=True)
warmup_completed = BooleanField(default=False)
camera_test_passed = BooleanField(default=False)
microphone_test_passed = BooleanField(default=False)
test_question_completed = BooleanField(default=False)
```

**Migration**: `0005_add_ux_improvements_fields.py`

## API Endpoints

### Setup & Warmup
```
POST /interviews/practice/setup/save/
- Save session configuration
- Response: { success: true, session_id: uuid }

GET /interviews/practice/warmup/<session_id>/
- Display warmup flow

POST /interviews/practice/warmup/<session_id>/complete/
- Mark warmup completed
```

### Progress Tracking
```
GET /interviews/practice/session/<session_id>/progress/
- Get current session progress (polling endpoint)
- Response: {
    progress: { completed, total, percentage },
    current_score: float,
    status: string,
    generation_state: string
  }
```

### Session Controls
```
POST /interviews/practice/session/<session_id>/controls/
- Handle control actions
- Body: { action: 'pause|resume|skip|rerecord|exit', ... }
```

### Dashboard
```
GET /interviews/practice/history/
- Display practice history dashboard
- Includes stats, sessions, charts
```

## JavaScript Integration

### VideoAnalyzer Integration
```javascript
// In session controls
if (window.videoAnalyzer) {
    window.videoAnalyzer.pause();  // Pause video recording
    window.videoAnalyzer.resume();  // Resume
    window.videoAnalyzer.reset();   // Reset for re-record
}
```

### Timer Management
```javascript
function startTimer() {
    timerInterval = setInterval(() => {
        sessionState.timeRemaining--;
        updateTimerDisplay();
        if (sessionState.timeRemaining <= 0) onTimeExpired();
    }, 1000);
}
```

### WebSocket Connection
```javascript
const socket = new WebSocket(`wss://${host}/ws/session/${sessionId}/`);

socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'progress_update') {
        updateProgressBar(message.data.progress);
    } else if (message.type === 'session_update') {
        handleSessionUpdate(message.data);
    }
};
```

## Database Schema

### InterviewPracticeSession
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| candidate | FK | Reference to User |
| focus_areas | JSON | Selected focus areas |
| time_limit_per_question | Integer | Minutes per question |
| video_analysis_enabled | Boolean | Video analysis flag |
| warmup_completed | Boolean | Warmup completion flag |
| camera_test_passed | Boolean | Camera test result |
| microphone_test_passed | Boolean | Microphone test result |
| test_question_completed | Boolean | Test question completion |
| status | String | Session status |
| question_generation_state | String | Generation state |
| report_generation_state | String | Report state |

## Celery Tasks

### Progress Tracking Tasks
```python
# Track progress and broadcast to clients
track_question_generation_progress(session_id, progress_data)

# Track warmup completion
track_warmup_completion(session_id, warmup_data)

# Track response analysis
track_response_analysis(session_id, response_id, analysis_result)

# Track session controls
track_session_pause(session_id, pause_reason)
track_session_resume(session_id)
track_question_skip(session_id, question_id)
track_question_rerecord(session_id, question_id)
```

## Usage Flow

### Typical Session Flow
```
1. User clicks "Start Practice"
   ↓
2. Setup Modal appears
   ↓
3. User configures session and clicks "Continue"
   ↓
4. Setup saved to server, session created
   ↓
5. Warmup Flow starts (camera → microphone → test question → confirm)
   ↓
6. Progress tracking begins (real-time updates)
   ↓
7. Practice questions displayed with session controls
   ↓
8. User can: pause, skip, re-record, or exit
   ↓
9. After all questions: Generate report
   ↓
10. View report or dashboard
```

## Browser Requirements

- **Camera/Microphone**: MediaDevices API
- **WebSocket**: Optional (falls back to polling)
- **Chart.js**: For dashboard visualizations
- **Modern CSS**: Tailwind CSS with gradients and animations

## Error Handling

### Camera/Microphone Errors
```javascript
try {
    cameraStream = await navigator.mediaDevices.getUserMedia({video: true});
} catch (error) {
    showError('Camera access denied: ' + error.message);
    document.getElementById('cameraStatus').classList.remove('hidden');
}
```

### Network Errors
- Polling fallback if WebSocket fails
- In-memory session state persisted in sessionStorage
- Graceful degradation for offline scenarios

## Performance Optimization

- **Lazy Loading**: Dashboard charts load on demand
- **Caching**: Progress data cached for 1 hour
- **Compression**: JSON responses gzipped
- **Throttling**: Progress updates throttled to prevent UI thrashing
- **Debouncing**: Session controls debounced to prevent double-clicks

## Security

- **CSRF Protection**: All POST requests require CSRF token
- **Authentication**: All endpoints require login
- **Authorization**: Users can only access their own sessions
- **Input Validation**: All form inputs validated server-side
- **XSS Prevention**: Template auto-escaping enabled

## Future Enhancements

1. **Analytics**: Track improvement metrics over time
2. **Peer Comparison**: Anonymous comparison with other candidates
3. **AI Recommendations**: Personalized practice recommendations
4. **Mobile Optimization**: Responsive design for tablets/phones
5. **Voice Analysis**: Advanced speaking pattern analysis
6. **Stress Detection**: Monitor stress levels during practice
7. **Accent Analysis**: Provide feedback on pronunciation
8. **Collaborative Practice**: Practice with a friend in real-time

## Troubleshooting

### Camera Not Showing
- Check browser permissions
- Ensure HTTPS is enabled
- Try different browser
- Check firewall/security software

### Microphone Recording Issues
- Check audio input device in browser settings
- Ensure microphone is not muted
- Test with browser's microphone test
- Check volume levels

### WebSocket Connection Failed
- Falls back to polling automatically
- Check WebSocket proxy configuration
- Verify CORS headers
- Check firewall/proxy settings

## Testing

```bash
# Run tests for views
python manage.py test apps.interviews.tests.test_views_ux

# Test progress tracking tasks
python manage.py test apps.interviews.tests.test_progress_tasks

# Test models
python manage.py test apps.interviews.tests.test_models
```
