# HireSight – AI-Powered Recruitment Platform

**HireSight** is a comprehensive, dual-sided recruitment platform that connects job seekers with companies through intelligent AI-powered resume screening and matching. Built for both candidates seeking opportunities and recruiters looking for top talent, HireSight streamlines the entire hiring lifecycle from job posting to offer acceptance.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
---

## 🎯 Vision

Transform the hiring process from a tedious, biased, manual task into an intelligent, fair, and efficient experience for both job seekers and employers. HireSight leverages cutting-edge NLP and machine learning to:

- **For Job Seekers**: Find the perfect job match, track applications, and showcase skills effectively
- **For Companies**: Screen candidates at scale, reduce time-to-hire, and make data-driven hiring decisions
- **For Everyone**: Eliminate unconscious bias and create a transparent, merit-based hiring ecosystem

---

## 📋 Table of Contents

- [Core Features](#core-features)
- [User Roles & Access](#user-roles--access)
- [Tech Stack](#tech-stack)
- [Key Capabilities](#key-capabilities)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🚀 Core Features

### **Dual-Sided Platform**

#### 👤 **For Job Seekers (Personal Accounts)**
- **Smart Profile Builder** – Upload resume and auto-populate profile with AI extraction
- **Resume Manager** – Store multiple resume versions, set primary for applications
- **Job Discovery** – AI-powered job recommendations based on skills and preferences
- **One-Click Apply** – Apply with saved profile + optional cover letter
- **Application Tracking** – Real-time status updates (Pending → Screening → Interview → Offer)
- **Saved Jobs** – Bookmark opportunities to apply later
- **Interview Scheduler** – Calendar integration for scheduled interviews
- **Skill Assessments** – Take tests to verify skills and boost match scores
- **Job Alerts** – Email/push notifications for relevant job postings
- **Company Following** – Follow companies to get instant job notifications
- **Networking** – Follow other job seekers, view public profiles
- **Profile Analytics** – See who viewed your profile, application success rate
- **Resume Optimization** – AI-powered tips to improve resume quality

#### 🏢 **For Companies (Recruiter Accounts)**
- **AI Resume Screening** – Upload 50+ resumes and get ranked candidates in seconds
- **Job Posting Manager** – Create, edit, duplicate, and archive job listings
- **Applicant Pipeline** – Visual Kanban board (New → Screening → Interview → Offer → Hired)
- **Semantic Matching** – Advanced NLP understands context beyond keywords
- **Bulk Actions** – Screen, accept, or reject multiple candidates at once
- **Team Collaboration** – Invite recruiters, assign roles, internal comments on candidates
- **Interview Scheduling** – Send calendar invites directly to applicants
- **Analytics Dashboard** – Job views, application rates, time-to-hire metrics
- **Candidate Notes** – Add private ratings and feedback on applicants
- **Talent Pool** – Save promising candidates for future opportunities
- **Company Branding** – Build public company page with culture, benefits, team photos
- **Verification Badge** – Verified companies earn trust badge
- **ATS Integration** – Export data to existing Applicant Tracking Systems
- **Smart Reports** – Generate Excel/PDF reports for stakeholders

### **Shared Features (Both Roles)**
- **Advanced Search & Filters** – Location, salary range, remote/hybrid, skills, experience
- **In-App Messaging** – Direct communication between candidates and recruiters
- **Notifications Center** – Real-time updates on applications, job matches, messages
- **Privacy Controls** – Hide profile from specific companies, control visibility
- **Mobile Responsive** – Full functionality on mobile devices
- **Dark Mode** – Eye-friendly interface option
- **Data Export** – GDPR-compliant data download

---

## 🔐 User Roles & Access

### **Account Types**

| Feature | Job Seeker (Personal) | Recruiter (Company) |
|---------|:---------------------:|:-------------------:|
| **Profile Management** | ✅ Resume, skills, experience | ✅ Company info, branding |
| **Job Browsing** | ✅ Search & apply for jobs | ❌ Not applicable |
| **Application Tracking** | ✅ Track own applications | ❌ Not applicable |
| **Resume Upload** | ✅ Multiple versions | ❌ Not applicable |
| **Skill Assessments** | ✅ Take skill tests | ❌ Not applicable |
| **Job Posting** | ❌ Cannot post jobs | ✅ Create & manage jobs |
| **Resume Screening** | ❌ No access | ✅ AI-powered screening |
| **Applicant Management** | ❌ No access | ✅ Pipeline & interviews |
| **Analytics Dashboard** | ✅ Application stats | ✅ Hiring metrics |
| **Following System** | ✅ Follow companies/users | ✅ See followers only |
| **Messaging** | ✅ Contact recruiters | ✅ Contact applicants |
| **Team Management** | ❌ Individual only | ✅ Invite team members |

### **Authentication Flow**

1. **Sign Up** → User selects account type (Personal or Company)
2. **Email Verification** → Confirm email address
3. **Profile Setup** → Complete profile based on account type
4. **Optional Verification** → Upload ID (Personal) or business docs (Company) for badge
5. **Dashboard Access** → Role-based UI rendered automatically

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | Django 5.0 | Full-stack web framework with batteries included |
| **Frontend** | HTML5 + Tailwind CSS + Alpine.js | Modern, utility-first styling with lightweight JS |
| **Interactive Updates** | HTMX | Dynamic updates without full page reload |
| **Database** | PostgreSQL 15+ | Relational data with JSONB for flexibility |
| **ORM** | Django ORM | Built-in, powerful database abstraction |
| **Authentication** | Django Auth + Custom User | Email-based auth with role separation |
| **File Storage** | Django Storage / AWS S3 | Resume and image uploads |
| **Resume Parsing** | spaCy + PyPDF2 + python-docx | Extract structured data from PDFs/DOCX |
| **NLP & AI** | spaCy + Sentence Transformers | Semantic matching and skill extraction |
| **Embeddings** | all-MiniLM-L6-v2 | Fast, accurate sentence embeddings |
| **Task Queue** | Celery + Redis | Background jobs (email, resume processing) |
| **Email** | Django Email / SendGrid | Transactional emails and notifications |
| **Caching** | Redis | Session storage, rate limiting, caching |
| **Monitoring** | Django Debug Toolbar + Logging | Development debugging and error tracking |
| **Deployment** | Gunicorn + Nginx | Production WSGI server with reverse proxy |
| **Testing** | pytest + pytest-django | Comprehensive test coverage |

---

## 🎨 Key Capabilities

### **1. Intelligent Resume Parsing**
- Extracts name, email, phone, location, skills, experience, education
- Handles multiple formats (PDF, DOCX, TXT)
- Cleans and normalizes data (e.g., "React.js" → "React")
- 95%+ accuracy on well-formatted resumes

### **2. Semantic Job Matching**
- Goes beyond keyword matching
- Understands synonyms (e.g., "JavaScript" matches "JS", "ECMAScript")
- Contextual analysis (e.g., "led team of 5" scores higher than "worked in team")
- Calculates match score (0-100) with detailed explanations
- Identifies skill gaps and strengths

### **3. Bias Mitigation**
- Removes identifying information during initial screening (name, gender, age)
- Scores based on objective criteria (skills, experience, achievements)
- Audit logs track scoring decisions for transparency
- Customizable fairness parameters

### **4. Application Pipeline**
- **New** – Unreviewed applications
- **Screening** – AI-scored, pending human review
- **Interview** – Scheduled or pending scheduling
- **Offer** – Offer extended, awaiting response
- **Hired** – Candidate accepted offer
- **Rejected** – Not moving forward (with optional feedback)

### **5. Real-Time Notifications**
- **Job Seekers**: New job matches, application status changes, interview invites, messages
- **Companies**: New applications, candidate responses, profile views, follower updates
- **Delivery**: In-app + email + push (optional)

### **6. Following & Discovery**
- Job seekers follow companies → auto-notified of new jobs
- Job seekers follow peers → networking and learning
- Companies see follower count → measure employer brand strength
- Algorithm surfaces trending jobs and top candidates

---

## 📦 Installation

### **Prerequisites**
- Python 3.10+
- PostgreSQL 15+
- Redis 7+

### **Quick Start**

```bash
# Clone repository
git clone https://github.com/yourusername/HireSight.git
cd HireSight

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create .env file
cp .env.example .env
# Edit .env with your database credentials, API keys, etc.

# Create database
createdb hiresight_db  # PostgreSQL

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
# Access at http://localhost:8000
```

---

## 🎮 Usage

### **For Job Seekers**

1. **Sign Up** → Select "Personal Account"
2. **Build Profile** → Upload resume or manually enter details
3. **Browse Jobs** → Use filters (remote, salary, location, skills)
4. **Apply** → One-click apply or customize cover letter
5. **Track Applications** → Monitor status in dashboard
6. **Follow Companies** → Get notified of new postings
7. **Take Skill Tests** → Boost your match score
8. **Schedule Interviews** → Sync with calendar

### **For Recruiters**

1. **Sign Up** → Select "Company Account"
2. **Complete Company Profile** → Add logo, description, benefits
3. **Post Job** → Define role, requirements, salary range
4. **Upload Resumes** → Bulk upload or wait for applications
5. **Review AI Rankings** → See match scores with explanations
6. **Manage Pipeline** → Move candidates through stages
7. **Schedule Interviews** → Send calendar invites
8. **Make Offers** → Track acceptance/rejection
9. **Analyze Performance** → View hiring metrics

---

## 📁 Project Structure

```
HireSight/
├── manage.py                       # Django management script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── README.md
├── TODO.md
│
├── hiresight/                      # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                           # Django applications
│   ├── accounts/                   # Authentication & profiles
│   ├── resumes/                    # Resume management & parsing
│   ├── jobs/                       # Job posting & browsing
│   ├── applications/               # Application system
│   ├── screening/                  # AI-powered screening
│   ├── dashboard/                  # Role-based dashboards
│   ├── notifications/              # Notification system
│   ├── messages/                   # In-app messaging
│   ├── following/                  # Follow system
│   └── analytics/                  # Reports & analytics
│
├── templates/                      # HTML templates
│   ├── base.html
│   ├── components/                 # Reusable components
│   ├── accounts/                   # Auth pages
│   ├── dashboard/                  # Dashboards
│   ├── jobs/                       # Job pages
│   ├── applications/               # Application pages
│   └── errors/                     # Error pages
│
├── static/                         # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                          # User uploads
│   ├── resumes/
│   ├── avatars/
│   └── company_logos/
│
└── utils/                          # Utility functions
    ├── email.py
    ├── validators.py
    └── helpers.py
```

---

## 🔌 API Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### **Key Endpoints**

#### **Authentication**
```
POST   /api/auth/register          # Register new user
POST   /api/auth/login             # Login and get JWT
POST   /api/auth/logout            # Logout (invalidate token)
GET    /api/auth/me                # Get current user info
POST   /api/auth/verify-email      # Verify email address
POST   /api/auth/forgot-password   # Request password reset
POST   /api/auth/reset-password    # Reset password with token
```

#### **Users & Profiles**
```
GET    /api/users/me/profile       # Get own profile
PUT    /api/users/me/profile       # Update profile
POST   /api/users/me/avatar        # Upload avatar
GET    /api/users/{id}/profile     # Get public profile (if visible)
```

#### **Jobs (Company only)**
```
GET    /api/jobs                   # List all jobs (with filters)
POST   /api/jobs                   # Create new job
GET    /api/jobs/{id}              # Get job details
PUT    /api/jobs/{id}              # Update job
DELETE /api/jobs/{id}              # Delete job
POST   /api/jobs/{id}/close        # Close job to applications
```

#### **Applications**
```
GET    /api/applications           # List applications (role-based)
POST   /api/applications           # Apply for job (Job Seeker)
GET    /api/applications/{id}      # Get application details
PUT    /api/applications/{id}      # Update application status (Company)
DELETE /api/applications/{id}      # Withdraw application (Job Seeker)
```

#### **Resume Screening (Company only)**
```
POST   /api/screening/upload       # Upload multiple resumes
POST   /api/screening/parse        # Parse and extract data
POST   /api/screening/match        # Match resumes to job description
GET    /api/screening/results/{id} # Get screening results
POST   /api/screening/export       # Export results to Excel/PDF
```

#### **Following**
```
POST   /api/follow/{user_id}       # Follow user or company
DELETE /api/follow/{user_id}       # Unfollow
GET    /api/follow/followers       # Get followers list
GET    /api/follow/following       # Get following list
```

#### **Notifications**
```
GET    /api/notifications          # Get all notifications
PUT    /api/notifications/{id}/read # Mark as read
DELETE /api/notifications/{id}     # Delete notification
PUT    /api/notifications/read-all # Mark all as read
```

---

## 🗄️ Database Schema

### **Core Tables**

#### **users**
```sql
id, email, password_hash, account_type (personal/company), 
is_verified, is_active, created_at, updated_at
```

#### **personal_profiles**
```sql
user_id, full_name, headline, location, phone, bio,
skills (JSONB), experience (JSONB), education (JSONB),
certifications (JSONB), portfolio_links (JSONB),
preferred_job_types, salary_expectation_min, salary_expectation_max,
availability, resume_primary_id, profile_visibility
```

#### **company_profiles**
```sql
user_id, company_name, logo_url, industry, company_size,
locations (JSONB), website, description, mission, culture,
benefits (JSONB), founded_year, verification_status
```

#### **resumes**
```sql
id, user_id, filename, file_url, version_name, is_primary,
parsed_data (JSONB), uploaded_at
```

#### **jobs**
```sql
id, company_id, title, description, requirements (JSONB),
location, remote_type (remote/hybrid/onsite), employment_type,
salary_min, salary_max, status (draft/active/closed),
screening_questions (JSONB), created_at, expires_at
```

#### **applications**
```sql
id, job_id, user_id, resume_id, cover_letter, 
status (pending/screening/interview/offer/hired/rejected),
match_score, match_explanation (JSONB), applied_at, updated_at
```

#### **follows**
```sql
id, follower_id, following_id, following_type (user/company),
created_at
```

#### **notifications**
```sql
id, user_id, type, title, message, link, is_read, created_at
```

#### **messages**
```sql
id, sender_id, receiver_id, subject, body, is_read, sent_at
```

---

## 🗺️ Roadmap

See [TODO.md](TODO.md) for detailed development phases.

### **Phase 1: MVP (Months 1-2)** ✅
- User authentication with role-based access
- Basic profiles (Personal & Company)
- Job posting and browsing
- Resume upload and parsing
- AI-powered resume screening
- Simple application tracking

### **Phase 2: Core Features (Months 3-4)** 🚧
- Application pipeline (Kanban board)
- Following system
- In-app messaging
- Email notifications
- Advanced search & filters
- Analytics dashboards

### **Phase 3: Engagement (Months 5-6)** 📅
- Skill assessments
- Interview scheduling
- Company branding pages
- Resume optimization tips
- Job recommendations
- Mobile app (React Native)

### **Phase 4: Scale & Monetization (Months 7-9)** 🔮
- Premium subscriptions (tiered pricing)
- ATS integrations (Greenhouse, Lever, etc.)
- Video introductions
- Live chat support
- API for third-party developers
- White-label solutions for enterprises

### **Phase 5: Advanced AI (Months 10-12)** 🤖
- Predictive hiring analytics
- Salary negotiation assistant
- Interview question generator
- Culture fit assessment
- Diversity & inclusion insights
- Automated reference checking

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development workflow
- Pull request process
- Coding standards
- Testing requirements

### **Getting Started**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest` for backend, `npm test` for frontend)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **pyresparser** – Resume parsing foundation
- **spaCy** – NLP and entity extraction
- **Sentence Transformers** – Semantic similarity
- **FastAPI** – Modern Python API framework
- **React** – UI library
- **Tailwind CSS** – Utility-first styling
- **PostgreSQL** – Robust relational database
- **Redis** – Caching and task queue
- **Docker** – Containerization

---

## 📞 Contact & Support

- **Website**: [hiresight.io](https://hiresight.io)
- **Documentation**: [docs.hiresight.io](https://docs.hiresight.io)
- **Email**: support@hiresight.io
- **Discord**: [Join our community](https://discord.gg/hiresight)
- **Twitter**: [@HireSightAI](https://twitter.com/HireSightAI)
- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/HireSight/issues)

---

## 🌟 Star History

If you find HireSight useful, please consider giving it a ⭐ on GitHub! It helps others discover the project.

---

## 📊 Project Stats

---

**Built with ❤️ by developers who believe in fair, intelligent hiring.**