# HireSight Development Roadmap

**Version**: 1.0  
**Last Updated**: January 2026  
**Project Status**: Pre-MVP

---

## 📋 Table of Contents
- [Phase 1: MVP Foundation](#phase-1-mvp-foundation-months-1-2)
- [Phase 2: Core Features](#phase-2-core-features-months-3-4)
- [Phase 3: Engagement & Growth](#phase-3-engagement--growth-months-5-6)
- [Phase 4: Scale & Monetization](#phase-4-scale--monetization-months-7-9)
- [Phase 5: Advanced AI](#phase-5-advanced-ai-months-10-12)
- [Technical Debt & Refactoring](#technical-debt--refactoring)
- [Bug Tracker](#bug-tracker)

---

## 🎯 Phase 1: MVP Foundation (Months 1-2)

**Goal**: Launch a working product that allows job seekers to apply and recruiters to screen candidates using AI.

### **1.1 Authentication & User Management**

#### Backend Tasks
- [x] **User Model**
  - [x] Create `users` table with `id`, `email`, `password_hash`, `account_type` (enum: personal/company), `is_verified`, `is_active`, `created_at`, `updated_at`
  - [x] Add unique constraints on `email`
  - [x] Create indexes on `email` and `account_type`
  
- [ ] **Authentication Service**
  - [x] Implement password hashing with bcrypt (min 12 rounds) _(implemented with Argon2 via passlib)_
  - [x] Generate JWT tokens (access token: 15min, refresh token: 7 days)
  - [x] Store refresh tokens in httpOnly cookies
  - [x] Implement token refresh endpoint
  - [x] Create middleware for protected routes
  - [x] Add role-based access control (RBAC) decorator
  
- [ ] **Registration Flow**
  - [x] POST `/api/auth/register` - Create new user with account type selection
  - [x] Send verification email with token (expires in 24 hours)
  - [x] POST `/api/auth/verify-email` - Verify email with token
  - [x] Implement rate limiting (5 registration attempts per hour per IP)
  
- [ ] **Login/Logout**
  - [x] POST `/api/auth/login` - Authenticate and return JWT
  - [x] POST `/api/auth/logout` - Invalidate refresh token
  - [x] GET `/api/auth/me` - Get current user info
  - [x] Implement login attempt tracking (lock after 5 failed attempts for 30 minutes)
  
- [ ] **Password Reset**
  - [x] POST `/api/auth/forgot-password` - Send reset email
  - [x] POST `/api/auth/reset-password` - Reset with token
  - [x] Tokens expire in 1 hour

#### Frontend Tasks
- [ ] **Landing Page**
  - [x] Hero section with dual CTA (For Job Seekers / For Recruiters)
  - [x] Features showcase
  - [x] Testimonials section
  - [ ] Pricing preview
  - [x] Footer with links
  
- [ ] **Authentication Modal**
  - [x] Sign Up form with account type toggle (Personal / Company)
  - [x] Sign In form
  - [x] Form validation (email format, password strength)
  - [x] Error handling with user-friendly messages
  - [x] Loading states during API calls
  - [ ] Success animations
  
- [ ] **Email Verification Flow**
  - [ ] Display verification pending message after signup
  - [ ] Verification success/error page
  - [ ] Resend verification email option
  
- [ ] **Password Reset Flow**
  - [ ] Forgot password form
  - [ ] Email sent confirmation
  - [ ] Reset password form (with token from URL)
  - [ ] Password strength indicator

#### Testing
- [ ] Unit tests for password hashing
- [ ] Integration tests for registration flow
- [ ] E2E tests for login/logout
- [ ] Test JWT expiration and refresh
- [ ] Test rate limiting

---

### **1.2 User Profiles (Personal & Company)**

#### Backend Tasks
- [x] **Personal Profile Model**
  - [x] Create `personal_profiles` table
  - [x] Fields: `user_id` (FK), `full_name`, `headline`, `location`, `phone`, `bio`
  - [x] JSONB fields: `skills` (array of objects), `experience` (array), `education` (array), `certifications` (array), `portfolio_links` (array)
  - [x] Preferences: `preferred_job_types` (JSONB), `salary_expectation_min`, `salary_expectation_max`, `availability`
  - [x] Privacy: `profile_visibility` (public/verified_companies/private)
  
- [x] **Company Profile Model**
  - [x] Create `company_profiles` table
  - [x] Fields: `user_id` (FK), `company_name`, `logo_url`, `industry`, `company_size`
  - [x] JSONB fields: `locations` (array), `benefits` (array), `team_photos` (array)
  - [x] Details: `website`, `description`, `mission`, `culture`, `founded_year`
  - [x] Verification: `verification_status` (unverified/pending/verified), `verification_docs_url`
  
- [ ] **Profile Endpoints**
  - [x] GET `/api/users/me/profile` - Get own profile (role-based response)
  - [x] PUT `/api/users/me/profile` - Update profile
  - [ ] POST `/api/users/me/avatar` - Upload profile picture (S3/Cloudinary)
  - [x] GET `/api/users/{id}/profile` - Get public profile (with privacy checks)
  - [x] GET `/api/companies` - List all verified companies (for job seekers)
  - [x] GET `/api/companies/{id}` - Get company public page

#### Frontend Tasks
- [ ] **Personal Profile Page**
  - [ ] Profile header (avatar, name, headline, location)
  - [ ] About section (bio)
  - [ ] Skills section (tags with proficiency levels)
  - [ ] Experience timeline (company, role, dates, description)
  - [ ] Education section
  - [ ] Certifications & licenses
  - [ ] Portfolio links (GitHub, LinkedIn, personal site)
  - [ ] Edit mode with inline editing
  - [ ] Profile completion progress bar (gamification)
  
- [ ] **Company Profile Page**
  - [ ] Company header (logo, name, industry, size)
  - [ ] About section (description, mission)
  - [ ] Culture & values section
  - [ ] Benefits offered (tags)
  - [ ] Team photos gallery
  - [ ] Office locations (map integration)
  - [ ] Open jobs section
  - [ ] Follower count display
  - [ ] Edit mode for own company
  
- [ ] **Profile Settings**
  - [ ] Privacy controls (who can see profile)
  - [ ] Notification preferences
  - [ ] Account security (password change, 2FA setup)
  - [ ] Connected accounts (LinkedIn, GitHub)
  - [ ] Delete account option (with confirmation)

#### Testing
- [ ] Test profile creation on signup
- [ ] Test profile update with various field combinations
- [ ] Test file upload (size limits, format validation)
- [ ] Test privacy controls (who can view profiles)
- [ ] Test company verification workflow

---

### **1.3 Resume Management**

#### Backend Tasks
- [x] **Resume Model**
  - [x] Create `resumes` table
  - [x] Fields: `id`, `user_id` (FK), `filename`, `file_url`, `version_name`, `is_primary`, `uploaded_at`
  - [x] `parsed_data` (JSONB): extracted name, email, phone, skills, experience, education
  - [x] Add constraint: only one primary resume per user
  
- [ ] **Resume Parser Service**
  - [ ] Install and configure `pyresparser`, `PyMuPDF`, `python-docx`
  - [ ] Extract text from PDF and DOCX
  - [ ] Use spaCy NER to extract entities (names, dates, organizations)
  - [ ] Extract email with regex
  - [ ] Extract phone numbers (multiple formats)
  - [ ] Extract skills (match against predefined skill taxonomy + custom extraction)
  - [ ] Extract experience (company, role, dates, description)
  - [ ] Extract education (institution, degree, dates)
  - [ ] Normalize and clean extracted data
  - [ ] Store raw text and parsed JSON
  
- [ ] **Resume Endpoints**
  - [x] POST `/api/resumes/upload` - Upload resume file (max 5MB, PDF/DOCX only)
  - [x] POST `/api/resumes/parse` - Parse uploaded resume
  - [x] GET `/api/resumes` - List user's resumes
  - [x] GET `/api/resumes/{id}` - Get resume details (with parsed data)
  - [x] PUT `/api/resumes/{id}` - Update resume metadata (version name, is_primary)
  - [x] DELETE `/api/resumes/{id}` - Delete resume
  - [x] POST `/api/resumes/{id}/set-primary` - Set as primary resume

#### Frontend Tasks
- [ ] **Resume Upload Component**
  - [ ] Drag-and-drop file upload area
  - [ ] File type validation (PDF, DOCX only)
  - [ ] File size validation (max 5MB)
  - [ ] Upload progress indicator
  - [ ] Success/error messages
  
- [ ] **Resume List View**
  - [ ] Display all uploaded resumes
  - [ ] Show version name, upload date, file size
  - [ ] Mark primary resume with badge
  - [ ] Quick actions: Download, Set as Primary, Delete
  - [ ] Preview resume (PDF viewer in modal)
  
- [ ] **Resume Auto-Fill Profile**
  - [ ] After parsing, show confirmation dialog
  - [ ] Display parsed data with editable fields
  - [ ] "Fill Profile" button to populate personal profile
  - [ ] Show conflicts if profile already has data

#### Testing
- [ ] Test resume upload with various file formats
- [ ] Test parsing accuracy with sample resumes
- [ ] Test error handling (corrupted files, oversized files)
- [ ] Test primary resume constraint
- [ ] Test file deletion (also delete from storage)

---

### **1.4 Job Posting & Browsing**

#### Backend Tasks
- [x] **Job Model**
  - [x] Create `jobs` table
  - [x] Fields: `id`, `company_id` (FK), `title`, `description`, `location`
  - [x] Employment: `remote_type` (remote/hybrid/onsite), `employment_type` (full-time/part-time/contract/internship)
  - [x] Compensation: `salary_min`, `salary_max`, `currency` (default USD)
  - [x] JSONB fields: `requirements` (skills, experience, education), `screening_questions` (array of questions)
  - [x] Status: `status` (draft/active/closed), `created_at`, `updated_at`, `expires_at` (optional)
  - [x] Metrics: `view_count`, `application_count`
  
- [ ] **Job Endpoints (Company only)**
  - [x] POST `/api/jobs` - Create new job
  - [x] GET `/api/jobs` - List company's jobs (with filters)
  - [x] GET `/api/jobs/{id}` - Get job details
  - [x] PUT `/api/jobs/{id}` - Update job
  - [x] DELETE `/api/jobs/{id}` - Delete job (soft delete)
  - [x] POST `/api/jobs/{id}/close` - Close job to applications
  - [x] POST `/api/jobs/{id}/duplicate` - Create copy of job

- [ ] **Job Search Endpoints (Personal only)**
  - [x] GET `/api/jobs/search` - Search all active jobs
  - [x] Query params: `q` (keyword), `location`, `remote_type`, `employment_type`, `salary_min`, `skills` (comma-separated), `page`, `limit`
  - [x] GET `/api/jobs/{id}/similar` - Get similar jobs (based on skills)
  - [x] POST `/api/jobs/{id}/view` - Track job view (increment view_count)

#### Frontend Tasks
- [ ] **Job Posting Form (Company)**
  - [ ] Job title input
  - [ ] Description (rich text editor with formatting)
  - [ ] Location input with autocomplete
  - [ ] Remote type selector (radio buttons)
  - [ ] Employment type selector
  - [ ] Salary range inputs (optional)
  - [ ] Requirements builder (add/remove skills, min experience, education)
  - [ ] Screening questions builder (add custom questions)
  - [ ] Preview mode before publishing
  - [ ] Save as draft option
  
- [ ] **Job List Page (Company)**
  - [ ] Card view of all jobs (active, draft, closed)
  - [ ] Filter by status
  - [ ] Sort by date, applications, views
  - [ ] Quick actions: Edit, Duplicate, Close, View Analytics
  - [ ] Bulk actions (close multiple, delete multiple)
  
- [ ] **Job Search Page (Personal)**
  - [ ] Search bar with autocomplete
  - [ ] Filters sidebar (location, remote, salary, skills)
  - [ ] Job cards (title, company, location, salary, skills)
  - [ ] "Save Job" bookmark button
  - [ ] "Apply" button (opens application modal)
  - [ ] Infinite scroll or pagination
  - [ ] Sort options (relevance, date, salary)
  
- [ ] **Job Detail Page**
  - [ ] Full job description
  - [ ] Company info section (with link to company page)
  - [ ] Requirements list
  - [ ] Apply button (for job seekers)
  - [ ] Save/Unsave button
  - [ ] Share button (copy link, social media)
  - [ ] Related jobs section

#### Testing
- [ ] Test job creation with all fields
- [ ] Test job search with various filters
- [ ] Test pagination and sorting
- [ ] Test job visibility (only active jobs visible to job seekers)
- [ ] Test authorization (job seekers can't create jobs)

---

### **1.5 AI-Powered Resume Screening**

#### Backend Tasks
- [ ] **Setup ML Pipeline**
  - [ ] Install `sentence-transformers` library
  - [ ] Load `all-MiniLM-L6-v2` model (384-dim embeddings)
  - [ ] Create embedding generation utility
  - [ ] Implement cosine similarity calculation
  
- [ ] **Screening Service**
  - [ ] Function: `generate_job_embedding(job_description)` → vector
  - [ ] Function: `generate_resume_embedding(resume_text)` → vector
  - [ ] Function: `calculate_match_score(job_embedding, resume_embedding)` → 0-100
  - [ ] Function: `explain_match(job_requirements, resume_skills)` → JSONB with strengths, gaps
  - [ ] Skill matching: exact match, synonym match, partial match
  - [ ] Experience matching: compare years of experience
  - [ ] Education matching: degree level, field of study
  
- [ ] **Screening Endpoints (Company only)**
  - [ ] POST `/api/screening/bulk-upload` - Upload multiple resumes (up to 50 per batch)
  - [ ] POST `/api/screening/process` - Process resumes against job description
  - [ ] GET `/api/screening/results/{job_id}` - Get ranked candidates for job
  - [ ] POST `/api/screening/export` - Export results to Excel/PDF

#### Frontend Tasks
- [ ] **Bulk Resume Upload (Company)**
  - [ ] Multi-file upload component (drag-and-drop, file picker)
  - [ ] Upload progress for each file
  - [ ] Display uploaded files with status (pending, processing, completed, error)
  - [ ] Select job to match against (dropdown)
  
- [ ] **Screening Results Page**
  - [ ] Top candidates list (ranked by match score)
  - [ ] Each candidate card shows:
    - [ ] Name, contact info
    - [ ] Match score (0-100) with color coding
    - [ ] Top matching skills (badges)
    - [ ] Skill gaps (what's missing)
    - [ ] Years of experience
    - [ ] Quick actions: View Full Resume, Contact, Reject
  - [ ] Filter by score threshold (e.g., show only 80+)
  - [ ] Bulk actions: Move to pipeline, Send email, Export
  
- [ ] **Match Explanation Modal**
  - [ ] Detailed breakdown of match score
  - [ ] Strengths: skills match, experience match, education match
  - [ ] Gaps: missing skills, insufficient experience
  - [ ] Visual chart (radar chart or bar chart)

#### Testing
- [ ] Test embedding generation consistency
- [ ] Test match score calculation accuracy (manually verify samples)
- [ ] Test bulk upload with 50 resumes
- [ ] Test error handling (corrupted files, parsing failures)
- [ ] Benchmark performance (time to process 50 resumes)

---

### **1.6 Application System**

#### Backend Tasks
- [x] **Application Model**
  - [x] Create `applications` table
  - [x] Fields: `id`, `job_id` (FK), `user_id` (FK), `resume_id` (FK), `cover_letter` (text)
  - [x] Status: `status` (pending/screening/interview/offer/hired/rejected), `match_score`, `match_explanation` (JSONB)
  - [x] Timestamps: `applied_at`, `updated_at`
  - [x] Add unique constraint: (`job_id`, `user_id`) to prevent duplicate applications
  
- [ ] **Application Endpoints**
  - [x] POST `/api/applications` - Apply for job (Job Seeker)
    - [x] Body: `job_id`, `resume_id`, `cover_letter` (optional)
    - [ ] Auto-calculate match score on apply
  - [ ] GET `/api/applications` - List applications
    - [x] For Job Seekers: their own applications (filter by status, job)
    - [ ] For Companies: applications for their jobs (filter by job, status)
  - [x] GET `/api/applications/{id}` - Get application details
  - [x] PUT `/api/applications/{id}/status` - Update status (Company only)
  - [ ] DELETE `/api/applications/{id}` - Withdraw application (Job Seeker, only if pending)

#### Frontend Tasks
- [ ] **Application Modal (Job Seeker)**
  - [ ] Display job title and company
  - [ ] Resume selector (dropdown of user's resumes)
  - [ ] Cover letter textarea (optional, rich text)
  - [ ] Preview application button
  - [ ] Submit button with loading state
  - [ ] Success confirmation with application number
  
- [ ] **My Applications Page (Job Seeker)**
  - [ ] List all applications (cards or table)
  - [ ] Filter by status (All, Pending, Interview, Offer, Rejected)
  - [ ] Each application shows:
    - [ ] Job title, company name, location
    - [ ] Applied date
    - [ ] Current status (with badge)
    - [ ] Match score (if available)
    - [ ] Quick actions: View Job, Withdraw Application
  - [ ] Empty state when no applications
  
- [ ] **Applications List (Company)**
  - [ ] Displayed on job detail page
  - [ ] List all applications for that job
  - [ ] Each application card shows:
    - [ ] Candidate name, headline
    - [ ] Match score (color-coded)
    - [ ] Applied date
    - [ ] Quick actions: View Profile, View Resume, Update Status
  - [ ] Filter by status
  - [ ] Sort by score, date

#### Testing
- [ ] Test application submission
- [ ] Test duplicate application prevention
- [ ] Test application withdrawal
- [ ] Test status update by recruiter
- [ ] Test application list filtering and sorting

---

### **1.7 Basic Dashboard**

#### Backend Tasks
- [ ] **Dashboard Stats Endpoints**
  - [ ] GET `/api/dashboard/stats` - Get role-specific stats
    - [ ] For Job Seekers: total applications, pending count, interview count, success rate
    - [ ] For Companies: total jobs, total applications, avg match score, avg time-to-hire
  - [ ] GET `/api/dashboard/recent-activity` - Get recent activity feed
    - [ ] For Job Seekers: application status changes, new job matches, messages
    - [ ] For Companies: new applications, candidate responses, job views

#### Frontend Tasks
- [ ] **Personal Dashboard**
  - [ ] Stats cards (applications, pending, interviews, offers)
  - [ ] Application status chart (pie chart)
  - [ ] Recent applications list (last 5)
  - [ ] Recommended jobs section
  - [ ] Profile completion widget
  - [ ] Quick actions: Upload Resume, Browse Jobs, Update Profile
  
- [ ] **Company Dashboard**
  - [ ] Stats cards (active jobs, total applications, avg match score, time saved)
  - [ ] Active jobs list with metrics (views, applications)
  - [ ] Recent applications (last 10 across all jobs)
  - [ ] Top matching candidates (across all jobs)
  - [ ] Quick actions: Post Job, Screen Resumes, View Analytics

#### Testing
- [ ] Test dashboard loads correctly for both roles
- [ ] Test stats calculations accuracy
- [ ] Test recent activity feed ordering
- [ ] Test empty states for new users

---

## 🚀 Phase 2: Core Features (Months 3-4)

**Goal**: Enhance user engagement with application pipeline, following, messaging, and notifications.

### **2.1 Application Pipeline (Kanban)**

#### Backend Tasks
- [ ] **Pipeline Stages**
  - [ ] Define status transitions: pending → screening → interview → offer → hired/rejected
  - [ ] Add validation rules (e.g., can't go from pending to hired directly)
  - [ ] Add `rejection_reason` field to applications table (for rejected status)
  
- [ ] **Pipeline Endpoints**
  - [ ] PUT `/api/applications/{id}/move` - Move to different stage
  - [ ] POST `/api/applications/{id}/note` - Add internal note (Company only)
  - [ ] GET `/api/applications/pipeline/{job_id}` - Get all applications grouped by stage

#### Frontend Tasks
- [ ] **Kanban Board (Company)**
  - [ ] Columns: New, Screening, Interview, Offer, Hired, Rejected
  - [ ] Drag-and-drop to move candidates between stages
  - [ ] Each card shows: name, match score, applied date
  - [ ] Click card to view full application
  - [ ] Bulk actions: Move multiple candidates, Send bulk email
  - [ ] Filter by job (dropdown)
  
- [ ] **Application Detail View**
  - [ ] Full candidate profile
  - [ ] Resume viewer (embedded PDF)
  - [ ] Cover letter display
  - [ ] Match score breakdown
  - [ ] Internal notes section (Company only)
  - [ ] Status history timeline
  - [ ] Action buttons: Move Stage, Schedule Interview, Send Message, Reject

#### Testing
- [ ] Test drag-and-drop functionality
- [ ] Test status transition validation
- [ ] Test bulk actions
- [ ] Test kanban board performance with 100+ candidates

---

### **2.2 Following System**

#### Backend Tasks
- [ ] **Follow Model**
  - [ ] Create `follows` table
  - [ ] Fields: `id`, `follower_id` (FK users), `following_id` (FK users), `following_type` (user/company), `created_at`
  - [ ] Unique constraint: (`follower_id`, `following_id`, `following_type`)
  
- [ ] **Follow Endpoints**
  - [ ] POST `/api/follow/{user_id}` - Follow user or company
  - [ ] DELETE `/api/follow/{user_id}` - Unfollow
  - [ ] GET `/api/follow/followers` - Get list of followers
  - [ ] GET `/api/follow/following` - Get list of following
  - [ ] GET `/api/follow/suggestions` - Get follow suggestions (companies in user's industry, users with similar roles)

#### Frontend Tasks
- [ ] **Follow Button Component**
  - [ ] Display on company profiles and user profiles
  - [ ] Toggle between "Follow" and "Following"
  - [ ] Show follower count
  - [ ] Loading state during API call
  
- [ ] **Followers/Following Page**
  - [ ] Tabs: Followers | Following
  - [ ] List view with avatar, name, headline
  - [ ] Unfollow button on following tab
  - [ ] Search/filter followers
  
- [ ] **Notifications on Follow**
  - [ ] Companies get notified when someone follows them
  - [ ] Feed integration (show new jobs from followed companies)

#### Testing
- [ ] Test follow/unfollow functionality
- [ ] Test follower count updates
- [ ] Test follow suggestions algorithm
- [ ] Test privacy (can't follow private profiles)

---

### **2.3 In-App Messaging**

#### Backend Tasks
- [ ] **Message Model**
  - [ ] Create `messages` table
  - [ ] Fields: `id`, `conversation_id`, `sender_id` (FK), `receiver_id` (FK), `subject`, `body`, `is_read`, `sent_at`
  - [ ] Create `conversations` table for grouping messages
  
- [ ] **Messaging Endpoints**
  - [ ] POST `/api/messages` - Send message
  - [ ] GET `/api/messages` - Get user's conversations (inbox)
  - [ ] GET `/api/messages/{conversation_id}` - Get conversation thread
  - [ ] PUT `/api/messages/{id}/read` - Mark as read
  - [ ] DELETE `/api/messages/{id}` - Delete message

#### Frontend Tasks
- [ ] **Inbox Page**
  - [ ] List of conversations (like email inbox)
  - [ ] Show sender name, subject, preview, date
  - [ ] Unread indicator (bold text, badge)
  - [ ] Search conversations
  
- [ ] **Conversation Thread**
  - [ ] Chat-style message display
  - [ ] Message composer (subject for first message, then just body)
  - [ ] Send button
  - [ ] Real-time updates (Socket.IO or polling)
  
- [ ] **Compose Message Modal**
  - [ ] Recipient selector (search users/companies)
  - [ ] Subject input
  - [ ] Body textarea
  - [ ] Send button
  
- [ ] **Message Notifications**
  - [ ] Badge on messaging icon in header
  - [ ] Browser notification for new messages (with permission)

#### Testing
- [ ] Test message sending
- [ ] Test conversation threading
- [ ] Test unread count accuracy
- [ ] Test real-time updates

---

### **2.4 Notification System**

#### Backend Tasks
- [ ] **Notification Model**
  - [ ] Create `notifications` table
  - [ ] Fields: `id`, `user_id` (FK), `type` (application/message/job/follow), `title`, `message`, `link`, `is_read`, `created_at`
  
- [ ] **Notification Service**
  - [ ] Function: `create_notification(user_id, type, title, message, link)`
  - [ ] Trigger notifications on:
    - [ ] Application status change
    - [ ] New message received
    - [ ] New job from followed company
    - [ ] Someone followed user/company
    - [ ] Interview scheduled
    - [ ] New application received (for companies)
  
- [ ] **Notification Endpoints**
  - [ ] GET `/api/notifications` - Get user's notifications (paginated)
  - [ ] PUT `/api/notifications/{id}/read` - Mark as read
  - [ ] PUT `/api/notifications/read-all` - Mark all as read
  - [ ] DELETE `/api/notifications/{id}` - Delete notification

#### Frontend Tasks
- [ ] **Notification Bell Icon**
  - [ ] Badge with unread count
  - [ ] Click to open dropdown
  - [ ] List last 5 notifications
  - [ ] "View All" link to full notifications page
  
- [ ] **Notifications Page**
  - [ ] List all notifications (grouped by date)
  - [ ] Filter by type (All, Applications, Messages, Jobs)
  - [ ] Each notification shows: icon, title, message, time
  - [ ] Click to navigate to relevant page
  - [ ] Mark all as read button
  
- [ ] **Real-Time Notifications**
  - [ ] Socket.IO connection for live updates
  - [ ] Toast notification for important events
  - [ ] Browser push notifications (with permission)

#### Testing
- [ ] Test notification creation for various events
- [ ] Test unread count calculation
- [ ] Test mark as read functionality
- [ ] Test real-time delivery

---

### **2.5 Advanced Search & Filters**

#### Backend Tasks
- [ ] **Elasticsearch Integration (Optional)**
  - [ ] Index jobs in Elasticsearch for fast full-text search
  - [ ] Index user profiles for candidate search (Company feature)
  
- [ ] **Enhanced Search Endpoints**
  - [ ] GET `/api/jobs/search` - Enhanced with faceted search
  - [ ] Filters: `skills[]`, `experience_min`, `education_level`, `company_size`, `benefits[]`
  - [ ] GET `/api/candidates/search` - Search candidates (Company only)
  - [ ] Filters: `skills[]`, `experience_min`, `location`, `availability`

#### Frontend Tasks
- [ ] **Advanced Filters Sidebar**
  - [ ] Skills multi-select (autocomplete)
  - [ ] Experience range slider
  - [ ] Salary range slider
  - [ ] Location with radius
  - [ ] Remote type checkboxes
  - [ ] Company size checkboxes
  - [ ] Benefits checkboxes
  - [ ] Apply filters button
  - [ ] Clear all filters button
  
- [ ] **Search Results Page**
  - [ ] Display filter chips (removable)
  - [ ] Results count
  - [ ] Sort options dropdown
  - [ ] Pagination or infinite scroll
  - [ ] "Save Search" option (for alerts)

#### Testing
- [ ] Test search with various filter combinations
- [ ] Test search performance with large datasets
- [ ] Test autocomplete suggestions
- [ ] Test pagination

---

### **2.6 Analytics Dashboards**

#### Backend Tasks
- [ ] **Analytics Endpoints**
  - [ ] GET `/api/analytics/jobs/{job_id}` - Job metrics (views, applications, conversion rate)
  - [ ] GET `/api/analytics/company` - Company-wide metrics (all jobs aggregate)
  - [ ] GET `/api/analytics/applications` - Application funnel (how many in each stage)
  - [ ] GET `/api/analytics/candidate-sources` - Where candidates found the job
  - [ ] GET `/api/analytics/time-to-hire` - Average days from posting to hire

#### Frontend Tasks
- [ ] **Job Analytics Page (Company)**
  - [ ] Line chart: Views over time
  - [ ] Funnel chart: Views → Applies → Interviews → Hires
  - [ ] Pie chart: Application status distribution
  - [ ] Table: Top referring sources
  - [ ] Metrics cards: Total views, applications, acceptance rate, avg match score
  
- [ ] **Company Analytics Dashboard**
  - [ ] Overview of all jobs
  - [ ] Bar chart: Applications per job
  - [ ] Line chart: Hiring trend over time
  - [ ] Metrics: Total hires, avg time-to-hire, cost-per-hire (if tracked)
  
- [ ] **Personal Analytics (Job Seeker)**
  - [ ] Application success rate
  - [ ] Profile views over time
  - [ ] Skills in demand (from job matches)
  - [ ] Comparison to similar users (anonymized)

#### Testing
- [ ] Test data accuracy of analytics
- [ ] Test chart rendering with various data sizes
- [ ] Test date range selectors
- [ ] Test export to CSV/PDF

---

## 🎨 Phase 3: Engagement & Growth (Months 5-6)

**Goal**: Increase user engagement and retention with skill assessments, recommendations, and social features.

### **3.1 Skill Assessments**

#### Backend Tasks
- [ ] **Assessment Model**
  - [ ] Create `skill_assessments` table (id, skill_name, questions (JSONB), difficulty, duration_minutes)
  - [ ] Create `user_assessment_results` table (user_id, assessment_id, score, completed_at)
  
- [ ] **Assessment Endpoints**
  - [ ] GET `/api/assessments` - List available assessments
  - [ ] GET `/api/assessments/{id}` - Get assessment questions
  - [ ] POST `/api/assessments/{id}/submit` - Submit answers and get score
  - [ ] GET `/api/users/me/assessments` - Get completed assessments

#### Frontend Tasks
- [ ] **Assessments Page**
  - [ ] Browse available skill tests
  - [ ] Filter by skill category
  - [ ] Each card shows: skill, difficulty, duration, your score (if taken)
  - [ ] "Take Test" button
  
- [ ] **Assessment Interface**
  - [ ] Display questions one at a time
  - [ ] Multiple choice or code editor (for programming tests)
  - [ ] Timer countdown
  - [ ] Progress indicator
  - [ ] Submit button
  
- [ ] **Results Page**
  - [ ] Score display (percentage)
  - [ ] Correct/incorrect answers review
  - [ ] Certificate download (PDF)
  - [ ] Share on profile option

#### Testing
- [ ] Test assessment scoring logic
- [ ] Test timer functionality
- [ ] Test answer submission
- [ ] Test certificate generation

---

### **3.2 Interview Scheduling**

#### Backend Tasks
- [ ] **Interview Model**
  - [ ] Create `interviews` table (id, application_id, interviewer_id, candidate_id, scheduled_at, duration_minutes, location/meeting_link, status (scheduled/completed/cancelled))
  
- [ ] **Interview Endpoints**
  - [ ] POST `/api/interviews` - Schedule interview (Company)
  - [ ] GET `/api/interviews` - Get upcoming interviews (for both roles)
  - [ ] PUT `/api/interviews/{id}` - Update interview (reschedule)
  - [ ] PUT `/api/interviews/{id}/cancel` - Cancel interview
  - [ ] POST `/api/interviews/{id}/feedback` - Add interview feedback (Company)

#### Frontend Tasks
- [ ] **Schedule Interview Modal (Company)**
  - [ ] Date & time picker
  - [ ] Duration selector
  - [ ] Location or video meeting link
  - [ ] Interviewer selector (team members)
  - [ ] Custom message to candidate
  - [ ] Send calendar invite option
  
- [ ] **My Interviews Page**
  - [ ] Calendar view of scheduled interviews
  - [ ] List view with filters (upcoming, past)
  - [ ] Each interview shows: candidate name, date/time, location, status
  - [ ] Quick actions: Join Meeting, Reschedule, Cancel
  
- [ ] **Interview Reminders**
  - [ ] Email notification 24 hours before
  - [ ] Email notification 1 hour before
  - [ ] In-app notification

#### Testing
- [ ] Test interview scheduling
- [ ] Test calendar integration
- [ ] Test reminder emails
- [ ] Test timezone handling

---

### **3.3 Company Branding Pages**

#### Backend Tasks
- [ ] **Company Page Enhancements**
  - [ ] Add `team_members` JSONB to company_profiles (photos, names, roles)
  - [ ] Add `office_photos` array to company_profiles
  - [ ] Add `testimonials` JSONB (employee testimonials)
  
- [ ] **Company Page Endpoints**
  - [ ] GET `/api/companies/{id}/jobs` - All active jobs for company
  - [ ] GET `/api/companies/{id}/reviews` - Company reviews (if Phase 4 completed)
  - [ ] GET `/api/companies/{id}/stats` - Public stats (total employees, open jobs, followers)

#### Frontend Tasks
- [ ] **Public Company Page**
  - [ ] Hero section with logo, name, tagline
  - [ ] About section (description, mission, values)
  - [ ] Culture section (photos, videos)
  - [ ] Benefits section (icons + descriptions)
  - [ ] Team section (photos + names)
  - [ ] Office locations (map)
  - [ ] Open jobs section
  - [ ] Follow button
  - [ ] Share button
  
- [ ] **Company Page Builder (Company)**
  - [ ] Drag-and-drop section reordering
  - [ ] Upload team photos
  - [ ] Add/edit benefits
  - [ ] Add employee testimonials
  - [ ] Preview mode

#### Testing
- [ ] Test company page rendering
- [ ] Test SEO meta tags
- [ ] Test public visibility
- [ ] Test page builder functionality

---

### **3.4 Resume Optimization Tips**

#### Backend Tasks
- [ ] **Resume Analysis Service**
  - [ ] Function: `analyze_resume(resume_text)` → feedback object
  - [ ] Check for: action verbs, quantifiable achievements, typos, length, formatting
  - [ ] Calculate ATS-friendliness score
  - [ ] Suggest improvements
  
- [ ] **Resume Optimization Endpoint**
  - [ ] POST `/api/resumes/{id}/analyze` - Get optimization suggestions

#### Frontend Tasks
- [ ] **Resume Analyzer Component**
  - [ ] Display resume score (0-100)
  - [ ] List of suggestions (categorized: Critical, Recommended, Optional)
  - [ ] Each suggestion shows: issue, example, how to fix
  - [ ] Re-analyze button after making changes
  
- [ ] **Integration with Resume Upload**
  - [ ] Show analysis immediately after upload
  - [ ] Option to apply suggestions before finalizing

#### Testing
- [ ] Test analysis accuracy
- [ ] Test suggestion quality
- [ ] Test re-analysis after edits

---

### **3.5 Job Recommendations**

#### Backend Tasks
- [ ] **Recommendation Engine**
  - [ ] Function: `get_recommended_jobs(user_id)` → list of jobs
  - [ ] Algorithm:
    - [ ] Match skills (weighted heavily)
    - [ ] Match experience level
    - [ ] Match location preference
    - [ ] Match salary expectation
    - [ ] Collaborative filtering (jobs similar users applied to)
  - [ ] Return jobs sorted by relevance score
  
- [ ] **Recommendation Endpoints**
  - [ ] GET `/api/recommendations/jobs` - Get personalized job recommendations
  - [ ] POST `/api/recommendations/feedback` - Thumbs up/down on recommendation

#### Frontend Tasks
- [ ] **Recommended Jobs Section**
  - [ ] Display on dashboard and job search page
  - [ ] "Why recommended?" tooltip (shows matching skills)
  - [ ] Feedback buttons (thumbs up/down)
  - [ ] Dismiss button
  
- [ ] **Recommendation Settings**
  - [ ] Toggle recommendation notifications
  - [ ] Adjust preferences (remote, salary, etc.)

#### Testing
- [ ] Test recommendation relevance
- [ ] Test feedback loop (improve over time)
- [ ] Test cold start problem (new users with no data)

---

### **3.6 Mobile App (React Native - Optional)**

#### Tasks
- [ ] Setup React Native project with TypeScript
- [ ] Implement navigation (React Navigation)
- [ ] Implement authentication screens
- [ ] Implement job browsing
- [ ] Implement application submission
- [ ] Implement notifications (push)
- [ ] Implement messaging
- [ ] Build and publish to App Store / Play Store

#### Testing
- [ ] Test on iOS and Android
- [ ] Test offline functionality
- [ ] Test push notifications
- [ ] Test performance

---

## 💰 Phase 4: Scale & Monetization (Months 7-9)

**Goal**: Introduce premium tiers, integrations, and revenue generation.

### **4.1 Premium Subscriptions**

#### Backend Tasks
- [ ] **Subscription Model**
  - [ ] Create `subscriptions` table (user_id, plan_type (free/premium/enterprise), status, started_at, expires_at)
  - [ ] Create `subscription_plans` table (plan details, features, pricing)
  
- [ ] **Stripe Integration**
  - [ ] Setup Stripe account
  - [ ] Create products and prices in Stripe
  - [ ] POST `/api/subscriptions/checkout` - Create Stripe checkout session
  - [ ] Webhook handler for Stripe events (payment success, subscription cancelled)
  
- [ ] **Feature Gating**
  - [ ] Middleware to check subscription level
  - [ ] Rate limiting based on plan (e.g., free: 5 applications/week, premium: unlimited)

#### Frontend Tasks
- [ ] **Pricing Page**
  - [ ] Comparison table (Free, Premium Personal, Premium Company)
  - [ ] Feature list for each plan
  - [ ] Monthly/yearly toggle (show savings)
  - [ ] CTA buttons for each plan
  
- [ ] **Upgrade Modal**
  - [ ] Triggered when hitting plan limits
  - [ ] Show benefits of upgrading
  - [ ] Direct link to checkout
  
- [ ] **Billing Page**
  - [ ] Current plan display
  - [ ] Payment method management
  - [ ] Invoices history
  - [ ] Upgrade/downgrade options
  - [ ] Cancel subscription button

#### Testing
- [ ] Test Stripe checkout flow
- [ ] Test webhook handling
- [ ] Test feature gating
- [ ] Test plan upgrade/downgrade

---

### **4.2 ATS Integrations**

#### Backend Tasks
- [ ] **Integration Framework**
  - [ ] Create `integrations` table (user_id, provider (greenhouse/lever/workday), access_token, refresh_token, settings)
  
- [ ] **Greenhouse Integration**
  - [ ] OAuth flow for Greenhouse
  - [ ] POST `/api/integrations/greenhouse/sync` - Sync jobs from Greenhouse
  - [ ] POST `/api/integrations/greenhouse/push-candidate` - Push candidate to Greenhouse
  
- [ ] **Lever Integration**
  - [ ] Similar to Greenhouse
  
- [ ] **Zapier Integration**
  - [ ] Create Zapier app
  - [ ] Define triggers and actions

#### Frontend Tasks
- [ ] **Integrations Page**
  - [ ] List of available integrations
  - [ ] Each shows: logo, description, "Connect" button, status
  - [ ] Configuration page after connection (map fields)
  
- [ ] **Integration Settings**
  - [ ] Toggle auto-sync
  - [ ] Sync frequency selector
  - [ ] Disconnect button

#### Testing
- [ ] Test OAuth flows
- [ ] Test data syncing
- [ ] Test error handling (API rate limits, auth failures)

---

### **4.3 Video Introductions**

#### Backend Tasks
- [ ] **Video Model**
  - [ ] Create `profile_videos` table (user_id, video_url, thumbnail_url, duration_seconds)
  
- [ ] **Video Storage**
  - [ ] Setup video hosting (AWS S3 + CloudFront, or Vimeo)
  - [ ] POST `/api/users/me/video` - Upload video
  - [ ] Generate thumbnail automatically

#### Frontend Tasks
- [ ] **Video Recorder Component**
  - [ ] Use browser MediaRecorder API
  - [ ] 30-second limit
  - [ ] Preview before uploading
  - [ ] Retake option
  
- [ ] **Video Display**
  - [ ] Show on candidate profiles
  - [ ] Play inline (not autoplay)
  - [ ] Fallback to photo if no video

#### Testing
- [ ] Test video upload
- [ ] Test browser compatibility
- [ ] Test video playback
- [ ] Test file size limits

---

### **4.4 Live Chat with Recruiters**

#### Backend Tasks
- [ ] **Chat Enhancement**
  - [ ] Upgrade messaging to real-time (Socket.IO)
  - [ ] Add typing indicators
  - [ ] Add online/offline status
  
- [ ] **Chat Availability**
  - [ ] Recruiters set availability hours
  - [ ] Show "Available Now" badge

#### Frontend Tasks
- [ ] **Chat Widget**
  - [ ] Floating chat button (for job seekers)
  - [ ] Click to open chat window
  - [ ] List of available recruiters
  - [ ] Real-time message updates
  - [ ] Typing indicator ("User is typing...")
  
- [ ] **Chat Management (Company)**
  - [ ] Inbox with active chats
  - [ ] Assign chats to team members
  - [ ] Canned responses (quick replies)

#### Testing
- [ ] Test real-time messaging
- [ ] Test multiple concurrent chats
- [ ] Test notification on new message

---

## 🤖 Phase 5: Advanced AI (Months 10-12)

**Goal**: Leverage AI for predictive analytics, personalization, and automation.

### **5.1 Predictive Hiring Analytics**

#### Backend Tasks
- [ ] **ML Model Training**
  - [ ] Collect historical data (successful hires vs rejected)
  - [ ] Train model to predict hire probability
  - [ ] Features: match score, experience, education, assessment scores, time to apply
  
- [ ] **Prediction Endpoint**
  - [ ] POST `/api/analytics/predict-hire` - Predict if candidate will be hired

#### Frontend Tasks
- [ ] **Prediction Display**
  - [ ] Show "X% likely to be hired" on candidate cards
  - [ ] Explanation of factors

#### Testing
- [ ] Test prediction accuracy
- [ ] Test model retraining pipeline

---

### **5.2 Salary Negotiation Assistant**

#### Backend Tasks
- [ ] **Salary Data Collection**
  - [ ] Scrape or integrate with salary databases (Glassdoor, PayScale)
  - [ ] Store salary ranges by role, location, experience
  
- [ ] **Negotiation Recommendations**
  - [ ] POST `/api/salary/recommend` - Get salary negotiation tips
  - [ ] Analyze job offer details and provide counter-offer suggestions

#### Frontend Tasks
- [ ] **Salary Tool**
  - [ ] Input current offer
  - [ ] See market data
  - [ ] Get negotiation tips (e.g., "Ask for 10% more based on your experience")

#### Testing
- [ ] Test salary data accuracy
- [ ] Test recommendation quality

---

### **5.3 Interview Question Generator**

#### Backend Tasks
- [ ] **Question Generation**
  - [ ] Use GPT API to generate custom questions based on job role and skills
  - [ ] POST `/api/interviews/generate-questions` - Generate interview questions

#### Frontend Tasks
- [ ] **Question Generator (Company)**
  - [ ] Input job role and skills
  - [ ] Click "Generate Questions"
  - [ ] Display 10-15 questions
  - [ ] Save to interview template

#### Testing
- [ ] Test question relevance
- [ ] Test variety of questions

---

### **5.4 Culture Fit Assessment**

#### Backend Tasks
- [ ] **Culture Quiz**
  - [ ] Create personality/culture questions
  - [ ] Company defines their culture values
  - [ ] Match candidate responses to company culture
  
- [ ] **Culture Match Endpoint**
  - [ ] POST `/api/culture/match` - Calculate culture fit score

#### Frontend Tasks
- [ ] **Culture Quiz (Job Seeker)**
  - [ ] 10-15 questions about work style, values
  - [ ] Save results to profile
  
- [ ] **Culture Match Display**
  - [ ] Show on application (e.g., "85% culture fit")

#### Testing
- [ ] Test quiz logic
- [ ] Test matching algorithm

---

### **5.5 Diversity & Inclusion Insights**

#### Backend Tasks
- [ ] **Anonymize Candidate Data**
  - [ ] Option to hide name, age, gender during screening
  
- [ ] **Diversity Analytics**
  - [ ] Track diversity metrics (opt-in by candidates)
  - [ ] GET `/api/analytics/diversity` - Company-wide diversity stats

#### Frontend Tasks
- [ ] **Diversity Dashboard (Company)**
  - [ ] Charts showing gender, ethnicity, age distribution
  - [ ] Compare to industry benchmarks
  
- [ ] **Inclusive Job Posting**
  - [ ] Suggestions to make job posts more inclusive
  - [ ] Gender-neutral language checker

#### Testing
- [ ] Test anonymization
- [ ] Test privacy compliance
- [ ] Test analytics accuracy

---

### **5.6 Automated Reference Checking**

#### Backend Tasks
- [ ] **Reference Model**
  - [ ] Create `references` table (application_id, reference_name, email, relationship, status)
  
- [ ] **Reference Workflow**
  - [ ] POST `/api/applications/{id}/request-references` - Send email to references
  - [ ] References fill out form
  - [ ] Results sent to company

#### Frontend Tasks
- [ ] **Request References (Company)**
  - [ ] Select candidate
  - [ ] Input reference contact info
  - [ ] Send automated email
  
- [ ] **Reference Form (Public)**
  - [ ] Reference answers questions
  - [ ] Submit form

#### Testing
- [ ] Test email delivery
- [ ] Test form submission
- [ ] Test privacy (references only accessible to requester)

---

## 🛠️ Technical Debt & Refactoring

### **Code Quality**
- [ ] Setup ESLint and Prettier for frontend
- [ ] Setup Black and isort for backend
- [ ] Write comprehensive test suite (target 80% coverage)
- [ ] Setup CI/CD pipeline (GitHub Actions)
- [ ] Add pre-commit hooks (linting, type checking)

### **Performance**
- [ ] Implement caching (Redis for API responses)
- [ ] Optimize database queries (add indexes, use query profiling)
- [ ] Implement lazy loading for images
- [ ] Code splitting for frontend (route-based)
- [ ] Setup CDN for static assets

### **Security**
- [ ] Security audit (OWASP Top 10)
- [ ] Implement rate limiting on all endpoints
- [ ] Add CSRF protection
- [ ] Setup Content Security Policy (CSP)
- [ ] Implement API key rotation
- [ ] Add 2FA for user accounts
- [ ] Regular dependency updates (Dependabot)

### **Monitoring**
- [ ] Setup Sentry for error tracking
- [ ] Setup Prometheus for metrics
- [ ] Setup Grafana for dashboards
- [ ] Add logging (structured logs with ELK stack)
- [ ] Setup uptime monitoring (UptimeRobot)

### **Documentation**
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User documentation (help center)
- [ ] Developer documentation (setup, architecture)
- [ ] Video tutorials for key features

### **Deployment**
- [ ] Setup staging environment
- [ ] Setup production environment
- [ ] Implement blue-green deployment
- [ ] Setup automated backups (daily)
- [ ] Disaster recovery plan

---

## 🐛 Bug Tracker

| ID | Description | Priority | Status | Assigned To | Fixed In |
|----|-------------|----------|--------|-------------|----------|
| - | - | - | - | - | - |

**Priority Levels:**
- 🔴 Critical (Blocks functionality)
- 🟠 High (Major issue, workaround available)
- 🟡 Medium (Minor issue, no workaround)
- 🟢 Low (Enhancement, nice-to-have)

---

## 📝 Notes

- **Development Velocity**: Adjust timelines based on team size (above is for 2-3 developers)
- **MVP Focus**: Get Phase 1 to users ASAP, gather feedback, iterate
- **User Feedback**: Setup feedback widget in app (e.g., Canny, UserVoice)
- **Feature Flags**: Use feature flags to gradually roll out new features
- **A/B Testing**: Test different UI variations for key conversion points

---

**Last Updated**: January 07, 2026  
**Next Review**: End of Phase 1 (Month 2)
