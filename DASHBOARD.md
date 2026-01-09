# HireSight Dashboard - Role-Based Features Summary

**Last Updated**: January 2026

---

## 🎯 **Overview**

The HireSight Dashboard now has **distinct user experiences** for two account types:
1. **Personal (Job Seekers)** - Browse jobs, apply, track applications, manage resumes
2. **Company (Recruiters)** - Post jobs, screen candidates, manage pipeline, track hiring metrics

---

## 📊 **Navigation Structure**

### **Personal (Job Seeker) Navigation**

```
Main
├── Overview (Home)
├── Job Discovery (Search jobs)
├── My Applications (Track status) [Badge: application count]
└── Saved Jobs (Bookmarked jobs) [Badge: saved count]

Profile
├── Resume Manager (Upload & manage resumes)
├── Skill Assessments (Take tests to verify skills)
└── My Profile (Edit profile, settings)

Engagement
├── My Interviews (Scheduled interviews) [Badge: upcoming count]
├── Messages (Chat with recruiters)
└── Following (Companies & users) [Badge: following count]
```

### **Company (Recruiter) Navigation**

```
Main
├── Overview (Home)
├── Job Manager (Create/edit jobs) [Badge: active jobs]
├── All Candidates (View all applicants) [Badge: total candidates]
├── Hiring Pipeline (Kanban board for stages)
└── Resume Screening (Bulk upload & AI screening)

Engagement
├── Interviews (Schedule & manage) [Badge: upcoming count]
├── Messages (Chat with candidates)
└── Followers (Who follows your company)

Insights
├── Analytics (Charts, metrics, KPIs)
└── Reports (Export data, generate reports)

System
└── Company Profile (Edit company info, branding)
```

---

## 🎨 **Dashboard Views**

### **Personal Dashboard Overview**

#### **Stats Cards (Top Row)**
```typescript
[
  { label: "Total Applications", value: "15", icon: Send, color: "blue" },
  { label: "Pending Reviews", value: "5", icon: Clock, color: "gold" },
  { label: "Interviews Scheduled", value: "3", icon: Calendar, color: "cyan" },
  { label: "Success Rate", value: "67%", icon: TrendingUp, color: "green", change: "+12%", trend: "up" }
]
```

#### **Main Content Sections**

1. **Profile Completion Widget** (if <100%)
   - Progress bar showing completion percentage
   - "Complete Profile" CTA button
   - Gradient background (blue to cyan)

2. **My Applications** (Wide Card)
   - List of recent applications (up to 5)
   - Each shows:
     - Company logo
     - Job title & company name
     - Application date & location
     - Status badge (color-coded)
     - Match score (if available)
   - "View All" link if more than 5
   - Empty state: "No applications yet" + "Browse Jobs" button

3. **Recommended Jobs** (Side Card)
   - AI-powered job recommendations (top 3)
   - Shows:
     - Company logo
     - Job title & company name
     - Top 3 matching skills
     - Match score
   - Only visible if recommendations exist

4. **Saved Jobs** (Side Card)
   - Bookmarked jobs (top 3)
   - Shows:
     - Company logo
     - Job title, company, location
     - Date saved
     - Bookmark icon
   - "View All" link

5. **Upcoming Interviews** (Side Card)
   - Next 3 scheduled interviews
   - Shows:
     - Job title & company
     - Date/time & duration
     - Location or meeting link
   - Only visible if interviews scheduled

6. **Recent Activity** (Side Card)
   - Last 4 activities
   - Types: application, message, follow, interview
   - Shows: icon, message, timestamp
   - Empty state: "No recent activity"

---

### **Company Dashboard Overview**

#### **Stats Cards (Top Row)**
```typescript
[
  { label: "Active Jobs", value: "5", icon: Briefcase, color: "blue" },
  { label: "Total Applications", value: "142", icon: Users, color: "cyan" },
  { label: "Avg Match Score", value: "78", icon: Target, color: "gold" },
  { label: "Time Saved", value: "48h", icon: Zap, color: "green", change: "+22%", trend: "up" }
]
```

#### **Main Content Sections**

1. **Top Matching Candidates** (Wide Card)
   - Highest-scoring candidates across all jobs (top 5)
   - Each shows:
     - Avatar or initials
     - Name & role
     - Top 3 skills
     - Match score (color-coded: green 90+, blue 75+, orange 60+, red <60)
     - Status badge (if applicable)
     - Actions: View Profile, Message, Download Resume
   - "View All" link
   - Empty state: "No candidates yet" + "Upload Resumes" button

2. **Active Job Postings** (Side Card)
   - List of active jobs (top 4)
   - Shows:
     - Job title
     - Location (or "Remote")
     - Posted date
     - Status badge
   - "Manage Jobs" link

3. **Upcoming Interviews** (Side Card)
   - Next 3 scheduled interviews
   - Shows:
     - Candidate name
     - Job title
     - Date/time & duration
   - Only visible if interviews scheduled

4. **Recent Activity** (Side Card)
   - Last 4 activities
   - Types: upload, match, report, update, application
   - Shows: icon, message, timestamp
   - Empty state: "No recent activity"

---

## 🔧 **Component Props Interface**

```typescript
type DashboardProps = {
  user: AuthUser & { avatar?: string };
  
  // Common (Both Roles)
  stats?: Stat[];
  activities?: Activity[];
  quickActions?: QuickAction[];
  
  // Personal (Job Seeker) Only
  applications?: Application[];
  savedJobs?: SavedJob[];
  recommendedJobs?: RecommendedJob[];
  upcomingInterviews?: Interview[];
  profileCompletionScore?: number;
  followingCompanies?: number;
  
  // Company (Recruiter) Only
  candidates?: Candidate[];
  activeJobs?: number;
  scheduledInterviews?: Interview[];
  
  // Handlers
  onSignOut: () => void;
  onNavigate?: (route: string) => void;
  isLoading?: boolean;
};
```

---

## 📝 **Type Definitions**

### **Application** (Personal)
```typescript
type Application = {
  id: string | number;
  job_title: string;
  company_name: string;
  company_logo?: string;
  status: 'pending' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected';
  applied_date: string;
  match_score?: number;
  location?: string;
};
```

### **Saved Job** (Personal)
```typescript
type SavedJob = {
  id: string | number;
  title: string;
  company_name: string;
  company_logo?: string;
  location: string;
  remote_type: 'remote' | 'hybrid' | 'onsite';
  salary_min?: number;
  salary_max?: number;
  saved_date: string;
};
```

### **Recommended Job** (Personal)
```typescript
type RecommendedJob = {
  id: string | number;
  title: string;
  company_name: string;
  company_logo?: string;
  location: string;
  match_score: number;
  skills_match: string[];  // Top matching skills
  posted_date: string;
};
```

### **Candidate** (Company)
```typescript
type Candidate = {
  id: string | number;
  name: string;
  role: string;
  score: number;  // Match score 0-100
  skills: string[];
  avatar?: string;
  applied_date?: string;
  status?: 'pending' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected';
};
```

### **Interview** (Both)
```typescript
type Interview = {
  id: string | number;
  job_title?: string;          // For personal accounts
  candidate_name?: string;     // For company accounts
  company_name?: string;       // For personal accounts
  scheduled_at: string;
  duration_minutes: number;
  location?: string;
  meeting_link?: string;
  status: 'scheduled' | 'completed' | 'cancelled';
};
```

---

## 🎯 **Usage Examples**

### **Personal Dashboard Example**

```typescript
<Dashboard
  user={{
    id: "user-123",
    email: "john@example.com",
    account_type: "personal",
    full_name: "John Doe",
    avatar: "https://..."
  }}
  stats={[
    { label: "Total Applications", value: "15", icon: Send, color: "blue" },
    { label: "Pending", value: "5", icon: Clock, color: "gold" },
    { label: "Interviews", value: "3", icon: Calendar, color: "cyan" },
    { label: "Success Rate", value: "67%", icon: TrendingUp, color: "green" }
  ]}
  applications={[
    {
      id: "app-1",
      job_title: "Senior React Developer",
      company_name: "TechCorp",
      status: "interview",
      applied_date: "2026-01-05T10:00:00Z",
      match_score: 92,
      location: "San Francisco, CA"
    }
  ]}
  savedJobs={[
    {
      id: "job-1",
      title: "Full Stack Engineer",
      company_name: "StartupXYZ",
      location: "Remote",
      remote_type: "remote",
      saved_date: "2026-01-07T14:30:00Z"
    }
  ]}
  recommendedJobs={[
    {
      id: "job-2",
      title: "Frontend Developer",
      company_name: "DesignCo",
      location: "New York, NY",
      match_score: 88,
      skills_match: ["React", "TypeScript", "Tailwind CSS"],
      posted_date: "2026-01-08T09:00:00Z"
    }
  ]}
  upcomingInterviews={[
    {
      id: "int-1",
      job_title: "Senior React Developer",
      company_name: "TechCorp",
      scheduled_at: "2026-01-12T14:00:00Z",
      duration_minutes: 60,
      meeting_link: "https://zoom.us/..."
    }
  ]}
  profileCompletionScore={75}
  followingCompanies={12}
  activities={[
    {
      id: "act-1",
      type: "application",
      message: "Applied to Senior React Developer at TechCorp",
      time: "2 hours ago"
    }
  ]}
  onNavigate={(route) => console.log('Navigate to:', route)}
  onSignOut={() => console.log('Sign out')}
/>
```

### **Company Dashboard Example**

```typescript
<Dashboard
  user={{
    id: "company-456",
    email: "hr@techcorp.com",
    account_type: "company",
    company_name: "TechCorp Inc",
    avatar: "https://..."
  }}
  stats={[
    { label: "Active Jobs", value: "5", icon: Briefcase, color: "blue" },
    { label: "Applications", value: "142", icon: Users, color: "cyan" },
    { label: "Avg Match Score", value: "78", icon: Target, color: "gold" },
    { label: "Time Saved", value: "48h", icon: Zap, color: "green" }
  ]}
  candidates={[
    {
      id: "cand-1",
      name: "Sarah Johnson",
      role: "Senior Full Stack Developer",
      score: 94,
      skills: ["React", "Node.js", "AWS"],
      status: "interview",
      applied_date: "2026-01-06T11:00:00Z"
    }
  ]}
  activeJobs={5}
  scheduledInterviews={[
    {
      id: "int-1",
      candidate_name: "Sarah Johnson",
      job_title: "Senior React Developer",
      scheduled_at: "2026-01-12T14:00:00Z",
      duration_minutes: 60,
      location: "Office - Building A"
    }
  ]}
  activities={[
    {
      id: "act-1",
      type: "application",
      message: "New application for Senior React Developer",
      time: "1 hour ago"
    }
  ]}
  onNavigate={(route) => console.log('Navigate to:', route)}
  onSignOut={() => console.log('Sign out')}
/>
```

---

## 🎨 **Visual Design Details**

### **Color Coding**

**Status Badges:**
- **Pending**: Gold background, gold text
- **Screening**: Cyan background, cyan text
- **Interview**: Blue background, blue text
- **Offer**: Purple background, purple text
- **Hired**: Green background, green text
- **Rejected**: Red background, red text

**Match Scores:**
- **90-100 (Excellent)**: Green
- **75-89 (Good)**: Blue
- **60-74 (Average)**: Orange
- **0-59 (Poor)**: Red

**Stat Icons:**
- **Blue**: Primary metrics (jobs, applications)
- **Cyan**: Secondary metrics (match scores, views)
- **Gold**: Warning/attention metrics (pending, screening)
- **Green**: Success metrics (hired, success rate)
- **Red**: Negative metrics (rejected, low scores)
- **Orange**: Neutral metrics (time, dates)

### **Animations & Interactions**

- **Card hover**: `translateY(-4px)` + shadow increase
- **List item hover**: `translateX(4px)` + background change to blue-light
- **Status badge**: No animation, static display
- **Match score**: Pulse animation on load
- **Empty state CTA**: Hover lift + shadow

---

## 🚀 **Implementation Checklist**

### **Backend Requirements**

- [ ] `GET /api/dashboard/stats` - Return role-specific stats
- [ ] `GET /api/applications` - For personal: user's applications
- [ ] `GET /api/applications` - For company: applications for company's jobs
- [ ] `GET /api/jobs/saved` - Personal: saved jobs
- [ ] `GET /api/jobs/recommended` - Personal: AI recommendations
- [ ] `GET /api/interviews` - Role-specific upcoming interviews
- [ ] `GET /api/follow/following` - Personal: following count
- [ ] `GET /api/follow/followers` - Company: follower count
- [ ] `GET /api/candidates` - Company: all candidates with scores
- [ ] `GET /api/dashboard/activities` - Recent activity feed

### **Frontend Tasks**

- [ ] Update Dashboard component with role-based navigation
- [ ] Create Application card component
- [ ] Create SavedJob card component
- [ ] Create RecommendedJob card component
- [ ] Create Candidate card component
- [ ] Create Interview list component
- [ ] Add profile completion widget
- [ ] Implement empty states for all sections
- [ ] Add loading states
- [ ] Test mobile responsiveness
- [ ] Test role switching (personal ↔ company)

### **Testing Scenarios**

- [ ] Personal account with 0 applications
- [ ] Personal account with 10+ applications
- [ ] Personal account with incomplete profile
- [ ] Company account with 0 candidates
- [ ] Company account with 50+ candidates
- [ ] Company account with 5 active jobs
- [ ] Both: Scheduled interviews
- [ ] Both: Recent activity feed
- [ ] Mobile view (sidebar overlay)
- [ ] Navigation between tabs

---

## 📱 **Responsive Behavior**

### **Desktop (>1024px)**
- Sidebar: 280px fixed, always visible
- Main content: Full width minus sidebar
- Cards grid: 2 columns (or wide cards span full width)
- Stats: 4 columns

### **Tablet (768-1024px)**
- Sidebar: 280px fixed, toggle with menu button
- Main content: Full width when sidebar hidden
- Cards grid: 1 column
- Stats: 2 columns

### **Mobile (<768px)**
- Sidebar: Overlay (transform translateX)
- Background overlay when sidebar open
- Main content: Full width
- Cards grid: 1 column
- Stats: 1 column
- Touch-friendly button sizes (44x44px minimum)

---

## ✅ **Key Differences Summary**

| Feature | Personal (Job Seeker) | Company (Recruiter) |
|---------|----------------------|---------------------|
| **Primary Action** | Browse Jobs | Post Job |
| **Main View** | My Applications | Top Candidates |
| **Secondary View** | Recommended Jobs | Active Job Postings |
| **Tertiary View** | Saved Jobs | Scheduled Interviews |
| **Profile Widget** | Completion Score | N/A |
| **Following** | Companies + Users | Followers Only |
| **Interviews** | "My Interviews" | "Interviews" (with candidates) |
| **Resume Section** | Resume Manager | Resume Screening |
| **Analytics** | Application Stats | Hiring Metrics |

---

**Built with ❤️ for HireSight - Making Hiring Fair & Intelligent**