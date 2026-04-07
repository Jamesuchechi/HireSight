# HireSight 2.0 Development Roadmap (Next.js + Supabase)

**Version**: 3.0 (Migration)  
**Last Updated**: April 6, 2026  
**Status**: Initial Scaffolding

---

## 🏗️ Phase 1: Foundation & Infrastructure
- [ ] Initialize Next.js 15 Project (App Router, TS, Tailwind)
- [ ] Setup Supabase Project & Auth configuration
- [ ] Define Database Schema in Supabase (SQL Migrations)
- [ ] Port Shared Layout & Navigation components
- [ ] Implement Landing Page (Framer Motion animations)

## 🔐 Phase 2: Authentication & Profiles
- [ ] Implement Sign Up / Sign In with Supabase Auth
- [ ] Role-based Access Control (RLS Policies)
- [ ] Personal Profile Builder (Jobs Seeker)
- [ ] Company Profile Builder (Recruiter)
- [ ] Profile Settings & Preferences

## 🤖 Phase 3: AI Core (Mistral + Groq + OpenRouter)
- [ ] Implement Resume Parser (Groq + Mistral)
- [ ] Setup Supabase Storage for Resumes
- [ ] Semantic Match Engine (Supabase Vector)
- [ ] Automated Job Matching & Scoring

## 💼 Phase 4: Job Management & Applications
- [ ] Job Posting & Lifecycle Management
- [ ] Job Searching & Filtering (Elastic/Vector)
- [ ] Application Pipeline (Kanban Board)
- [ ] In-app Messaging & Realtime Notifications

---

## 📱 Legacy Tracker (Django)
- Legacy files moved to `legacy-django/` for reference.
- No users to migrate (Fresh Start).

---

## 💼 **jobs** App

### Job Posting Management (Company Only)
- [ ] Create job form (title, description, requirements, salary)
- [ ] Rich text editor for job description
- [ ] Skills tagging (required vs nice-to-have)
- [ ] Screening questions (custom questions for applicants)
- [ ] Job status management (draft/active/closed)
- [ ] Edit/update job postings
- [ ] Duplicate existing job (template feature)
- [ ] Delete job (with cascade handling)
- [ ] Job expiration date (auto-close after date)
- [ ] Job preview before publishing

### Job Discovery (Personal Only)
- [ ] Browse all active jobs (paginated list)
- [ ] Search by keyword (title, description, company)
- [ ] Advanced filters:
  - [ ] Location (with radius search)
  - [ ] Remote type (remote/hybrid/onsite)
  - [ ] Salary range (min-max slider)
  - [ ] Experience level (entry/mid/senior)
  - [ ] Job type (full-time/part-time/contract)
  - [ ] Skills (multi-select with AND/OR logic)
  - [ ] Posted date (last 24h, week, month)
- [ ] Sort options (relevance, date, salary, match score)
- [ ] Save search criteria for quick access
- [ ] Job recommendation algorithm (AI-powered matches)
- [ ] "Jobs you may like" section on dashboard
- [ ] Job detail page with:
  - [ ] Full description & requirements
  - [ ] Company info & logo
  - [ ] Similar jobs from same company
  - [ ] Apply button with resume selection
  - [ ] Save job button (bookmark)
  - [ ] Share job (copy link, social media)

### Saved Jobs (Personal Only)
- [ ] Save/bookmark jobs for later
- [ ] View all saved jobs (dedicated page)
- [ ] Remove from saved jobs
- [ ] Saved jobs counter on dashboard
- [ ] Email reminders for saved jobs not applied to

### Job Analytics (Company Only)
- [ ] Job views count (unique vs total)
- [ ] Application rate (applications per view)
- [ ] Time-to-first-application metric
- [ ] Average match score per job
- [ ] Source tracking (where applicants found job)
- [ ] Export job analytics to CSV

---

## 📝 **applications** App

### Application Submission (Personal Only)
- [ ] One-click apply with primary resume
- [ ] Resume selection dropdown (choose version)
- [ ] Optional cover letter (rich text editor)
- [ ] Answer screening questions (if job has them)
- [ ] Prevent duplicate applications (validation)
- [ ] Application confirmation email
- [ ] Track application status timeline

### Application Tracking (Personal Only)
- [ ] View all applications (list view)
- [ ] Filter by status (pending, screening, interview, offer, hired, rejected)
- [ ] Filter by date range
- [ ] Search by company or job title
- [ ] Application detail page showing:
  - [ ] Job details
  - [ ] Resume used
  - [ ] Cover letter
  - [ ] Status history timeline
  - [ ] Match score (if screened)
  - [ ] Company feedback (if provided)
- [ ] Withdraw application button
- [ ] Application success rate widget (hired/total)

### Application Management (Company Only)
- [ ] View all applicants per job (table view)
- [ ] Filter by status, match score, date applied
- [ ] Sort by match score, date, name
- [ ] Bulk actions:
  - [ ] Move to screening
  - [ ] Move to interview
  - [ ] Reject multiple candidates
  - [ ] Send bulk emails
- [ ] Individual application view with:
  - [ ] Candidate profile preview
  - [ ] Resume download/preview
  - [ ] Cover letter
  - [ ] Match score breakdown
  - [ ] Screening question answers
  - [ ] Internal notes section
  - [ ] Status change buttons
  - [ ] Rating system (1-5 stars)

### Application Pipeline (Company Only)
- [ ] Visual Kanban board with columns:
  - [ ] New (unreviewed)
  - [ ] Screening (under review)
  - [ ] Interview (scheduled or pending)
  - [ ] Offer (offer sent)
  - [ ] Hired (accepted)
  - [ ] Rejected (with reason)
- [ ] Drag-and-drop between stages
- [ ] Card preview (name, match score, applied date)
- [ ] Filter pipeline by job
- [ ] Pipeline analytics (conversion rates per stage)
- [ ] Time in stage tracking

### Application Status Updates
- [ ] Update status with reason/notes
- [ ] Send automated emails on status change
- [ ] Allow candidates to respond to status updates
- [ ] Status change history log
- [ ] Rejection with feedback option

---

## 🤖 **screening** App

### AI Resume Screening System

#### Bulk Resume Upload
- [ ] Drag-and-drop upload interface (up to 50 resumes)
- [ ] File type validation (PDF/DOCX only)
- [ ] File size validation (5MB per file)
- [ ] Progress bar for upload
- [ ] Preview uploaded files before processing
- [ ] Remove files from queue before processing

#### Screening Session Management
- [ ] Create screening session form
- [ ] Link session to specific job (optional)
- [ ] Define screening criteria:
  - [ ] Required skills (multi-select)
  - [ ] Nice-to-have skills
  - [ ] Min/max years of experience
  - [ ] Education requirements
  - [ ] Location preferences
  - [ ] Custom keywords
  - [ ] Scoring weights (skills, experience, education, keywords)
- [ ] Session status tracking (pending/processing/completed/failed)
- [ ] View all screening sessions (list view)
- [ ] Session detail page with progress indicator

#### AI Matching Engine
- [ ] Implement semantic similarity with Sentence Transformers
- [ ] Calculate match score (0-100) with weighted algorithm:
  - [ ] Skills match (40% weight)
  - [ ] Experience match (30% weight)
  - [ ] Education match (20% weight)
  - [ ] Keyword match (10% weight)
- [ ] Extract skills from resume using spaCy NER
- [ ] Calculate skills match percentage
- [ ] Identify skill gaps (required skills missing)
- [ ] Generate detailed match explanation (JSONB)
- [ ] Handle multiple languages (English priority)

#### Background Processing (Celery)
- [ ] Async task for bulk resume processing
- [ ] Process resumes sequentially with progress updates
- [ ] Real-time progress via WebSocket (or polling)
- [ ] Error handling for failed parsing
- [ ] Retry mechanism (max 3 retries)
- [ ] Email notification when processing complete
- [ ] Log all processing steps for debugging

#### Screening Results
- [ ] Results dashboard with:
  - [ ] Total resumes processed
  - [ ] Average match score
  - [ ] Processing time
  - [ ] Failed resumes count
- [ ] Ranked candidates list (sorted by match score)
- [ ] Pagination (20 candidates per page)
- [ ] Filter by match score range (e.g., 80-100)
- [ ] Filter by status (completed/failed)
- [ ] Search by candidate name or email
- [ ] Detailed candidate view showing:
  - [ ] Keyword matches highlighted
  - [ ] Full resume preview
  - [ ] Shortlist button
  - [ ] Add internal notes
  - [ ] Manual rating (1-5 stars)

#### Export & Integration
- [ ] Export results to Excel (all data)
- [ ] Export to PDF report (summary + top candidates)
- [ ] Export to CSV for data analysis
- [ ] Customizable export columns
- [ ] Push top candidates to application pipeline
- [ ] Sync screening results with ATS (future)

#### Screening Analytics
- [ ] Distribution chart of match scores
- [ ] Most common skill gaps
- [ ] Top matched skills
- [ ] Experience distribution histogram
- [ ] Processing performance metrics (time per resume)
- [ ] Screening success rate (hired vs total screened)

---

## 📊 **dashboard** App

### Personal Dashboard (Job Seekers)
- [ ] Welcome message with personalized greeting
- [ ] Profile completion progress (circular progress bar)
- [ ] Quick stats cards:
  - [ ] Active applications count
  - [ ] Saved jobs count
  - [ ] Profile views (last 30 days)
  - [ ] Recommended jobs count
- [ ] Recommended jobs section (top 5 AI matches)
- [ ] Recent applications timeline (last 10)
- [ ] Saved jobs widget (quick access to bookmarks)
- [ ] Upcoming interviews calendar widget
- [ ] Recent notifications feed
- [ ] Quick actions:
  - [ ] Upload resume
  - [ ] Edit profile
  - [ ] Browse jobs
  - [ ] Take skill assessment

### Company Dashboard (Recruiters)
- [ ] Welcome message with company name
- [ ] Quick stats cards:
  - [ ] Active jobs count
  - [ ] Total applicants (pending review)
  - [ ] Interviews scheduled (this week)
  - [ ] Offers pending response
  - [ ] Hired this month
- [ ] Top candidates widget (highest match scores across jobs)
- [ ] Recent activity feed (new applications, status changes)
- [ ] Active jobs summary (applications per job)
- [ ] Hiring funnel visualization (conversion rates)
- [ ] Recent screening sessions
- [ ] Company followers count
- [ ] Quick actions:
  - [ ] Post new job
  - [ ] Screen resumes
  - [ ] View applicants
  - [ ] Schedule interview

### Shared Dashboard Features
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Dark mode toggle
- [ ] Customizable widget layout (drag-and-drop)
- [ ] Export dashboard data to PDF
- [ ] Dashboard refresh button

### Immediate implementation plan
- [ ] Add a persistent dark/light mode toggle that swaps theme classes and optionally syncs to the server.
- [ ] Enable drag-and-drop rearrangement for dashboard cards via a lightweight JS helper, persisting layout order per user in localStorage or a profile endpoint.
- [ ] Wire an “Export to PDF” control that triggers server-side rendering (reusing the existing PDF export utilities) and returns a downloadable snapshot.
- [ ] Hook a “Refresh dashboard” button to either reload the current view or hit a lightweight JSON endpoint so widgets can reflect the latest data.

---

## 💬 messaging App

### Core messaging features (✅ implementation in `apps.messaging`)
- [x] Inbox view with search/filter, pagination, unread counts, and archive controls (`apps/messaging/views.py`, `templates/messaging/inbox.html`)
- [x] Compose modal plus full-page composer with draft autosave, template selector, and quick recipient suggestions (`forms.py`, `templates/messaging/compose_modal.html`)
- [x] Conversation detail view with chat bubbles, attachments/lightbox, mark-as-read/archive/delete, block/report actions, and pagination (`views.py`, `templates/messaging/conversation_detail.html`, `_message_bubble.html`)
- [x] Message attachments (images/PDFs/Word) with previews, metadata, and lightbox download links (`models.py`, `_message_bubble.html`, `contexts`, attachments handling in view)
- [x] Message templates for companies, AJAX loader, and usage tracking (`models.py`, `forms.py`, `views.py`, `_template_loader_script.html`)
- [x] Unread badge + realtime notifications powered by `unread_messages_count` context processor, `UnreadConsumer`, and navbar JS hooking into `/ws/messaging/unread/` (`context_processors.py`, `consumers.py`, `templates/base.html`)
- [x] WebSocket-driven conversation updates, typing indicators, and read-receipt helpers (signals + consumers handling `conversation.message` events) backed by Django Channels routing (`consumers.py`, `signals.py`, `websocket_routing.py`)
- [x] Block/report flows with confirmation modals, backend endpoints, admin tooling, and messaging (`views.py`, `templates/messaging/conversation_detail.html`, `admin.py`)
- [x] Message pagination and load-more API/fallback (`load_more_messages`, `poll_conversation_messages`, `templates/messaging/conversation_detail.html`)

### Outstanding / partially implemented work
- [ ] Add online/offline presence indicators per participant (via Channels presence tracking) so the UI can flag who is currently available in a conversation thread.
- [ ] Replace textual read-status labels with double-check visual treatments (and propagate per-message read states over WebSockets for both sender and recipient).
- [ ] Implement browser/mobile push notifications (service worker + Celery task) tied to the new-message signal so messages can arrive even when the tab is backgrounded.
- [ ] Expand automated coverage for `ConversationConsumer`/`UnreadConsumer` and retire the polling endpoint once real-time paths prove stable.
- [ ] Document the messaging workflow (real-time hooks, template usage, attachment requirements) in the project README or a dedicated messaging guide.

---

## 🔔 **notifications** App

### Notification System
- [ ] Notification center (bell icon in navbar)
- [ ] Notification list with pagination
- [ ] Mark as read/unread toggle
- [ ] Mark all as read button
- [ ] Delete individual notification
- [ ] Delete all notifications
- [ ] Unread count badge
- [ ] Notification types:
  - [ ] New application received (company)
  - [ ] Application status changed (personal)
  - [ ] New message received (both)
  - [ ] Someone followed you/your company (both)
  - [ ] New job from followed company (personal)
  - [ ] Interview scheduled/rescheduled (both)
  - [ ] Resume screening completed (company)
  - [ ] Job about to expire (company)
  - [ ] Profile viewed (personal)

### Email Notifications (Celery)
- [ ] Async task for sending emails
- [ ] Email templates for each notification type
- [ ] User preferences for email frequency:
  - [ ] Instant (real-time)
  - [ ] Daily digest
  - [ ] Weekly digest
  - [ ] Off (in-app only)
- [ ] Unsubscribe link in all emails
- [ ] Email open/click tracking (optional)
- [ ] Retry failed email sends (max 3 attempts)

### Push Notifications (Future)
- [ ] Browser push notifications (service worker)
- [ ] Mobile push notifications (FCM)
- [ ] Push notification preferences

---

## 👥 **following** App

### Following System
- [ ] Follow button on company profiles (personal only)
- [ ] Follow button on user profiles (personal only)
- [ ] Unfollow button
- [ ] Followers list view (who follows you)
- [ ] Following list view (who you follow)
- [ ] Followers count display on profiles
- [ ] Following count display on profiles
- [ ] Notification when someone follows you
- [ ] Notification when followed company posts new job
- [ ] Mutual followers indicator
- [ ] Suggested companies to follow (based on job searches)
- [ ] Suggested users to follow (based on skills/industry)

### Network Features (Personal Only)
- [ ] View follower's public profiles
- [ ] See mutual connections
- [ ] Activity feed from followed users (optional)
- [ ] Follow recommendations algorithm

---

## 📈 **analytics** App

### Company Analytics
- [ ] Hiring overview dashboard:
  - [ ] Total jobs posted
  - [ ] Total applications received
  - [ ] Total hires
  - [ ] Average time-to-hire
  - [ ] Average cost-per-hire (if budget tracked)
- [ ] Job-specific analytics:
  - [ ] Applications per job
  - [ ] Views per job
  - [ ] Application rate (apps/views)
  - [ ] Match score distribution
  - [ ] Source of applicants (organic search, referral, etc.)
- [ ] Application funnel visualization:
  - [ ] Applied → Screening → Interview → Offer → Hired
  - [ ] Conversion rates between stages
  - [ ] Drop-off analysis
- [ ] Screening analytics:
  - [ ] Total resumes screened
  - [ ] Average match score
  - [ ] Top skills found
  - [ ] Skill gap analysis
- [ ] Time-based trends:
  - [ ] Applications over time (line chart)
  - [ ] Hires per month (bar chart)
  - [ ] Average time-to-hire trend
- [ ] Export options:
  - [ ] Export to CSV
  - [ ] Export to PDF report
  - [ ] Scheduled email reports (weekly/monthly)

### Personal Analytics
- [ ] Application overview:
  - [ ] Total applications submitted
  - [ ] Applications by status
  - [ ] Success rate (offers/applications)
  - [ ] Average response time from companies
- [ ] Job search activity:
  - [ ] Jobs viewed
  - [ ] Jobs saved
  - [ ] Searches performed
- [ ] Profile analytics:
  - [ ] Profile views count
  - [ ] Who viewed your profile (list)
  - [ ] Profile completion score
- [ ] Skill assessment results:
  - [ ] Tests taken
  - [ ] Average scores
  - [ ] Skill badges earned

### Advanced Analytics
- [ ] Predictive analytics (likelihood to hire)
- [ ] Benchmarking (compare to industry averages)
- [ ] Custom report builder
- [ ] Data export API

---

## 🎯 Additional Features (Cross-App)

## Interviews App

### Interview Scheduling
- [ ] Schedule interview form (company)
- [ ] Calendar date/time picker
- [ ] Send interview invitation email
- [ ] Google Calendar integration (iCal export)
- [ ] Interview reminders:
  - [ ] 24 hours before
  - [ ] 1 hour before
- [ ] Reschedule interview functionality
- [ ] Cancel interview with reason
- [ ] View upcoming interviews (both roles)
- [ ] Mark interview as completed
- [ ] Add interview notes (company only)
- [ ] Video interview link integration (Zoom, Meet)

### Skill Assessments (Personal Only)
- [ ] Browse available skill tests (programming, design, etc.)
- [ ] Take timed assessment (multiple choice)
- [ ] Submit assessment answers
- [ ] Score calculation (instant results)
- [ ] Display passed assessments on profile
- [ ] Assessment badges
- [ ] Generate PDF certificate
- [ ] Share assessment results with companies
- [ ] Ensure each dynamic test can pull `question_count` items by keeping the `QuestionPool` seeded per skill/  difficulty (review `apps/assessments/models.py::SkillTest.generate_questions`)

### Skill Assessment Enhancements (In Review)
- [ ] Add a “Generate questions” button on the browse/detail views that POSTs to a protected endpoint (admin/staff-only) and triggers `QuestionGenerator.bulk_generate_for_test(test)` (AJAX-friendly UI with progress/feedback)
- [ ] Cache the current pool size per skill+difficulty (e.g., `skill:React:BEGINNER:pool_size`) so the browse page can show “12/8 questions available” without hitting the DB each render; expire every 5–10 minutes or on pool update
- [ ] Implement rate limiting/cooldown for generation (e.g., one request per test every 5 minutes, tracked per user/IP) and surface cooldown status on the UI
- [ ] Queue AI generation via Celery to avoid blocking the request and update the cache + `QuestionPool` with new entries (keep `is_verified=False` for review); optionally record history entry for auditing
- [ ] Build an assessment history page showing users’ attempts, question-by-question results, pass/fail status, badges earned, and per-question stats (fail/pass) so they can review performance
- [ ] Create a lightweight log/history model for generation attempts (timestamp, initiator, test, result count) and expose it on the history page for admins
- [ ] After generation, refresh the cached counts and notify admins (email/slack) that new questions are ready for review; include a “mark as verified” toggle if desired

### Job Recommendations (Personal Only)
- [ ] AI-powered job matching algorithm:
  - [ ] Based on profile skills
  - [ ] Based on experience level
  - [ ] Based on job preferences
  - [ ] Based on past applications
- [ ] Display recommended jobs on dashboard
- [ ] "Why recommended?" explanation modal
- [ ] Thumbs up/down feedback buttons
- [ ] Improve recommendations based on feedback
- [ ] Weekly email digest of recommended jobs

### Company Branding Pages
- [ ] Public company profile page (accessible without login)
- [ ] Company overview section
- [ ] Team member showcase (photo grid)
- [ ] Office photos gallery (carousel)
- [ ] Employee testimonials (quotes)
- [ ] Open jobs section
- [ ] Follow button for job seekers
- [ ] Company stats (followers, open jobs, employees)
- [ ] Social media links
- [ ] SEO optimization for company pages

---

## 💰 Monetization & Advanced Features (Future Phases)

### Subscription System
- [ ] Define pricing tiers:
  - [ ] Free (Personal): Limited applications
  - [ ] Premium Personal: Unlimited applications + features
  - [ ] Free (Company): 1 job post
  - [ ] Basic Company: 5 job posts
  - [ ] Pro Company: Unlimited + AI screening
  - [ ] Enterprise: Custom solution
- [ ] Stripe integration for payments
- [ ] Subscription checkout flow
- [ ] Manage subscription (upgrade/downgrade/cancel)
- [ ] Feature gating middleware (check subscription tier)
- [ ] Invoice history page
- [ ] Payment method management (cards, bank accounts)
- [ ] Free trial period (14 days)
- [ ] Prorated billing for upgrades

### ATS Integrations (Company Only)
- [ ] Greenhouse OAuth integration
- [ ] Lever API integration
- [ ] Workday integration
- [ ] Sync jobs from external ATS
- [ ] Push candidates to external ATS
- [ ] Field mapping configuration UI
- [ ] Bidirectional sync (two-way)
- [ ] Zapier app creation (public integration)

### Video Introductions (Personal Only)
- [ ] Record 30-second video intro (in-browser)
- [ ] Upload pre-recorded video (MP4, max 50MB)
- [ ] Video upload to AWS S3 or Cloudflare Stream
- [ ] Generate video thumbnail
- [ ] Display video on profile (with play button)
- [ ] Video playback in applicant view
- [ ] Video compression/transcoding (background job)

### Live Chat (Real-Time)
- [ ] WebSocket-based live chat
- [ ] Chat widget on website
- [ ] Typing indicators
- [ ] Online/offline status
- [ ] Chat availability hours (company sets)
- [ ] Canned responses (quick replies)
- [ ] Chat assignment to team members
- [ ] Chat transcript export
- [ ] Mobile push for chat messages

---

## 🤖 Advanced AI Features (Long-Term)

### Predictive Hiring Analytics
- [ ] Train ML model on historical hiring data
- [ ] Predict hire probability for candidates (0-100%)
- [ ] Display prediction confidence level
- [ ] Explain prediction factors (feature importance)
- [ ] Retrain model monthly with new data

### Salary Negotiation Assistant (Personal)
- [ ] Integrate with salary databases (Glassdoor API, Payscale)
- [ ] Display market salary ranges for job title + location
- [ ] Provide negotiation tips based on offer
- [ ] Counter-offer suggestions
- [ ] Total compensation calculator (salary + benefits)

### Interview Question Generator (Company)
- [ ] Generate custom interview questions with Mistral AI
- [ ] Based on job role and required skills
- [ ] Technical vs behavioral questions
- [ ] Save questions to reusable templates
- [ ] Question bank with categories
- [ ] Rate question effectiveness (company feedback)

### Culture Fit Assessment
- [ ] Company defines culture values (survey/questionnaire)
- [ ] Candidates take culture fit quiz (10-15 questions)
- [ ] Calculate culture fit score (0-100)
- [ ] Display on application (alongside match score)
- [ ] Aggregate culture fit data for analytics

### Diversity & Inclusion Tools
- [ ] Optional demographic data collection (anonymous)
- [ ] Diversity analytics dashboard (company only)
- [ ] Anonymize candidate data during initial screening
- [ ] Inclusive language checker for job descriptions
- [ ] Highlight non-inclusive terms and suggest alternatives
- [ ] Compare company diversity to industry benchmarks
- [ ] EEOC compliance reporting

### Automated Reference Checking
- [ ] Request references from candidates (email form)
- [ ] Send automated reference questionnaires
- [ ] Collect reference responses (structured data)
- [ ] Display aggregated feedback to company
- [ ] Privacy controls for reference data
- [ ] Reference verification status tracking

---

## 🛠️ Technical Improvements (Ongoing)

### Performance Optimization
- [ ] Database query optimization:
  - [ ] Add indexes on frequently queried fields
  - [ ] Use select_related and prefetch_related
  - [ ] Implement database query logging
  - [ ] Identify and fix N+1 queries
- [ ] Caching strategy:
  - [ ] Cache job listings (1 hour TTL)
  - [ ] Cache company profiles (24 hour TTL)
  - [ ] Cache computed match scores (until profile changes)
  - [ ] Redis for session storage
- [ ] Frontend performance:
  - [ ] Lazy loading for images (IntersectionObserver)
  - [ ] Code splitting for JavaScript
  - [ ] Minify and compress static assets
  - [ ] CDN setup for static files (CloudFlare, AWS CloudFront)
- [ ] Database performance:
  - [ ] Connection pooling (pgBouncer for PostgreSQL)
  - [ ] Database read replicas for analytics queries
  - [ ] Partitioning for large tables (applications, notifications)

### Security Hardening
- [ ] Rate limiting on all API endpoints (django-ratelimit)
- [ ] CSRF protection (Django built-in, verify all forms)
- [ ] SQL injection prevention (use ORM, avoid raw SQL)
- [ ] XSS prevention (template auto-escaping, CSP headers)
- [ ] File upload security:
  - [ ] Validate file types (magic number check)
  - [ ] Scan uploads with antivirus (ClamAV)
  - [ ] Limit file sizes (5MB for resumes)
  - [ ] Store files outside web root
- [ ] Two-factor authentication (2FA):
  - [ ] TOTP-based (Google Authenticator, Authy)
  - [ ] SMS backup codes
  - [ ] Recovery codes
- [ ] Security headers:
  - [ ] Content-Security-Policy (CSP)
  - [ ] Strict-Transport-Security (HSTS)
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
- [ ] Secure session management:
  - [ ] HttpOnly and Secure cookies
  - [ ] Session timeout (2 weeks)
  - [ ] Logout from all devices option
- [ ] Input validation:
  - [ ] Whitelist allowed characters
  - [ ] Sanitize user input
  - [ ] Use Django forms for all user input
- [ ] Dependency security:
  - [ ] Regular dependency updates (pip-audit)
  - [ ] Security vulnerability scanning (Snyk, Dependabot)

### Testing & Quality Assurance
- [ ] Unit tests for models:
  - [ ] Test model methods
  - [ ] Test model validation
  - [ ] Test model signals
- [ ] Integration tests for views:
  - [ ] Test GET/POST requests
  - [ ] Test form submissions
  - [ ] Test authentication/authorization
- [ ] End-to-end tests for user flows:
  - [ ] User registration → profile setup → job apply
  - [ ] Company creates job → receives application → hires
- [ ] API tests:
  - [ ] Test all endpoints
  - [ ] Test error handling
  - [ ] Test rate limiting
- [ ] Test coverage:
  - [ ] Target: 80% code coverage
  - [ ] Generate coverage reports (coverage.py)
  - [ ] Fail CI if coverage drops below threshold
- [ ] Automated testing:
  - [ ] Set up GitHub Actions or GitLab CI
  - [ ] Run tests on every commit
  - [ ] Run tests on pull requests
- [ ] Load testing:
  - [ ] Simulate high traffic (Locust, Apache JMeter)
  - [ ] Test concurrent users (100, 500, 1000)
  - [ ] Identify bottlenecks

### Monitoring & Observability
- [ ] Error tracking:
  - [ ] Integrate Sentry for error monitoring
  - [ ] Alert on critical errors
  - [ ] Group similar errors
- [ ] Performance monitoring:
  - [ ] Application performance monitoring (APM): New Relic, Datadog
  - [ ] Track slow database queries
  - [ ] Track API response times
- [ ] User analytics:
  - [ ] Google Analytics 4 integration
  - [ ] Track page views, sessions, conversions
  - [ ] Set up goals (registration, application, hire)
- [ ] Uptime monitoring:
  - [ ] Pingdom, UptimeRobot, or StatusCake
  - [ ] Alert on downtime (email, SMS)
  - [ ] Public status page
- [ ] Log aggregation:
  - [ ] Centralized logging (ELK stack, Papertrail)
  - [ ] Structured logging (JSON format)
  - [ ] Log retention policy (90 days)
- [ ] Metrics dashboard:
  - [ ] System metrics (CPU, memory, disk)
  - [ ] Application metrics (requests/sec, error rate)
  - [ ] Business metrics (signups, applications, hires)

### Documentation
- [ ] API documentation:
  - [ ] OpenAPI/Swagger schema
  - [ ] Interactive API docs (Swagger UI)
  - [ ] Code examples for each endpoint
- [ ] User documentation:
  - [ ] User guide (how to use the platform)
  - [ ] FAQ page
  - [ ] Video tutorials for key features
- [ ] Developer documentation:
  - [ ] Architecture overview (system design)
  - [ ] Code structure guide
  - [ ] Contribution guidelines
  - [ ] Setup instructions (detailed README)
- [ ] Deployment documentation:
  - [ ] Production deployment guide
  - [ ] Environment variables documentation
  - [ ] Database migration guide
  - [ ] Scaling guide
- [ ] Code comments:
  - [ ] Docstrings for all functions/classes
  - [ ] Inline comments for complex logic
  - [ ] Type hints (Python 3.10+)

---

## 📱 Mobile App (Phase 6+)

### Mobile Development
- [ ] Choose framework (React Native or Flutter)
- [ ] iOS app development
- [ ] Android app development
- [ ] Responsive mobile UI/UX design
- [ ] Push notifications (FCM)
- [ ] Offline mode (cache critical data)
- [ ] Mobile-specific features:
  - [ ] Face ID / Touch ID for login
  - [ ] QR code scanning for quick apply
  - [ ] Voice search for jobs
- [ ] App Store submission (iOS)
- [ ] Google Play Store submission (Android)

---

## 🚀 Future Enhancements (Long-Term)

### Advanced Features
- [ ] Virtual career fairs (live video events)
- [ ] Group video interviews (multi-candidate panels)
- [ ] Anonymous company Q&A (Blind-style)
- [ ] Salary negotiation simulator (gamified)
- [ ] Employee referral program (incentivize referrals)
- [ ] Company review system (Glassdoor-like)
- [ ] Skill-based matching (not just keywords)
- [ ] Career path visualization (roadmap to dream job)
- [ ] Mentorship program (connect seniors with juniors)
- [ ] Community forum (job seekers helping each other)

---

## ✅ Completed Features

_(Move tasks here as they're completed)_

### Setup & Infrastructure
- [x] Project structure created
- [x] Django 5.0 project initialized
- [x] Database models designed (User, Profile, Job, Application, etc.)
- [x] Security settings configured (CSP, HSTS, CSRF)
- [x] Django Axes configured for account lockout
- [x] Celery configured for background tasks
- [x] Redis configured for caching and task queue
- [x] Email backend configured (SMTP)
- [x] Mistral AI API configured
- [x] README.md updated with comprehensive info
- [x] TODO.md created and organized
- [x] Logging configured (Django, security, Axes)

---

## 📝 Notes

### Development Workflow
1. **Phase-Based Approach**: Focus on one app at a time
2. **Test-Driven Development**: Write tests before implementing features
3. **Code Review**: All changes require review (even solo projects)
4. **Documentation**: Document features as you build them
5. **Git Hygiene**: Commit frequently with clear messages

### Priority Order
1. **Core Authentication** (accounts app) - Users must be able to sign up
2. **Profile Management** (accounts app) - Users need profiles before applying
3. **Resume Management** (resumes app) - Required for applications
4. **Job Posting** (jobs app) - Companies need to post jobs
5. **Application System** (applications app) - Core functionality
6. **AI Screening** (screening app) - Key differentiator
7. **Dashboards** (dashboard app) - User experience
8. **Notifications** (notifications app) - User engagement
9. **Everything Else** - Build based on user feedback

### Testing Strategy
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test how components work together
- **E2E Tests**: Test complete user journeys
- **Run tests locally** before committing
- **CI/CD runs tests** on every pull request

### Feedback Loops
- Gather user feedback after each major feature release
- Iterate based on analytics and user feedback
- Don't build features users don't want
- Focus on metrics that matter (signups, applications, hires)

---

## 🎯 Success Metrics

### North Star Metrics
- **For Platform**: Total successful hires through platform
- **For Job Seekers**: Time to job offer
- **For Companies**: Time to hire + quality of hire

### Key Performance Indicators (KPIs)
- **User Acquisition**: New signups per week
- **User Activation**: % of users who complete profile
- **User Retention**: % of users active after 30 days
- **Application Rate**: Applications per job posting
- **Match Accuracy**: % of high-match candidates who get hired
- **Customer Satisfaction**: NPS score (Net Promoter Score)

---

**Remember**: Build features incrementally, test thoroughly, and iterate based on user feedback! 🚀

Focus on delivering value to users, not just adding features.
