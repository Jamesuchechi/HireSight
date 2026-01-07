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
- [ ] **User Model**
  - [ ] Create `users` table with `id`, `email`, `password_hash`, `account_type` (enum: personal/company), `is_verified`, `is_active`, `created_at`, `updated_at`
  - [ ] Add unique constraints on `email`
  - [ ] Create indexes on `email` and `account_type`
  
- [ ] **Authentication Service**
  - [ ] Implement password hashing with bcrypt (min 12 rounds)
  - [ ] Generate JWT tokens (access token: 15min, refresh token: 7 days)
  - [ ] Store refresh tokens in httpOnly cookies
  - [ ] Implement token refresh endpoint
  - [ ] Create middleware for protected routes
  - [ ] Add role-based access control (RBAC) decorator
  
- [ ] **Registration Flow**
  - [ ] POST `/api/auth/register` - Create new user with account type selection
  - [ ] Send verification email with token (expires in 24 hours)
  - [ ] POST `/api/auth/verify-email` - Verify email with token
  - [ ] Implement rate limiting (5 registration attempts per hour per IP)
  
- [ ] **Login/Logout**
  - [ ] POST `/api/auth/login` - Authenticate and return JWT
  - [ ] POST `/api/auth/logout` - Invalidate refresh token
  - [ ] GET `/api/auth/me` - Get current user info
  - [ ] Implement login attempt tracking (lock after 5 failed attempts for 30 minutes)
  
- [ ] **Password Reset**
  - [ ] POST `/api/auth/forgot-password` - Send reset email
  - [ ] POST `/api/auth/reset-password` - Reset with token
  - [ ] Tokens expire in 1 hour

#### Frontend Tasks
- [ ] **Landing Page**
  - [ ] Hero section with dual CTA (For Job Seekers / For Recruiters)
  - [ ] Features showcase
  - [ ] Testimonials section
  - [ ] Pricing preview
  - [ ] Footer with links
  
- [ ] **Authentication Modal**
  - [ ] Sign Up form with account type toggle (Personal / Company)
  - [ ] Sign In form
  - [ ] Form validation (email format, password strength)
  - [ ] Error handling with user-friendly messages
  - [ ] Loading states during API calls
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
- [ ] **Personal Profile Model**
  - [ ] Create `personal_profiles` table
  - [ ] Fields: `user_id` (FK), `full_name`, `headline`, `location`, `phone`, `bio`
  - [ ] JSONB fields: `skills` (array of objects), `experience` (array), `education` (array), `certifications` (array), `portfolio_links` (array)
  - [ ] Preferences: `preferred_job_types` (JSONB), `salary_expectation_min`, `salary_expectation_max`, `availability`
  - [ ] Privacy: `profile_visibility` (public/verified_companies/private)
  
- [ ] **Company Profile Model**
  - [ ] Create `company_profiles` table
  - [ ] Fields: `user_id` (FK), `company_name`, `logo_url`, `industry`, `company_size`
  - [ ] JSONB fields: `locations` (array), `benefits` (array), `team_photos` (array)
  - [ ] Details: `website`, `description`, `mission`, `culture`, `founded_year`
  - [ ] Verification: `verification_status` (unverified/pending/verified), `verification_docs_url`
  
- [ ] **Profile Endpoints**
  - [ ] GET `/api/users/me/profile` - Get own profile (role-based response)
  - [ ] PUT `/api/users/me/profile` - Update profile
  - [ ] POST `/api/users/me/avatar` - Upload profile picture (S3/Cloudinary)
  - [ ] GET `/api/users/{id}/profile` - Get public profile (with privacy checks)
  - [ ] GET `/api/companies` - List all verified companies (for job seekers)
  - [ ] GET `/api/companies/{id}` - Get company public page

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
- [ ] **Resume Model**
  - [ ] Create `resumes` table
  - [ ] Fields: `id`, `user_id` (FK), `filename`, `file_url`, `version_name`, `is_primary`, `uploaded_at`
  - [ ] `parsed_data` (JSONB): extracted name, email, phone, skills, experience, education
  - [ ] Add constraint: only one primary resume per user
  
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
  - [ ] POST `/api/resumes/upload` - Upload resume file (max 5MB, PDF/DOCX only)
  - [ ] POST `/api/resumes/parse` - Parse uploaded resume
  - [ ] GET `/api/resumes` - List user's resumes
  - [ ] GET `/api/resumes/{id}` - Get resume details (with parsed data)
  - [ ] PUT `/api/resumes/{id}` - Update resume metadata (version name, is_primary)
  - [ ] DELETE `/api/resumes/{id}` - Delete resume
  - [ ] POST `/api/resumes/{id}/set-primary` - Set as primary resume

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
- [ ] **Job Model**
  - [ ] Create `jobs` table
  - [ ] Fields: `id`, `company_id` (FK), `title`, `description`, `location`
  - [ ] Employment: `remote_type` (remote/hybrid/onsite), `employment_type` (full-time/part-time/contract/internship)
  - [ ] Compensation: `salary_min`, `salary_max`, `currency` (default USD)
  - [ ] JSONB fields: `requirements` (skills, experience, education), `screening_questions` (array of questions)
  - [ ] Status: `status` (draft/active/closed), `created_at`, `updated_at`, `expires_at` (optional)
  - [ ] Metrics: `view_count`, `application_count`
  
- [ ] **Job Endpoints (Company only)**
  - [ ] POST `/api/jobs` - Create new job
  - [ ] GET `/api/jobs` - List company's jobs (with filters)
  - [ ] GET `/api/jobs/{id}` - Get job details
  - [ ] PUT `/api/jobs/{id}` - Update job
  - [ ] DELETE `/api/jobs/{id}` - Delete job (soft delete)
  - [ ] POST `/api/jobs/{id}/close` - Close job to applications
  - [ ] POST `/api/jobs/{id}/duplicate` - Create copy of job
  
- [ ] **Job Search Endpoints (Personal only)**
  - [ ] GET `/api/jobs/search` - Search all active jobs
  - [ ] Query params: `q` (keyword), `location`, `remote_type`, `employment_type`, `salary_min`, `skills` (comma-separated), `page`, `limit`
  - [ ] GET `/api/jobs/{id}/similar` - Get similar jobs (based on skills)
  - [ ] POST `/api/jobs/{id}/view` - Track job view (increment view_count)

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
- [ ] **Application Model**
  - [ ] Create `applications` table
  - [ ] Fields: `id`, `job_id` (FK), `user_id` (FK), `resume_id` (FK), `cover_letter` (text)
  - [ ] Status: `status` (pending/screening/interview/offer/hired/rejected), `match_score`, `match_explanation` (JSONB)
  - [ ] Timestamps: `applied_at`, `updated_at`
  - [ ] Add unique constraint: (`job_id`, `user_id`) to prevent duplicate applications
  
- [ ] **Application Endpoints**
  - [ ] POST `/api/applications` - Apply for job (Job Seeker)
    - [ ] Body: `job_id`, `resume_id`, `cover_letter` (optional)
    - [ ] Auto-calculate match score on apply
  - [ ] GET `/api/applications` - List applications
    - [ ] For Job Seekers: their own applications (filter by status, job)
    - [ ] For Companies: applications for their jobs (filter by job, status)
  - [ ] GET `/api/applications/{id}` - Get application details
  - [ ] PUT `/api/applications/{id}/status` - Update status (Company only)
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


PROMPT

# COMPREHENSIVE PROMPT FOR AI AGENT: Build HireSight Dual-Sided Recruitment Platform

## PROJECT OVERVIEW

You are building **HireSight**, a production-ready, dual-sided recruitment platform that connects job seekers with companies through AI-powered resume screening. This is a FULL-STACK application with distinct user experiences for two account types:

1. **Personal (Job Seekers)** - Browse jobs, apply, track applications, manage resumes
2. **Company (Recruiters)** - Post jobs, screen resumes with AI, manage applicants, track hiring pipeline

**Critical Requirements:**
- Complete role-based access control (RBAC)
- Different dashboard UIs for each account type
- Different profile structures for each account type
- AI-powered semantic resume matching
- Real-time notifications and messaging
- Following system (job seekers follow companies/users)
- Application pipeline management (Kanban board)
- Mobile-responsive design
- Production-ready security and performance

---

## PART 1: AUTHENTICATION & USER MANAGEMENT

### 1.1 Database Schema - Users & Authentication

Create the following tables with proper foreign keys, indexes, and constraints:

#### **users** table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('personal', 'company')),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_account_type ON users(account_type);
```

#### **verification_tokens** table
```sql
CREATE TABLE verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **refresh_tokens** table
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 Backend - Authentication Endpoints

**Technology**: FastAPI (Python 3.10+), SQLAlchemy 2.0, JWT

Implement the following endpoints with proper validation, error handling, and security:

#### POST `/api/auth/register`
**Request Body:**
```json
{
  "name": "string",  // Only for personal accounts
  "company_name": "string",  // Only for company accounts
  "email": "string",
  "password": "string",  // Min 8 chars, 1 uppercase, 1 number, 1 special
  "account_type": "personal" | "company"
}
```

**Business Logic:**
1. Validate email format and check if already exists
2. Validate password strength (min 8 chars, 1 uppercase, 1 number, 1 special char)
3. Hash password with bcrypt (12 rounds)
4. Create user record with `is_verified=false`
5. Create corresponding profile (personal_profile or company_profile) with basic info
6. Generate verification token (UUID, expires in 24 hours)
7. Send verification email using background task (Celery)
8. Return success message (do NOT return JWT until email verified)

**Response (201):**
```json
{
  "message": "Registration successful. Please check your email to verify your account.",
  "email": "user@example.com"
}
```

#### POST `/api/auth/verify-email`
**Request Body:**
```json
{
  "token": "string"
}
```

**Business Logic:**
1. Find verification token in database
2. Check if token expired
3. Mark user as verified (`is_verified=true`)
4. Delete verification token
5. Return success message

#### POST `/api/auth/login`
**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Business Logic:**
1. Find user by email
2. Verify password hash
3. Check if email is verified (reject if not)
4. Check if account is active
5. Generate JWT access token (expires in 15 minutes)
6. Generate refresh token (expires in 7 days, store in database)
7. Set refresh token in httpOnly cookie
8. Track login attempt (for rate limiting)
9. Return access token and user info

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "account_type": "personal",
    "profile": {
      // Profile details based on account type
    }
  }
}
```

#### POST `/api/auth/refresh`
**Headers:** Cookie with refresh_token

**Business Logic:**
1. Extract refresh token from cookie
2. Validate token in database
3. Check if token expired
4. Generate new access token
5. Return new access token

#### POST `/api/auth/logout`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Verify access token
2. Delete refresh token from database
3. Clear refresh token cookie
4. Return success message

#### POST `/api/auth/forgot-password`
**Request Body:**
```json
{
  "email": "string"
}
```

**Business Logic:**
1. Find user by email
2. Generate password reset token (expires in 1 hour)
3. Send reset email with token
4. Return success message (always, even if email doesn't exist - security)

#### POST `/api/auth/reset-password`
**Request Body:**
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Business Logic:**
1. Validate token
2. Check expiration
3. Hash new password
4. Update user password
5. Delete reset token
6. Invalidate all refresh tokens (force re-login)
7. Return success message

#### GET `/api/auth/me`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "account_type": "personal",
  "is_verified": true,
  "created_at": "2026-01-01T00:00:00Z",
  "profile": {
    // Full profile based on account type
  }
}
```

### 1.3 Frontend - Authentication Components

**Technology**: React 18 + TypeScript + Vite, Tailwind CSS

#### **Landing Page** (`/`)
- Hero section with tagline and dual CTA buttons:
  - "For Job Seekers" → Opens signup modal with account_type="personal"
  - "For Recruiters" → Opens signup modal with account_type="company"
- Features section
- Testimonials
- Pricing preview
- Footer

#### **Authentication Modal Component**
Create a reusable modal with two tabs: "Sign In" and "Sign Up"

**Sign Up Tab:**
- Toggle: "Personal Account" / "Company Account" (visually distinct)
- Conditional fields based on toggle:
  - Personal: Name, Email, Password
  - Company: Company Name, Email, Password
- Password strength indicator (visual bar: weak/medium/strong)
- Form validation (real-time)
- Submit button with loading state
- Success state: "Check your email to verify"

**Sign In Tab:**
- Email and Password fields
- "Forgot Password?" link
- Submit button with loading state
- Error handling (display user-friendly messages)

#### **Email Verification Page** (`/verify-email?token=...`)
- Show loading spinner while verifying
- Success: "Email verified! Redirecting to dashboard..."
- Error: "Invalid or expired token. Request a new verification email."
- Auto-redirect to dashboard on success (after 2 seconds)

#### **Forgot Password Flow**
1. **Forgot Password Modal:**
   - Email input
   - Submit button
   - Success: "Check your email for reset instructions"

2. **Reset Password Page** (`/reset-password?token=...`)
   - New password input with strength indicator
   - Confirm password input
   - Submit button
   - Success: "Password reset! Please log in."

### 1.4 Security Implementation

**Password Hashing:**
```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

**JWT Implementation:**
```python
from datetime import datetime, timedelta
import jwt

SECRET_KEY = "your-secret-key"  # From environment variable
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

**Rate Limiting:**
- Registration: 5 attempts per hour per IP
- Login: 5 failed attempts → lock for 30 minutes
- Password reset: 3 requests per hour per email

**Middleware for Protected Routes:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Fetch user from database
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Role-Based Access Control (RBAC):**
```python
def require_account_type(account_type: str):
    def decorator(func):
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            if current_user.account_type != account_type:
                raise HTTPException(status_code=403, detail="Access forbidden")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage:
@router.post("/jobs")
@require_account_type("company")
async def create_job(job: JobCreate, current_user = Depends(get_current_user)):
    # Only companies can access this
    pass
```

---

## PART 2: USER PROFILES (PERSONAL & COMPANY)

### 2.1 Database Schema - Profiles

#### **personal_profiles** table
```sql
CREATE TABLE personal_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    headline VARCHAR(255),  -- e.g., "Senior React Developer"
    avatar_url VARCHAR(512),
    location VARCHAR(255),
    phone VARCHAR(50),
    bio TEXT,
    skills JSONB DEFAULT '[]',  -- [{skill: "React", proficiency: "expert"}]
    experience JSONB DEFAULT '[]',  -- [{company, role, start_date, end_date, description}]
    education JSONB DEFAULT '[]',  -- [{institution, degree, field, start_date, end_date}]
    certifications JSONB DEFAULT '[]',  -- [{name, issuer, date, credential_url}]
    portfolio_links JSONB DEFAULT '[]',  -- [{type: "github", url}]
    preferred_job_types JSONB DEFAULT '[]',  -- ["full-time", "remote"]
    salary_expectation_min INTEGER,
    salary_expectation_max INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    availability VARCHAR(50),  -- "immediate", "2 weeks", "1 month"
    profile_visibility VARCHAR(50) DEFAULT 'public',  -- 'public', 'verified_companies', 'private'
    resume_primary_id UUID REFERENCES resumes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_personal_profiles_user_id ON personal_profiles(user_id);
```

#### **company_profiles** table
```sql
CREATE TABLE company_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    logo_url VARCHAR(512),
    industry VARCHAR(100),
    company_size VARCHAR(50),  -- "1-10", "11-50", "51-200", etc.
    locations JSONB DEFAULT '[]',  -- [{city, state, country, is_hq}]
    website VARCHAR(512),
    description TEXT,
    mission TEXT,
    culture TEXT,
    benefits JSONB DEFAULT '[]',  -- ["Health Insurance", "Remote Work", "401k"]
    team_photos JSONB DEFAULT '[]',  -- [{url, caption}]
    founded_year INTEGER,
    verification_status VARCHAR(50) DEFAULT 'unverified',  -- 'unverified', 'pending', 'verified'
    verification_docs_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_company_profiles_user_id ON company_profiles(user_id);
CREATE INDEX idx_company_profiles_verification ON company_profiles(verification_status);
```

### 2.2 Backend - Profile Endpoints

#### GET `/api/users/me/profile`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Get current user from token
2. Based on account_type, fetch personal_profile or company_profile
3. Return profile data

**Response for Personal (200):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "full_name": "John Doe",
  "headline": "Senior Full Stack Developer",
  "avatar_url": "https://...",
  "location": "San Francisco, CA",
  "phone": "+1234567890",
  "bio": "Passionate developer with 5 years of experience...",
  "skills": [
    {"skill": "React", "proficiency": "expert"},
    {"skill": "Node.js", "proficiency": "advanced"}
  ],
  "experience": [
    {
      "company": "Tech Corp",
      "role": "Senior Developer",
      "start_date": "2020-01-01",
      "end_date": "2024-12-31",
      "description": "Led team of 5 developers..."
    }
  ],
  "education": [...],
  "certifications": [...],
  "portfolio_links": [
    {"type": "github", "url": "https://github.com/johndoe"}
  ],
  "preferred_job_types": ["full-time", "remote"],
  "salary_expectation_min": 100000,
  "salary_expectation_max": 150000,
  "availability": "2 weeks",
  "profile_visibility": "public"
}
```

**Response for Company (200):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "company_name": "Tech Corp Inc",
  "logo_url": "https://...",
  "industry": "Technology",
  "company_size": "51-200",
  "locations": [
    {"city": "San Francisco", "state": "CA", "country": "USA", "is_hq": true}
  ],
  "website": "https://techcorp.com",
  "description": "We build innovative solutions...",
  "mission": "To revolutionize...",
  "culture": "Fast-paced, collaborative...",
  "benefits": ["Health Insurance", "401k", "Remote Work"],
  "team_photos": [{"url": "https://...", "caption": "Our amazing team"}],
  "founded_year": 2015,
  "verification_status": "verified"
}
```

#### PUT `/api/users/me/profile`
**Headers:** Authorization: Bearer {access_token}

**Request Body:** Partial update (send only fields to update)

**Business Logic:**
1. Validate input data
2. Update only provided fields
3. Set updated_at timestamp
4. Return updated profile

#### POST `/api/users/me/avatar`
**Headers:** Authorization: Bearer {access_token}, Content-Type: multipart/form-data

**Request Body:** FormData with `file` field

**Business Logic:**
1. Validate file type (JPEG, PNG, max 5MB)
2. Resize image to 400x400 (maintain aspect ratio)
3. Upload to cloud storage (AWS S3 or Cloudinary)
4. Update avatar_url in profile
5. Return new avatar URL

**Response (200):**
```json
{
  "avatar_url": "https://..."
}
```

#### GET `/api/users/{user_id}/profile`
**Query Params:** None required

**Business Logic:**
1. Fetch user by ID
2. Check profile visibility:
   - If public → return profile
   - If verified_companies → only allow company accounts to view
   - If private → only allow owner to view
3. Return public-safe profile (hide sensitive data like phone, email)

#### GET `/api/companies`
**Query Params:** `industry`, `size`, `page`, `limit`

**Business Logic:**
1. Fetch all company profiles where verification_status = 'verified'
2. Apply filters
3. Return paginated results

**Response (200):**
```json
{
  "companies": [
    {
      "id": "uuid",
      "company_name": "Tech Corp",
      "logo_url": "https://...",
      "industry": "Technology",
      "company_size": "51-200",
      "location": "San Francisco, CA",
      "follower_count": 1234,
      "open_jobs_count": 5
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

#### GET `/api/companies/{company_id}`
**Response (200):** Full company public profile with open jobs

### 2.3 Frontend - Profile Pages

#### **Personal Profile Page** (`/profile`)
**Sections:**
1. **Header:**
   - Avatar (editable)
   - Name (editable inline or in edit mode)
   - Headline (editable)
   - Location (editable)
   - Profile completion progress bar (0-100%)

2. **About Section:**
   - Bio (editable textarea, rich text)
   - Contact info (phone, email - with visibility toggle)

3. **Skills Section:**
   - Display as tags with proficiency levels (color-coded)
   - Add/remove skills
   - Autocomplete from skill taxonomy

4. **Experience Section:**
   - Timeline view (vertical with company logos if available)
   - Each entry: Company, Role, Dates, Description
   - Add/edit/delete buttons

5. **Education Section:**
   - List of degrees
   - Each entry: Institution, Degree, Field, Dates

6. **Certifications:**
   - List with badges
   - Each entry: Name, Issuer, Date, Link

7. **Portfolio:**
   - Links to GitHub, LinkedIn, personal website
   - Preview GitHub repos (if GitHub linked)

8. **Preferences:**
   - Job types (checkboxes)
   - Salary range (slider)
   - Availability (dropdown)
   - Privacy settings

**Edit Mode:**
- Toggle between "View" and "Edit" mode
- Save button (API call to PUT /api/users/me/profile)
- Cancel button (revert changes)

#### **Company Profile Page** (`/company/{id}`)
**For Own Company (Edit Mode):**
- Logo upload
- Company name, industry, size
- Locations (add/remove with map integration)
- Description, mission, culture (rich text editors)
- Benefits (tags, add/remove)
- Team photos (drag-and-drop upload gallery)
- Verification status display

**For Public View:**
- Hero section with logo and name
- About, mission, culture sections
- Benefits display (icon + text)
- Team photos gallery
- Office locations (map)
- Open jobs section (cards)
- Follower count
- "Follow" button (if logged in as personal)

---

## PART 3: RESUME MANAGEMENT & PARSING

### 3.1 Database Schema - Resumes

#### **resumes** table
```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(512) NOT NULL,
    file_size INTEGER,  -- in bytes
    version_name VARCHAR(255) DEFAULT 'Main Resume',
    is_primary BOOLEAN DEFAULT FALSE,
    parsed_data JSONB DEFAULT '{}',  -- extracted data
    raw_text TEXT,  -- full text extracted
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE UNIQUE INDEX idx_resumes_primary_per_user ON resumes(user_id) WHERE is_primary = TRUE;
```

### 3.2 Backend - Resume Parsing Service

**Install Dependencies:**
```bash
pip install pyresparser pymupdf python-docx spacy
python -m spacy download en_core_web_sm
```

**Resume Parser Implementation:**
```python
import PyPDF2
from docx import Document
import spacy
import re
from typing import Dict, List

nlp = spacy.load("en_core_web_sm")

class ResumeParser:
    def __init__(self):
        self.nlp = nlp
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        return "\\n".join([para.text for para in doc.paragraphs])
    
    def extract_email(self, text: str) -> str:
        """Extract email using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else None
    
    def extract_name(self, text: str) -> str:
        """Extract name using spaCy NER"""
        doc = self.nlp(text[:500])  # First 500 chars likely contain name
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills by matching against skill taxonomy"""
        # Load skill taxonomy (predefined list)
        skill_taxonomy = [
            "Python", "JavaScript", "React", "Node.js", "SQL", "AWS",
            "Docker", "Kubernetes", "Git", "Agile", "Scrum", "Java",
            "C++", "TypeScript", "MongoDB", "PostgreSQL", "Redis",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision"
            # ... add more
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in skill_taxonomy:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience (simplified)"""
        # This is a simplified version - use more advanced NER or regex for production
        doc = self.nlp(text)
        experiences = []
        
        # Look for organization names and dates
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Try to find associated dates nearby
                experiences.append({
                    "company": ent.text,
                    "role": "Unknown",  # More complex extraction needed
                    "start_date": None,
                    "end_date": None,
                    "description": ""
                })
        
        return experiences
    
    def parse(self, file_path: str, file_type: str) -> Dict:
        """Main parsing function"""
        # Extract text
        if file_type == "pdf":
            text = self.extract_text_from_pdf(file_path)
        elif file_type == "docx":
            text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file type")
        
        # Extract structured data
        parsed_data = {
            "name": self.extract_name(text),
            "email": self.extract_email(text),
            "phone": self.extract_phone(text),
            "skills": self.extract_skills(text),
            "experience": self.extract_experience(text),
            "education": [],  # Implement similar to experience
            "raw_text": text
        }
        
        return parsed_data
```

### 3.3 Backend - Resume Endpoints

#### POST `/api/resumes/upload`
**Headers:** Authorization: Bearer {access_token}, Content-Type: multipart/form-data

**Request Body:** FormData with `file` and optional `version_name`

**Business Logic:**
1. Validate file (PDF or DOCX, max 5MB)
2. Upload to cloud storage (S3/Cloudinary)
3. Parse resume using ResumeParser
4. Create resume record in database
5. If this is user's first resume, set as primary
6. Return resume data with parsed info

**Response (201):**
```json
{
  "id": "uuid",
  "filename": "resume.pdf",
  "file_url": "https://...",
  "version_name": "Main Resume",
  "is_primary": true,
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "skills": ["React", "Node.js", "Python"],
    "experience": [...]
  },
  "uploaded_at": "2026-01-01T00:00:00Z"
}
```

#### GET `/api/resumes`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "resumes": [
    {
      "id": "uuid",
      "filename": "resume.pdf",
      "file_url": "https://...",
      "version_name": "Main Resume",
      "is_primary": true,
      "file_size": 102400,
      "uploaded_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

#### GET `/api/resumes/{id}`
**Headers:** Authorization: Bearer {access_token}

**Response (200):** Full resume data including parsed_data

#### PUT `/api/resumes/{id}`
**Headers:** Authorization: Bearer {access_token}

**Request Body:**
```json
{
  "version_name": "Updated Resume - 2026"
}
```

#### POST `/api/resumes/{id}/set-primary`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Set all user's resumes to is_primary=false
2. Set this resume to is_primary=true
3. Update personal_profile.resume_primary_id

#### DELETE `/api/resumes/{id}`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Check ownership
2. Delete file from storage
3. Delete database record
4. If this was primary, set another resume as primary (if any exist)

### 3.4 Frontend - Resume Components

#### **Resume Upload Component**
- Drag-and-drop zone
- File picker button
- File type validation (show error if not PDF/DOCX)
- File size validation (show error if >5MB)
- Upload progress bar
- Success message with "Auto-fill Profile" option

#### **Resume List View**
- Card view of all resumes
- Each card shows:
  - Filename
  - Version name (editable inline)
  - File size
  - Upload date
  - "Primary" badge if is_primary
  - Actions dropdown: Download, Set as Primary, Delete, Preview

#### **Resume Preview Modal**
- Embedded PDF viewer or DOCX renderer
- Close button

#### **Auto-Fill Profile Dialog**
- Shows after parsing complete
- Display parsed data in editable form
- Checkboxes for each section: Skills, Experience, Education
- "Fill Profile" button (calls PUT /api/users/me/profile with parsed data)

---

## PART 4: JOB POSTING & BROWSING

### 4.1 Database Schema - Jobs

#### **jobs** table
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements JSONB DEFAULT '{}',  -- {skills: [], experience_min: int, education: []}
    location VARCHAR(255),
    remote_type VARCHAR(50) DEFAULT 'onsite',  -- 'remote', 'hybrid', 'onsite'
    employment_type VARCHAR(50) DEFAULT 'full-time',  -- 'full-time', 'part-time', 'contract', 'internship'
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    screening_questions JSONB DEFAULT '[]',  -- [{question: "...", required: bool}]
    status VARCHAR(50) DEFAULT 'draft',  -- 'draft', 'active', 'closed'
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_jobs_company_id ON jobs(company_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
```

### 4.2 Backend - Job Endpoints (Company Only)

#### POST `/api/jobs`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Request Body:**
```json
{
  "title": "Senior Full Stack Developer",
  "description": "<p>We are looking for...</p>",
  "requirements": {
    "skills": ["React", "Node.js", "PostgreSQL"],
    "experience_min": 5,
    "education": ["Bachelor's degree in Computer Science"]
  },
  "location": "San Francisco, CA",
  "remote_type": "hybrid",
  "employment_type": "full-time",
  "salary_min": 120000,
  "salary_max": 180000,
  "screening_questions": [
    {"question": "Why do you want to work here?", "required": true}
  ],
  "status": "active"
}
```

**Business Logic:**
1. Validate company_id matches current user
2. Create job record
3. If status='active', set expires_at to 30 days from now (default)
4. Return created job

#### GET `/api/jobs`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Query Params:** `status`, `page`, `limit`, `sort`

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "uuid",
      "title": "Senior Full Stack Developer",
      "location": "San Francisco, CA",
      "remote_type": "hybrid",
      "status": "active",
      "view_count": 342,
      "application_count": 28,
      "created_at": "2026-01-01T00:00:00Z",
      "expires_at": "2026-01-31T00:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20
}
```

#### GET `/api/jobs/{id}`
**Response (200):** Full job details

#### PUT `/api/jobs/{id}`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company', ownership check

**Request Body:** Partial update (same structure as POST)

#### DELETE `/api/jobs/{id}`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company', ownership check

**Business Logic:**
1. Soft delete (set status='closed' or add deleted_at timestamp)
2. Do NOT actually delete record (preserve application history)

#### POST `/api/jobs/{id}/duplicate`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Copy job with all fields
2. Set status='draft'
3. Set title to "{original_title} (Copy)"
4. Reset view_count and application_count

### 4.3 Backend - Job Search Endpoints (Personal Only)

#### GET `/api/jobs/search`
**Requires:** account_type = 'personal' OR public access (not logged in)

**Query Params:**
- `q` (keyword search in title + description)
- `location` (city or state)
- `remote_type` (remote, hybrid, onsite)
- `employment_type` (full-time, part-time, etc.)
- `salary_min` (filter by minimum salary)
- `skills` (comma-separated list)
- `page`, `limit`
- `sort` (relevance, date, salary)

**Business Logic:**
1. Query jobs where status='active' AND expires_at > now()
2. Apply filters
3. If `q` provided, search in title and description (full-text search)
4. If `skills` provided, match against requirements.skills
5. Sort by relevance (if keyword search) or date
6. Return paginated results

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "uuid",
      "title": "Senior Full Stack Developer",
      "company": {
        "id": "uuid",
        "name": "Tech Corp",
        "logo_url": "https://..."
      },
      "location": "San Francisco, CA",
      "remote_type": "hybrid",
      "employment_type": "full-time",
      "salary_min": 120000,
      "salary_max": 180000,
      "requirements": {
        "skills": ["React", "Node.js"],
        "experience_min": 5
      },
      "posted_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 342,
  "page": 1,
  "limit": 20
}
```

#### POST `/api/jobs/{id}/view`
**Business Logic:**
1. Increment job.view_count
2. Track view in analytics (optional: store user_id, timestamp)

### 4.4 Frontend - Job Management (Company)

#### **Job Posting Form** (`/jobs/new` or `/jobs/{id}/edit`)
**Sections:**
1. Basic Info: Title, Location
2. Job Details: Remote type (radio), Employment type (dropdown)
3. Description: Rich text editor (Quill or TipTap)
4. Requirements:
   - Skills (multi-select with autocomplete)
   - Min experience (slider or input)
   - Education (multi-select)
5. Compensation: Salary range (two inputs or range slider)
6. Screening Questions:
   - Add question button
   - Each question: text input + "Required" checkbox + delete button
7. Actions:
   - Save as Draft button
   - Publish button (sets status='active')
   - Cancel button

#### **Job List Page** (`/jobs`)
**Filters:** Status tabs (All, Draft, Active, Closed)

**Job Cards:**
- Title, location, remote type
- View count, application count
- Posted date, expires date
- Actions dropdown: Edit, Duplicate, View Analytics, Close, Delete

#### **Job Detail Page** (`/jobs/{id}`)
**Sections:**
1. Header: Title, company, location, salary
2. Description (rendered HTML)
3. Requirements list
4. Application button (for job seekers) or Applications list (for company)
5. Similar jobs section

### 4.5 Frontend - Job Search (Personal)

#### **Job Search Page** (`/jobs`)
**Layout:** Sidebar filters + Main results area

**Filters Sidebar:**
- Keyword search input
- Location input (with autocomplete)
- Remote type checkboxes
- Employment type checkboxes
- Salary range slider
- Skills multi-select

**Results Area:**
- Sort dropdown (Relevance, Date, Salary)
- Results count
- Job cards (grid or list view toggle)
- Pagination or infinite scroll

**Job Card:**
- Company logo
- Job title
- Company name
- Location + remote badge
- Salary range
- Key skills (first 3)
- Posted date
- Save button (bookmark)
- Apply button

#### **Job Detail Page** (`/jobs/{id}`)
**For Job Seekers:**
- Full job details
- Company info (with link to company page)
- Apply button (opens application modal)
- Save button
- Share button (copy link, social media)
- "X people applied" (social proof)
- Related jobs section (similar based on skills)

---

## PART 5: AI-POWERED RESUME SCREENING

### 5.1 Setup ML Pipeline

**Install Dependencies:**
```bash
pip install sentence-transformers scikit-learn
```

**Embedding Model:**
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings

def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for text"""
    return model.encode(text, convert_to_tensor=False)

def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings"""
    similarity = cosine_similarity([embedding1], [embedding2])[0][0]
    return float(similarity)
```

### 5.2 Screening Service

```python
class ResumeScreeningService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def calculate_match_score(self, job_requirements: dict, resume_data: dict) -> dict:
        """Calculate comprehensive match score"""
        
        # 1. Skills Match (40% weight)
        job_skills = set([s.lower() for s in job_requirements.get('skills', [])])
        resume_skills = set([s.lower() for s in resume_data.get('skills', [])])
        skills_match = len(job_skills.intersection(resume_skills)) / len(job_skills) if job_skills else 0
        
        # 2. Experience Match (30% weight)
        required_experience = job_requirements.get('experience_min', 0)
        candidate_experience = self.calculate_total_experience(resume_data.get('experience', []))
        experience_match = min(candidate_experience / required_experience, 1.0) if required_experience > 0 else 1.0
        
        # 3. Semantic Match (30% weight)
        job_description = job_requirements.get('description', '')
        resume_text = resume_data.get('raw_text', '')
        job_embedding = self.model.encode(job_description)
        resume_embedding = self.model.encode(resume_text)
        semantic_match = cosine_similarity([job_embedding], [resume_embedding])[0][0]
        
        # Weighted score
        final_score = (
            skills_match * 0.4 +
            experience_match * 0.3 +
            semantic_match * 0.3
        ) * 100
        
        # Generate explanation
        matched_skills = list(job_skills.intersection(resume_skills))
        missing_skills = list(job_skills - resume_skills)
        
        explanation = {
            "score": round(final_score, 2),
            "skills_match": {
                "score": round(skills_match * 100, 2),
                "matched": matched_skills,
                "missing": missing_skills
            },
            "experience_match": {
                "score": round(experience_match * 100, 2),
                "required": required_experience,
                "actual": candidate_experience
            },
            "semantic_match": {
                "score": round(semantic_match * 100, 2)
            }
        }
        
        return explanation
    
    def calculate_total_experience(self, experience_list: list) -> int:
        """Calculate total years of experience"""
        # Simplified - in production, parse dates properly
        return len(experience_list)
```

### 5.3 Backend - Screening Endpoints (Company Only)

#### POST `/api/screening/bulk-upload`
**Headers:** Authorization: Bearer {access_token}, Content-Type: multipart/form-data
**Requires:** account_type = 'company'

**Request Body:** FormData with multiple `files[]` and `job_id`

**Business Logic:**
1. Validate job_id belongs to company
2. Upload all files (max 50 per batch)
3. Queue parsing job (Celery task)
4. Return batch ID for polling

**Response (202 Accepted):**
```json
{
  "batch_id": "uuid",
  "total_files": 45,
  "status": "processing"
}
```

#### POST `/api/screening/process`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Request Body:**
```json
{
  "job_id": "uuid",
  "resume_ids": ["uuid1", "uuid2", ...]  // From bulk upload or existing
}
```

**Business Logic:**
1. Fetch job requirements
2. For each resume:
   - Fetch parsed data
   - Calculate match score using screening service
   - Create application record with match_score and match_explanation
3. Return ranked candidates

**Response (200):**
```json
{
  "candidates": [
    {
      "resume_id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "match_score": 94,
      "explanation": {
        "skills_match": {"score": 95, "matched": ["React", "Node.js"], "missing": ["AWS"]},
        "experience_match": {"score": 100, "required": 5, "actual": 6},
        "semantic_match": {"score": 88}
      }
    }
  ]
}
```

#### GET `/api/screening/results/{job_id}`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company', ownership check

**Query Params:** `min_score`, `sort` (score, date)

**Response (200):** List of candidates ranked by match score

#### POST `/api/screening/export`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Request Body:**
```json
{
  "job_id": "uuid",
  "format": "excel" | "pdf",
  "include_top_n": 10
}
```

**Business Logic:**
1. Fetch top N candidates for job
2. Generate Excel or PDF report
3. Return download URL

**Response (200):**
```json
{
  "download_url": "https://..."
}
```

### 5.4 Frontend - Screening Interface (Company)

#### **Bulk Resume Upload Page** (`/screening/upload`)
**Components:**
1. Job selector dropdown (which job to screen for)
2. Multi-file drag-and-drop zone
3. File list with status (pending, processing, completed, error)
4. "Process Resumes" button (calls POST /api/screening/process)
5. Progress indicator during processing

#### **Screening Results Page** (`/screening/results/{job_id}`)
**Layout:**
- Header: Job title, total candidates, avg match score
- Filter: Min score slider (show only candidates above X score)
- Sort: Dropdown (score high-to-low, date)

**Candidate Cards:**
- Name, contact info
- Match score (large, color-coded: 90+ green, 75-89 blue, 60-74 orange, <60 red)
- Top 3 matching skills (green badges)
- Missing skills (red badges)
- Experience (e.g., "5 years | Required: 3")
- Actions: View Resume, View Full Profile, Contact, Move to Pipeline, Reject

**Match Explanation Modal:**
- Opens on click of match score
- Breakdown:
  - Skills Match: 95/100 (show matched and missing)
  - Experience Match: 100/100 (show required vs actual)
  - Semantic Match: 88/100 (brief explanation)
- Visual: Radar chart or bar chart

#### **Export Report Dialog**
- Format selector: Excel or PDF
- "Top N candidates" input (default 10)
- Export button
- Download link after generation

---

## PART 6: APPLICATION SYSTEM

### 6.1 Database Schema - Applications

#### **applications** table
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id),
    cover_letter TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'screening', 'interview', 'offer', 'hired', 'rejected'
    match_score DECIMAL(5,2),
    match_explanation JSONB DEFAULT '{}',
    rejection_reason TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, user_id)  -- Prevent duplicate applications
);

CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
```

### 6.2 Backend - Application Endpoints

#### POST `/api/applications`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'personal'

**Request Body:**
```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "cover_letter": "I am excited to apply..."
}
```

**Business Logic:**
1. Check if user already applied to this job (unique constraint)
2. Validate resume belongs to user
3. Fetch job requirements and resume parsed_data
4. Calculate match score using screening service
5. Create application with status='pending'
6. Increment job.application_count
7. Create notification for company
8. Send confirmation email to user
9. Return application

**Response (201):**
```json
{
  "id": "uuid",
  "job": {
    "id": "uuid",
    "title": "Senior Developer",
    "company": "Tech Corp"
  },
  "match_score": 87,
  "status": "pending",
  "applied_at": "2026-01-01T00:00:00Z"
}
```

#### GET `/api/applications`
**Headers:** Authorization: Bearer {access_token}

**For Personal:**
- Query Params: `status`, `page`, `limit`
- Returns: User's own applications

**For Company:**
- Query Params: `job_id`, `status`, `page`, `limit`
- Returns: Applications for company's jobs

**Response (200):**
```json
{
  "applications": [...],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

#### GET `/api/applications/{id}`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Check ownership (user is applicant OR company owns job)
2. Return full application details

#### PUT `/api/applications/{id}/status`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company', ownership check

**Request Body:**
```json
{
  "status": "interview",
  "rejection_reason": "Not enough experience" // Optional, only if status='rejected'
}
```

**Business Logic:**
1. Update application status
2. Set updated_at
3. Create notification for applicant
4. Send email to applicant
5. Return updated application

#### DELETE `/api/applications/{id}`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'personal', ownership check, status='pending'

**Business Logic:**
1. Delete application
2. Decrement job.application_count
3. Notify company (optional)

### 6.3 Frontend - Application Flow

#### **Application Modal (Job Seeker)**
**Triggered by:** "Apply" button on job detail page

**Form Fields:**
1. Resume selector: Dropdown of user's resumes (shows is_primary)
2. Cover letter: Textarea (optional, rich text)
3. Screening questions (if job has them): Display questions, user answers
4. Preview button: Show summary before submit

**Actions:**
- Submit button (loading state)
- Cancel button

**After Submit:**
- Success animation (checkmark)
- "Application submitted! Application #12345"
- "Track your application in My Applications"
- Auto-close after 3 seconds

#### **My Applications Page** (`/applications`)
**For Job Seekers:**

**Filters:**
- Status tabs: All, Pending, Interview, Offer, Rejected
- Search by job title or company

**Application Cards:**
- Job title, company name, location
- Applied date
- Status badge (color-coded)
- Match score (if available)
- Actions: View Job, View Application, Withdraw (if pending)

**Empty State:**
- "No applications yet"
- "Browse Jobs" button

#### **Application Detail Page** (`/applications/{id}`)
**For Job Seekers:**
- Job details (title, company, description)
- Your resume (embedded viewer)
- Your cover letter
- Match score breakdown (if shared by company)
- Status timeline (pending → screening → interview → offer)
- Current status with date
- Next steps (e.g., "The company is reviewing your application")

**For Company (Same page, different view):**
- Candidate info (name, headline, contact)
- Resume viewer
- Cover letter
- Match score breakdown (detailed)
- Answers to screening questions
- Action buttons: Update Status, Schedule Interview, Send Message, Reject
- Internal notes section (only visible to company)

---

## PART 7: APPLICATION PIPELINE (KANBAN)

### 7.1 Backend - Pipeline Endpoints

#### GET `/api/applications/pipeline/{job_id}`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company', ownership check

**Response (200):**
```json
{
  "job_id": "uuid",
  "pipeline": {
    "pending": [
      {
        "id": "uuid",
        "candidate": {...},
        "match_score": 87,
        "applied_at": "..."
      }
    ],
    "screening": [...],
    "interview": [...],
    "offer": [...],
    "hired": [...],
    "rejected": [...]
  }
}
```

#### PUT `/api/applications/{id}/move`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Request Body:**
```json
{
  "status": "interview"
}
```

**Business Logic:**
1. Validate status transition (e.g., can't go from pending to hired directly)
2. Update application status
3. Create notification for candidate
4. Return updated application

#### POST `/api/applications/{id}/note`
**Headers:** Authorization: Bearer {access_token}
**Requires:** account_type = 'company'

**Request Body:**
```json
{
  "note": "Great communication skills. Recommended for next round."
}
```

**Business Logic:**
1. Add note to internal notes array (JSONB field or separate table)
2. Include author and timestamp

### 7.2 Frontend - Kanban Board (Company)

#### **Pipeline Page** (`/jobs/{id}/pipeline`)
**Layout:** 6 columns (Pending, Screening, Interview, Offer, Hired, Rejected)

**Each Column:**
- Header: Stage name + count
- Scrollable list of candidate cards
- "Add Candidate" button (for manually adding from screening results)

**Candidate Card (Draggable):**
- Avatar or initials
- Name
- Match score (small badge)
- Applied date
- Drag handle icon

**Interactions:**
- Drag card to different column → Calls PUT /api/applications/{id}/move
- Click card → Opens application detail modal
- Bulk actions: Select multiple cards → Move all to stage

**Filters:**
- Min match score slider
- Search by name

---

## PART 8: FOLLOWING SYSTEM

### 8.1 Database Schema - Follows

#### **follows** table
```sql
CREATE TABLE follows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_type VARCHAR(50) NOT NULL,  -- 'user' or 'company'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (follower_id, following_id, following_type)
);

CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);
```

### 8.2 Backend - Follow Endpoints

#### POST `/api/follow/{user_id}`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Check if already following (unique constraint)
2. Create follow record
3. Determine following_type (check target user's account_type)
4. Create notification for followed user/company
5. Return success

#### DELETE `/api/follow/{user_id}`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Delete follow record
2. Return success

#### GET `/api/follow/followers`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "followers": [
    {
      "id": "uuid",
      "name": "John Doe",
      "avatar_url": "https://...",
      "headline": "Senior Developer",
      "followed_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

#### GET `/api/follow/following`
**Headers:** Authorization: Bearer {access_token}

**Response (200):** Similar to followers

#### GET `/api/follow/suggestions`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. For Personal: Suggest companies in their industry, companies with matching job types
2. For Company: Not applicable (companies don't follow)
3. Return list of suggested users/companies to follow

### 8.3 Frontend - Follow Components

#### **Follow Button Component**
**Props:** `userId`, `userType` (user/company)

**Display:**
- "Follow" button (if not following)
- "Following" button with checkmark (if following)
- Click to toggle follow/unfollow
- Loading state during API call

**Placement:**
- On company profile pages
- On user profile pages
- On job cards (follow company from job listing)

#### **Followers/Following Page** (`/profile/followers` or `/profile/following`)
**Tabs:** Followers | Following

**List View:**
- Avatar, name, headline
- Unfollow button (on Following tab)
- Link to profile

---

## PART 9: NOTIFICATIONS & MESSAGING

### 9.1 Database Schema - Notifications

#### **notifications** table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'application', 'message', 'job', 'follow', 'interview'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(512),  -- URL to relevant page
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

### 9.2 Backend - Notification Service

**Create Notification Function:**
```python
def create_notification(user_id: str, type: str, title: str, message: str, link: str = None):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link
    )
    db.add(notification)
    db.commit()
    
    # Emit real-time notification via Socket.IO
    socketio.emit('notification', {
        'id': str(notification.id),
        'title': title,
        'message': message,
        'link': link
    }, room=user_id)
    
    # Send email notification (background task)
    send_email_notification.delay(user_id, title, message, link)
```

**Trigger Notifications:**
- Application status change → Notify candidate
- New application received → Notify company
- New job from followed company → Notify followers
- Someone followed you → Notify user/company
- New message received → Notify recipient

### 9.3 Backend - Notification Endpoints

#### GET `/api/notifications`
**Headers:** Authorization: Bearer {access_token}

**Query Params:** `is_read`, `type`, `page`, `limit`

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "application",
      "title": "Application Status Update",
      "message": "Your application for Senior Developer has been moved to Interview stage.",
      "link": "/applications/uuid",
      "is_read": false,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "unread_count": 5
}
```

#### PUT `/api/notifications/{id}/read`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Mark notification as read
2. Return success

#### PUT `/api/notifications/read-all`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Mark all user's notifications as read
2. Return success

### 9.4 Frontend - Notification Components

#### **Notification Bell Icon** (in Header)
- Bell icon with unread count badge
- Click to open dropdown
- Dropdown shows last 5 notifications
- "View All" link at bottom

#### **Notifications Page** (`/notifications`)
- List of all notifications (paginated)
- Filter by type (All, Applications, Messages, Jobs, Follows)
- Group by date (Today, Yesterday, This Week, Older)
- Click notification → Navigate to link + mark as read
- "Mark all as read" button

#### **Real-Time Updates** (Socket.IO)
- Connect to Socket.IO on app load
- Listen for 'notification' events
- Show toast notification for new events
- Update unread count badge
- Add new notification to list (if on notifications page)

---

## PART 10: MESSAGING SYSTEM

### 10.1 Database Schema - Messages

#### **conversations** table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    participant_1_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    participant_2_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (participant_1_id, participant_2_id)
);

CREATE INDEX idx_conversations_participant1 ON conversations(participant_1_id);
CREATE INDEX idx_conversations_participant2 ON conversations(participant_2_id);
```

#### **messages** table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
```

### 10.2 Backend - Messaging Endpoints

#### POST `/api/messages`
**Headers:** Authorization: Bearer {access_token}

**Request Body:**
```json
{
  "receiver_id": "uuid",
  "body": "Hello, I'm interested in the position..."
}
```

**Business Logic:**
1. Find or create conversation between sender and receiver
2. Create message record
3. Update conversation.last_message_at
4. Create notification for receiver
5. Emit Socket.IO event to receiver
6. Return message

#### GET `/api/messages`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "other_user": {
        "id": "uuid",
        "name": "Tech Corp",
        "avatar_url": "https://..."
      },
      "last_message": {
        "body": "Thank you for applying...",
        "sent_at": "2026-01-01T12:00:00Z",
        "is_read": false
      },
      "unread_count": 2
    }
  ]
}
```

#### GET `/api/messages/{conversation_id}`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "body": "Hello!",
      "sent_at": "2026-01-01T10:00:00Z",
      "is_read": true
    }
  ]
}
```

#### PUT `/api/messages/{id}/read`
**Headers:** Authorization: Bearer {access_token}

**Business Logic:**
1. Mark message as read
2. Return success

### 10.3 Frontend - Messaging Components

#### **Inbox Page** (`/messages`)
**Layout:** Left sidebar (conversations) + Right (message thread)

**Conversations List:**
- Search conversations input
- List of conversations sorted by last_message_at
- Each item: Avatar, name, last message preview, time, unread badge

**Message Thread:**
- Header: Other user's name, avatar, link to profile
- Messages (chat-style bubbles)
- Message composer at bottom (textarea + send button)
- Real-time updates (new messages appear instantly)

#### **Compose Message Modal**
**Triggered by:** "Message" button on profiles, application pages

**Form:**
- Recipient (auto-filled, read-only)
- Message body (textarea)
- Send button

---

## PART 11: DASHBOARD IMPLEMENTATION

### 11.1 Backend - Dashboard Stats Endpoints

#### GET `/api/dashboard/stats`
**Headers:** Authorization: Bearer {access_token}

**For Personal:**
```json
{
  "total_applications": 15,
  "pending_count": 5,
  "interview_count": 3,
  "offer_count": 1,
  "rejected_count": 6,
  "profile_completion": 85,
  "profile_views": 127,
  "recommended_jobs_count": 8
}
```

**For Company:**
```json
{
  "active_jobs": 5,
  "total_applications": 142,
  "avg_match_score": 78,
  "time_saved_hours": 48,
  "new_applications_today": 12,
  "interviews_scheduled": 8
}
```

#### GET `/api/dashboard/recent-activity`
**Headers:** Authorization: Bearer {access_token}

**Response (200):**
```json
{
  "activities": [
    {
      "id": "uuid",
      "type": "application",
      "message": "Your application for Senior Developer was moved to Interview stage",
      "time": "5 mins ago",
      "link": "/applications/uuid"
    }
  ]
}
```

### 11.2 Frontend - Dashboard Pages

#### **Personal Dashboard** (`/dashboard`)
**Sections:**
1. **Stats Cards:** (4 cards in row)
   - Total Applications
   - Pending Reviews
   - Scheduled Interviews
   - Success Rate

2. **Application Status Chart:**
   - Pie chart showing distribution (Pending, Interview, Offer, Rejected)

3. **Recent Applications:**
   - List of last 5 applications with status
   - "View All" link

4. **Recommended Jobs:**
   - Carousel or grid of 4-6 job cards
   - "See More" link

5. **Profile Completion Widget:**
   - Progress bar (0-100%)
   - Checklist of missing items
   - "Complete Profile" button

6. **Quick Actions:**
   - Upload Resume
   - Browse Jobs
   - Update Profile

#### **Company Dashboard** (`/dashboard`)
**Sections:**
1. **Stats Cards:** (4 cards in row)
   - Active Jobs
   - Total Applications
   - Avg Match Score
   - Time Saved

2. **Active Jobs List:**
   - Cards showing each active job
   - Metrics per job: Views, Applications, Fill rate
   - "View Pipeline" button

3. **Recent Applications:**
   - List of last 10 applications across all jobs
   - Quick actions: View, Move Stage, Reject

4. **Top Matching Candidates:**
   - List of highest-scoring candidates across all jobs
   - "View All Candidates" link

5. **Quick Actions:**
   - Post New Job
   - Screen Resumes
   - View Analytics

---

## PART 12: TECHNICAL REQUIREMENTS

### 12.1 Environment Setup

**Backend `.env`:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/hiresight
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SENDGRID_API_KEY=your-sendgrid-key
EMAIL_FROM=noreply@hiresight.com

# Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=hiresight-files
AWS_REGION=us-east-1

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

**Frontend `.env`:**
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_SOCKET_URL=http://localhost:8000
```

### 12.2 CORS Configuration

**Backend (FastAPI):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 12.3 Error Handling

**Backend:**
```python
from fastapi import HTTPException

# Standard error responses
class ErrorResponse:
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}

# Usage
if not user:
    raise HTTPException(status_code=404, detail="User not found")
```

**Frontend:**
```typescript
// API client with error handling
async function apiCall(endpoint: string, options: RequestInit) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'An error occurred');
    }
    
    return await response.json();
  } catch (error) {
    // Show toast notification
    showErrorToast(error.message);
    throw error;
  }
}
```

### 12.4 Testing Requirements

**Backend Tests (pytest):**
- Unit tests for all services (auth, parsing, screening)
- Integration tests for API endpoints
- Test coverage target: 80%

**Frontend Tests (Vitest + React Testing Library):**
- Component tests for key components
- Integration tests for user flows (signup, login, apply)

### 12.5 Performance Requirements

- API response time: < 200ms (p95)
- Resume parsing: < 5 seconds per resume
- Bulk screening: 50 resumes in < 30 seconds
- Page load time: < 2 seconds
- Database queries: < 100ms (add indexes as needed)

---

## PART 13: DEPLOYMENT CHECKLIST

### 13.1 Security Hardening

- [ ] Use environment variables for secrets (never commit to Git)
- [ ] Enable HTTPS only
- [ ] Set secure httpOnly cookies for refresh tokens
- [ ] Implement rate limiting on all endpoints
- [ ] Add CSRF protection
- [ ] Set Content Security Policy headers
- [ ] Regular dependency updates
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize user inputs)

### 13.2 Production Database

- [ ] Create database backups (daily)
- [ ] Setup read replicas (if needed)
- [ ] Add indexes on frequently queried columns
- [ ] Monitor query performance
- [ ] Setup database connection pooling

### 13.3 Monitoring & Logging

- [ ] Setup Sentry for error tracking
- [ ] Setup application logs (structured JSON logs)
- [ ] Setup uptime monitoring
- [ ] Setup performance monitoring (response times, error rates)

---

## CRITICAL SUCCESS CRITERIA

Your implementation will be considered successful when:

1. ✅ Users can register as Personal or Company with email verification
2. ✅ Personal users can create profile, upload resume, browse jobs, apply
3. ✅ Company users can create profile, post jobs, upload resumes for screening
4. ✅ AI screening accurately ranks candidates (match score 0-100)
5. ✅ Both dashboards render correctly with role-specific content
6. ✅ Application pipeline (Kanban) works with drag-and-drop
7. ✅ Following system works (personal follows companies)
8. ✅ Notifications and messaging work in real-time
9. ✅ All forms validate properly with user-friendly error messages
10. ✅ Mobile responsive (test on phone)
11. ✅ No security vulnerabilities (SQL injection, XSS, CSRF)
12. ✅ Performance meets requirements (see 12.5)

---

## DEVELOPMENT ORDER (RECOMMENDED)

**Week 1-2:** Authentication, User Management, Profiles  
**Week 3-4:** Resume Management, Parsing, Job Posting  
**Week 5-6:** AI Screening, Application System  
**Week 7-8:** Pipeline, Notifications, Messaging, Following  
**Week 9-10:** Dashboards, Polish, Testing  
**Week 11-12:** Deployment, Bug Fixes, Performance Optimization  

---

## FINAL NOTES

- **Prioritize MVP:** Get core features working before adding nice-to-haves
- **Test incrementally:** Don't wait until the end to test
- **Use Git properly:** Commit often, use branches for features
- **Document as you go:** README, API docs, code comments
- **Ask questions:** If any requirement is unclear, ask for clarification
- **Show progress:** Regular demos to stakeholders

**Good luck building HireSight! 🚀**