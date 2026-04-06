# Dashboard Templates

Beautiful, production-ready dashboard templates for HireSight.

## Files

1. **personal_dashboard.html** - Job seeker dashboard
2. **company_dashboard.html** - Company/recruiter dashboard

## Features

✅ Gradient hero headers with personalized welcome
✅ 4 stats cards with real-time metrics
✅ Recent activity sections
✅ AI-powered recommendations
✅ Quick action cards
✅ Profile/pipeline tracking
✅ Empty states with CTAs
✅ Fully responsive design
✅ Card hover effects
✅ Color-coded status badges

## Installation

```bash
cp *.html /path/to/your/project/templates/dashboard/
```

## Quick Start

### Personal Dashboard View
```python
from django.views.generic import TemplateView
from apps.accounts.decorators import personal_required

@method_decorator(personal_required, name='dispatch')
class PersonalDashboardView(TemplateView):
    template_name = 'dashboard/personal_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your context data here
        return context
```

### Company Dashboard View
```python
@method_decorator(company_required, name='dispatch')
class CompanyDashboardView(TemplateView):
    template_name = 'dashboard/company_dashboard.html'
    # ...
```

## Required Context

See **DASHBOARD_TEMPLATES_GUIDE.md** for complete context structure.

## URLs Required

Personal: `jobs:browse`, `applications:my_applications`, `resumes:upload`
Company: `jobs:create`, `screening:upload`, `analytics:dashboard`

## See Also

- **DASHBOARD_TEMPLATES_GUIDE.md** - Complete documentation
- **base.html** - Main layout template