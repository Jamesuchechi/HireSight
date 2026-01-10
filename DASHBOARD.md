# HireSight Dashboard Features Guide

**Last Updated**: January 2026

---

## 🎯 Overview

HireSight has **two distinct dashboards** based on user account type:
1. **Personal Dashboard** - For job seekers
2. **Company Dashboard** - For recruiters

---

## 👤 Personal Dashboard (Job Seekers)

### **What to Display:**

#### 1. **Header Section**
- Welcome message: "Welcome back, [FirstName]!"
- Subtitle: "Your job search activity at a glance"

#### 2. **Stats Cards (4 cards in a row)**
```
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  Total Applications │ │   Pending Reviews   │ │   Interviews        │ │   Success Rate      │
│        15           │ │         5           │ │        3            │ │       67%           │
│  📤 Send icon       │ │  ⏰ Clock icon      │ │  📅 Calendar icon  │ │  📈 Chart icon      │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

#### 3. **Profile Completion Widget** (Only show if <100%)
```
┌────────────────────────────────────────────────┐
│  Complete Your Profile                    75%  │
│  ████████████████████░░░░░░░░                  │
│                                                │
│  [Complete Profile Button]                     │
└────────────────────────────────────────────────┘
```

#### 4. **My Applications** (Large section)
Show recent 5 applications with:
- Company logo
- Job title
- Company name
- Location
- Applied date (e.g., "2 days ago")
- Status badge (Pending/Screening/Interview/Offer/Hired/Rejected)
- Match score (if available)
- Click to view details

**Empty State**: 
- Icon: 📤
- Text: "No applications yet"
- Subtitle: "Start applying to jobs to track your applications here"
- Button: "Browse Jobs"

#### 5. **Recommended Jobs** (Side section)
Show top 3 AI-recommended jobs with:
- Company logo
- Job title
- Company name
- Top 3 matching skills (as tags)
- Match score (color-coded: 90+ green, 75+ blue, 60+ orange, <60 red)
- Click to view job details

#### 6. **Saved Jobs** (Side section)
Show top 3 bookmarked jobs with:
- Company logo
- Job title
- Company name & location
- Date saved
- Bookmark icon
- "View All" link if more than 3

#### 7. **Upcoming Interviews** (Side section)
Show next 3 scheduled interviews with:
- Job title & company name
- Date & time
- Duration (e.g., "60 mins")
- Location or meeting link
- Calendar icon

#### 8. **Recent Activity** (Side section)
Show last 4 activities with:
- Icon based on type (📤 application, 💬 message, 👤 follow, 📅 interview)
- Activity message (e.g., "Applied to Senior Developer at TechCorp")
- Time ago (e.g., "2 hours ago")

---

## 🏢 Company Dashboard (Recruiters)

### **What to Display:**

#### 1. **Header Section**
- Welcome message: "Welcome back, [CompanyName]!"
- Subtitle: "Here's your recruitment overview"

#### 2. **Stats Cards (4 cards in a row)**
```
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│   Active Jobs       │ │  Total Applications │ │  Avg Match Score    │ │   Time Saved        │
│         5           │ │        142          │ │        78           │ │      48h            │
│  💼 Briefcase icon  │ │  👥 Users icon      │ │  🎯 Target icon     │ │  ⚡ Zap icon        │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

#### 3. **Top Matching Candidates** (Large section)
Show top 5 highest-scoring candidates across all jobs with:
- Avatar or initials
- Candidate name
- Role/headline (e.g., "Senior Full Stack Developer")
- Top 3 skills (as tags)
- Match score (large, color-coded)
- Status badge (if applicable)
- Action buttons: 👁️ View Profile, 💬 Message, 📥 Download Resume

**Empty State**:
- Icon: 👥
- Text: "No candidates yet"
- Subtitle: "Upload resumes or wait for applications to start screening candidates"
- Button: "Upload Resumes"

#### 4. **Active Job Postings** (Side section)
Show top 4 active jobs with:
- Job title
- Location (or "Remote")
- Posted date (e.g., "Posted 5 days ago")
- Status badge (Active/Draft/Closed)
- Briefcase icon
- "Manage Jobs" link

#### 5. **Upcoming Interviews** (Side section)
Show next 3 scheduled interviews with:
- Candidate name
- Job title
- Date & time
- Duration (e.g., "45 mins")
- Location or meeting link
- Calendar icon

#### 6. **Recent Activity** (Side section)
Show last 4 activities with:
- Icon based on type (📤 upload, 🎯 match, 📄 report, ✅ update, 📨 application)
- Activity message (e.g., "New application for Senior React Developer")
- Time ago (e.g., "1 hour ago")

---

## 🎨 Design Guidelines

### **Colors for Status Badges:**
- **Pending**: Gold background (#FFB800), gold text
- **Screening**: Cyan background (#00D4FF), cyan text
- **Interview**: Blue background (#0066FF), blue text
- **Offer**: Purple background (#9333EA), purple text
- **Hired**: Green background (#00C853), green text
- **Rejected**: Red background (#FF3B30), red text

### **Colors for Match Scores:**
- **90-100 (Excellent)**: Green (#00C853)
- **75-89 (Good)**: Blue (#0066FF)
- **60-74 (Average)**: Orange (#FF9500)
- **0-59 (Poor)**: Red (#FF3B30)

### **Card Styles:**
- White background
- Rounded corners (16px)
- 1px border (gray-200)
- Hover: Lift 4px + subtle shadow
- Padding: 1.5rem

### **Typography:**
- **Page Title**: Clash Display font, 2rem, bold
- **Section Titles**: Clash Display font, 1.25rem, semi-bold
- **Card Text**: Sora font, 0.9-1rem, regular
- **Stats**: Clash Display font, 2rem, bold

---

## 📊 Data to Fetch from Backend

### **Personal Dashboard:**
```python
# In dashboard view
context = {
    'stats': [
        {'label': 'Total Applications', 'value': 15, 'icon': 'send', 'color': 'blue'},
        {'label': 'Pending Reviews', 'value': 5, 'icon': 'clock', 'color': 'gold'},
        {'label': 'Interviews', 'value': 3, 'icon': 'calendar', 'color': 'cyan'},
        {'label': 'Success Rate', 'value': '67%', 'icon': 'trending-up', 'color': 'green'},
    ],
    'applications': Application.objects.filter(user=request.user).order_by('-applied_at')[:5],
    'saved_jobs': request.user.saved_jobs.all()[:3],
    'recommended_jobs': get_recommended_jobs(request.user)[:3],
    'upcoming_interviews': Interview.objects.filter(user=request.user, scheduled_at__gte=timezone.now()).order_by('scheduled_at')[:3],
    'profile_completion_score': request.user.personal_profile.calculate_completion_score(),
    'following_count': request.user.following.count(),
    'activities': get_recent_activities(request.user, limit=4),
}
```

### **Company Dashboard:**
```python
# In dashboard view
context = {
    'stats': [
        {'label': 'Active Jobs', 'value': 5, 'icon': 'briefcase', 'color': 'blue'},
        {'label': 'Total Applications', 'value': 142, 'icon': 'users', 'color': 'cyan'},
        {'label': 'Avg Match Score', 'value': 78, 'icon': 'target', 'color': 'gold'},
        {'label': 'Time Saved', 'value': '48h', 'icon': 'zap', 'color': 'green'},
    ],
    'candidates': get_top_candidates(request.user.company_profile, limit=5),
    'active_jobs': Job.objects.filter(company=request.user, status='active')[:4],
    'upcoming_interviews': Interview.objects.filter(company=request.user, scheduled_at__gte=timezone.now()).order_by('scheduled_at')[:3],
    'activities': get_recent_activities(request.user, limit=4),
}
```

---

## 🔀 Navigation Menu (Sidebar)

### **Personal (Job Seeker):**
```
Main
├── Overview (🏠)
├── Job Discovery (🔍)
├── My Applications (📄) [Badge: count]
└── Saved Jobs (🔖) [Badge: count]

Profile
├── Resume Manager (📤)
├── Skill Assessments (🏆)
└── My Profile (⚙️)

Engagement
├── My Interviews (📅) [Badge: count]
├── Messages (💬)
└── Following (👥) [Badge: count]
```

### **Company (Recruiter):**
```
Main
├── Overview (🏠)
├── Job Manager (💼) [Badge: active count]
├── All Candidates (👥) [Badge: total count]
├── Hiring Pipeline (🎯)
└── Resume Screening (📤)

Engagement
├── Interviews (📅) [Badge: upcoming count]
├── Messages (💬)
└── Followers (👤)

Insights
├── Analytics (📊)
└── Reports (📄)

System
└── Company Profile (⚙️)
```

---

## 🎯 Key Differences Summary

| Feature | Personal Dashboard | Company Dashboard |
|---------|-------------------|-------------------|
| **Primary Focus** | My applications & job search | Top candidates & hiring metrics |
| **Stats Shown** | Applications, interviews, success rate | Jobs, applications, match scores, time saved |
| **Main Section** | My Applications (recent 5) | Top Matching Candidates (top 5) |
| **Side Sections** | Recommended Jobs, Saved Jobs, Interviews | Active Jobs, Scheduled Interviews |
| **Special Widget** | Profile Completion (if <100%) | None |
| **Action Button** | "Browse Jobs" | "Post Job" |
| **Empty State CTA** | "Browse Jobs" | "Upload Resumes" |

---

## 📝 Implementation Notes

1. **Use Django template system** to render HTML
2. **Use Tailwind CSS** for styling (utility classes)
3. **Use Alpine.js** for simple interactions (dropdowns, modals)
4. **Use HTMX** for dynamic updates without page reload
5. **Responsive design**: Stack cards on mobile, grid on desktop
6. **Loading states**: Show skeleton loaders while fetching data
7. **Empty states**: Always provide helpful messages and CTAs
8. **Error handling**: Graceful error messages if data fetch fails

---

**Remember**: The dashboard should feel fast, clean, and informative at a glance! 🚀