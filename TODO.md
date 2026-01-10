# HireSight Development TODO

**Version**: 1.0  
**Last Updated**: January 2026  
**Status**: In Progress

---

## 🎯 Phase 1: MVP Foundation (Weeks 1-4)

### 1. Build Authentication System
- [ ] User registration with email verification
- [ ] Login/logout functionality
- [ ] Password reset via email
- [ ] Role-based access (Personal vs Company)
- [ ] Profile auto-creation on signup

### 2. Build Personal Profile Features
- [ ] Profile editing (name, headline, bio, avatar)
- [ ] Skills management (add/remove/edit)
- [ ] Experience timeline
- [ ] Education section
- [ ] Certifications & portfolio links
- [ ] Job preferences (salary, remote, availability)
- [ ] Privacy settings
- [ ] Profile completion progress

### 3. Build Company Profile Features
- [ ] Company info editing (name, logo, industry)
- [ ] Company description & mission
- [ ] Benefits listing
- [ ] Team photos gallery
- [ ] Multiple location support
- [ ] Company verification system

### 4. Build Resume Management
- [ ] Resume file upload (PDF/DOCX, max 5MB)
- [ ] Multiple resume versions per user
- [ ] Set primary resume
- [ ] Resume parsing with AI (extract text, skills, experience)
- [ ] Auto-fill profile from parsed resume
- [ ] Resume preview/download

### 5. Build Job Posting System
- [ ] Create job form (title, description, requirements)
- [ ] Job status management (draft/active/closed)
- [ ] Edit/duplicate/delete jobs
- [ ] Company-only access enforcement

### 6. Build Job Discovery (Personal)
- [ ] Browse all active jobs
- [ ] Search by keyword
- [ ] Filter by location, remote type, salary
- [ ] Filter by skills and experience
- [ ] Job detail page with company info
- [ ] Save jobs for later (bookmark)

### 7. Build Application System
- [ ] Apply to jobs with resume selection
- [ ] Optional cover letter
- [ ] Prevent duplicate applications
- [ ] Track application status (personal view)
- [ ] View all applicants per job (company view)
- [ ] Update application status (company)

### 8. Build AI Resume Screening
- [ ] Bulk resume upload (up to 50 per batch)
- [ ] Parse all resumes automatically
- [ ] Calculate match scores (0-100) using AI
- [ ] Generate match explanations (skills match, gaps)
- [ ] Rank candidates by score
- [ ] Display screening results with filters
- [ ] Export results to Excel/PDF

### 9. Build Dashboards
- [ ] Personal dashboard (applications, recommended jobs, saved jobs)
- [ ] Company dashboard (top candidates, active jobs, recent activity)
- [ ] Role-specific stats cards
- [ ] Recent activity feed
- [ ] Profile completion widget (personal only)
- [ ] Quick actions section

---

## 🚀 Phase 2: Core Engagement (Weeks 5-8)

### 10. Build Application Pipeline (Company)
- [ ] Kanban board view (New → Screening → Interview → Offer → Hired/Rejected)
- [ ] Drag-and-drop candidates between stages
- [ ] Filter by job and status
- [ ] Bulk actions (move multiple, send emails)
- [ ] Internal notes on candidates
- [ ] Status change notifications

### 11. Build Following System
- [ ] Follow companies (personal)
- [ ] Follow other job seekers (personal)
- [ ] View followers list (company)
- [ ] View following list (personal)
- [ ] Follow/unfollow buttons on profiles
- [ ] Notifications when someone follows

### 12. Build Notification System
- [ ] In-app notifications (bell icon)
- [ ] Email notifications (async with Celery)
- [ ] Notification types: application, message, follow, job, interview
- [ ] Mark as read/unread
- [ ] Mark all as read
- [ ] Delete notifications
- [ ] Real-time badge count

### 13. Build Messaging System
- [ ] In-app inbox
- [ ] Send message to users/companies
- [ ] Conversation threads
- [ ] Unread message count
- [ ] Mark messages as read
- [ ] Search conversations

### 14. Build Advanced Job Search
- [ ] Keyword search in title & description
- [ ] Multi-select filters (skills, remote type)
- [ ] Salary range slider
- [ ] Sort by relevance, date, salary
- [ ] Pagination (20 jobs per page)
- [ ] Save search criteria

### 15. Build Company Analytics
- [ ] Job metrics (views, applications per job)
- [ ] Application funnel visualization
- [ ] Average match score calculation
- [ ] Time-to-hire metrics
- [ ] Hiring trend charts
- [ ] Export analytics to CSV

---

## 🎨 Phase 3: User Engagement (Weeks 9-12)

### 16. Build Skill Assessments (Personal)
- [ ] Browse available skill tests
- [ ] Take timed assessments
- [ ] Multiple choice questions
- [ ] Score calculation
- [ ] Display completed assessments on profile
- [ ] Generate PDF certificates

### 17. Build Interview Scheduling
- [ ] Schedule interview form (company)
- [ ] Calendar integration
- [ ] Send interview invitations
- [ ] Interview reminders (24h, 1h before)
- [ ] Reschedule/cancel interviews
- [ ] View upcoming interviews (both roles)
- [ ] Mark interviews as completed

### 18. Build Company Branding Pages
- [ ] Public company profile page
- [ ] Team member showcase
- [ ] Office photos gallery
- [ ] Employee testimonials
- [ ] Open jobs section on company page
- [ ] Follow button for job seekers
- [ ] Company stats (followers, open jobs)

### 19. Build Resume Optimization Tips (Personal)
- [ ] Analyze resume with AI
- [ ] Check for action verbs
- [ ] Check for quantifiable achievements
- [ ] Calculate ATS-friendliness score
- [ ] Provide improvement suggestions
- [ ] Re-analyze after changes

### 20. Build Job Recommendations (Personal)
- [ ] AI-powered job matching
- [ ] Match based on skills, experience, preferences
- [ ] Display recommended jobs on dashboard
- [ ] "Why recommended?" explanations
- [ ] Thumbs up/down feedback
- [ ] Improve recommendations over time

### 21. Build Saved Jobs & Application Tracking
- [ ] Save/unsave jobs (bookmark)
- [ ] View all saved jobs
- [ ] Application status timeline
- [ ] Application success rate metrics
- [ ] Profile views tracking (who viewed profile)

---

## 💰 Phase 4: Monetization & Scale (Weeks 13-16)

### 22. Build Subscription System
- [ ] Define pricing tiers (Free, Premium Personal, Premium Company)
- [ ] Stripe integration for payments
- [ ] Subscription checkout flow
- [ ] Manage subscription (upgrade/downgrade/cancel)
- [ ] Feature gating based on plan
- [ ] Invoice history
- [ ] Payment method management

### 23. Build ATS Integrations
- [ ] Greenhouse OAuth integration
- [ ] Lever API integration
- [ ] Sync jobs from external ATS
- [ ] Push candidates to external ATS
- [ ] Field mapping configuration
- [ ] Zapier app creation

### 24. Build Video Introductions (Personal)
- [ ] Record 30-second video intro
- [ ] Upload video to storage
- [ ] Generate video thumbnail
- [ ] Display on profile
- [ ] Video playback in applicant view

### 25. Build Live Chat
- [ ] Real-time messaging with WebSockets
- [ ] Typing indicators
- [ ] Online/offline status
- [ ] Chat availability hours (company)
- [ ] Canned responses (quick replies)
- [ ] Chat assignment to team members

---

## 🤖 Phase 5: Advanced AI (Weeks 17-20)

### 26. Build Predictive Analytics
- [ ] Train ML model on historical hire data
- [ ] Predict hire probability for candidates
- [ ] Display prediction confidence
- [ ] Explain prediction factors

### 27. Build Salary Negotiation Assistant (Personal)
- [ ] Integrate salary database APIs
- [ ] Display market salary ranges
- [ ] Provide negotiation tips based on offer
- [ ] Counter-offer suggestions

### 28. Build Interview Question Generator (Company)
- [ ] Generate custom questions with GPT
- [ ] Based on job role and required skills
- [ ] Save questions to templates
- [ ] Question bank for reuse

### 29. Build Culture Fit Assessment
- [ ] Company defines culture values
- [ ] Candidates take culture quiz
- [ ] Calculate culture fit score
- [ ] Display on application

### 30. Build Diversity & Inclusion Tools
- [ ] Optional demographic data collection
- [ ] Diversity analytics dashboard (company)
- [ ] Anonymize candidate data during screening
- [ ] Inclusive language checker for job posts
- [ ] Compare to industry benchmarks

### 31. Build Automated Reference Checking
- [ ] Request references from candidates
- [ ] Send automated forms to references
- [ ] Collect reference responses
- [ ] Display aggregated feedback
- [ ] Privacy controls for references

---

## 🛠️ Technical Improvements (Ongoing)

### 32. Improve Performance
- [ ] Database query optimization (add indexes)
- [ ] Implement Redis caching for frequently accessed data
- [ ] Lazy loading for images
- [ ] Pagination for large lists
- [ ] CDN setup for static assets
- [ ] Database connection pooling

### 33. Improve Security
- [ ] Rate limiting on all endpoints (Django Ratelimit)
- [ ] CSRF protection (Django built-in)
- [ ] SQL injection prevention (ORM usage)
- [ ] XSS prevention (template escaping)
- [ ] File upload validation (size, type, scan)
- [ ] 2FA implementation
- [ ] Security headers (CSP, HSTS)

### 34. Improve Testing
- [ ] Unit tests for models
- [ ] Integration tests for views
- [ ] End-to-end tests for user flows
- [ ] 80% code coverage target
- [ ] Automated test runs (CI/CD)

### 35. Improve Monitoring
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] User analytics (Google Analytics)
- [ ] Uptime monitoring
- [ ] Log aggregation

### 36. Improve Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide & help center
- [ ] Video tutorials for key features
- [ ] Developer documentation
- [ ] Deployment guide

---

## 📱 Future Enhancements (Phase 6+)

### 37. Build Mobile App
- [ ] React Native or Flutter app
- [ ] iOS and Android versions
- [ ] Push notifications
- [ ] Offline mode for viewing saved data
- [ ] Mobile-optimized UI

### 38. Build Advanced Features
- [ ] Virtual career fairs
- [ ] Group video interviews
- [ ] Anonymous company Q&A
- [ ] Salary negotiation simulator
- [ ] Employee referral program
- [ ] Company review system (like Glassdoor)

---

## ✅ Completed Features

_(Move tasks here as they're completed)_

- [x] Project structure created
- [x] User models designed
- [x] README.md updated
- [x] TODO.md created

---

## 📝 Notes

- **Priority**: Focus on Phase 1 (MVP) first before moving to Phase 2
- **Feedback**: Gather user feedback after Phase 1 completion
- **Iteration**: Each phase should be tested and refined before moving forward
- **Documentation**: Document features as you build them
- **Git**: Commit frequently with clear messages

---

**Remember**: Build features incrementally, test thoroughly, and iterate based on user feedback! 🚀