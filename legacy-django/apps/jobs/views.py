from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden, Http404, HttpResponseNotAllowed
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, date
import uuid

from apps.applications.models import ApplicationStatus
from .models import Job, SavedJob, JobView, JobStatus
from .forms import (
    JobCreateForm, JobEditForm, JobFilterForm,
    JobQuickEditForm, JobDuplicateForm, SavedJobForm
)


# ==================== Mixins ====================

class CompanyRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user has a company account."""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'company_profile')
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            'You need a company account to access this page.'
        )
        return redirect('dashboard:dashboard_home')


class JobOwnerMixin(UserPassesTestMixin):
    """Mixin to ensure user owns the job."""

    def test_func(self):
        job = self.get_object()
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'company_profile') and
            job.company == self.request.user.company_profile
        )

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this job.')
        return redirect('jobs:manage')


# ==================== Job Seeker Views (Public) ====================

class JobBrowseView(ListView):
    """Browse all active jobs with filtering."""
    model = Job
    template_name = 'jobs/browse.html'
    context_object_name = 'jobs'
    paginate_by = 20

    def get_queryset(self):
        """Get filtered job queryset."""
        queryset = Job.objects.filter(
            status=JobStatus.ACTIVE
        ).select_related(
            'company', 'company__user'
        )

        # Get filter form
        form = JobFilterForm(self.request.GET)
        
        if form.is_valid():
            # Search
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(company__company_name__icontains=search)
                )

            # Location and radius filtering
            location = form.cleaned_data.get('location')
            location_radius = form.cleaned_data.get('location_radius')

            if location and location_radius:
                # Geocode the search location
                try:
                    from geopy.geocoders import Nominatim
                    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

                    geolocator = Nominatim(user_agent="hiresight-location-search")
                    search_location = geolocator.geocode(location, timeout=10)

                    if search_location:
                        search_lat = search_location.latitude
                        search_lon = search_location.longitude
                        radius = int(location_radius)

                        # Filter jobs within radius (only non-remote jobs with coordinates)
                        job_ids_within_radius = []
                        for job in queryset.filter(is_remote=False, latitude__isnull=False, longitude__isnull=False):
                            distance = job.distance_to(search_lat, search_lon)
                            if distance and distance <= radius:
                                job_ids_within_radius.append(job.id)

                        if job_ids_within_radius:
                            queryset = queryset.filter(id__in=job_ids_within_radius)
                        else:
                            # No jobs found within radius, return empty queryset
                            queryset = queryset.none()

                except (GeocoderTimedOut, GeocoderUnavailable, ValueError):
                    # If geocoding fails, fall back to text search
                    queryset = queryset.filter(location__icontains=location)
            elif location:
                # Text search only (no radius specified)
                queryset = queryset.filter(location__icontains=location)

            # Remote type
            remote_type = form.cleaned_data.get('remote_type')
            if remote_type:
                queryset = queryset.filter(remote_type=remote_type)

            # Employment type
            employment_type = form.cleaned_data.get('employment_type')
            if employment_type:
                queryset = queryset.filter(employment_type=employment_type)

            # Experience level
            experience_level = form.cleaned_data.get('experience_level')
            if experience_level:
                queryset = queryset.filter(experience_level=experience_level)

            # Skills filtering with AND/OR logic
            skills = form.cleaned_data.get('skills')
            skills_match = form.cleaned_data.get('skills_match', 'any')
            if skills:
                # Split skills by comma and filter jobs
                skill_list = [skill.strip().lower() for skill in skills.split(',') if skill.strip()]
                if skill_list:
                    if skills_match == 'all':
                        # Match ALL skills (AND logic)
                        # Job must have all required skills
                        for skill in skill_list:
                            queryset = queryset.filter(tags__icontains=skill)
                    else:
                        # Match ANY skill (OR logic) - default behavior
                        q_objects = Q()
                        for skill in skill_list:
                            q_objects |= Q(tags__icontains=skill)
                        queryset = queryset.filter(q_objects)

            # Salary range (min and max)
            salary_min = form.cleaned_data.get('salary_min')
            salary_max = form.cleaned_data.get('salary_max')
            if salary_min:
                # Find jobs where salary range overlaps with user's range
                queryset = queryset.filter(
                    Q(salary_min__gte=salary_min) | Q(salary_max__gte=salary_min)
                )
            if salary_max:
                queryset = queryset.filter(
                    Q(salary_max__lte=salary_max) | Q(salary_min__lte=salary_max)
                )

            # Posted within
            posted_within = form.cleaned_data.get('posted_within')
            if posted_within:
                cutoff_date = timezone.now() - timedelta(days=int(posted_within))
                queryset = queryset.filter(published_at__gte=cutoff_date)

            # Sorting
            sort_by = form.cleaned_data.get('sort_by', 'relevance')
            if sort_by == 'date':
                queryset = queryset.order_by('-published_at')
            elif sort_by == 'salary':
                queryset = queryset.order_by('-salary_max', '-salary_min')
            elif sort_by == 'recommendations':
                # Personalized recommendations - requires authentication
                if self.request.user.is_authenticated and hasattr(self.request.user, 'personal_profile'):
                    from .recommendations import recommendation_engine
                    
                    # Get jobs and calculate recommendation scores
                    jobs_with_scores = []
                    for job in queryset:
                        score = recommendation_engine.calculate_match_score(self.request.user, job)
                        jobs_with_scores.append((job, score))
                    
                    # Sort by recommendation score (highest first)
                    jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
                    
                    # Extract sorted jobs
                    job_ids = [job.id for job, score in jobs_with_scores]
                    if job_ids:
                        # Preserve order by using case/whens
                        from django.db.models import Case, When
                        order_by_case = Case(*[When(id=id_val, then=pos) for pos, id_val in enumerate(job_ids)])
                        queryset = Job.objects.filter(id__in=job_ids).order_by(order_by_case)
                    else:
                        queryset = Job.objects.none()
                else:
                    # Fall back to date sorting for non-authenticated users
                    queryset = queryset.order_by('-published_at')
            # 'relevance' is default ordering

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter form to context."""
        context = super().get_context_data(**kwargs)
        context['filter_form'] = JobFilterForm(self.request.GET)
        return context


class JobDetailView(DetailView):
    """View job details."""
    model = Job
    template_name = 'jobs/detail.html'
    context_object_name = 'job'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Get job with related data."""
        return Job.objects.select_related(
            'company', 'company__user'
        ).prefetch_related('saved_by')

    def get_object(self, queryset=None):
        """
        Handle both slug and UUID-based lookups intelligently.
        
        This method can handle:
        1. Direct UUID lookup via job_id parameter (from by-id/ route)
        2. Slug lookup via slug parameter
        3. UUID passed as slug parameter (auto-detect and handle)
        """
        if queryset is None:
            queryset = self.get_queryset()
        
        # Check if we have a job_id parameter (from by-id/ route)
        job_id = self.kwargs.get('job_id')
        if job_id:
            try:
                return queryset.get(id=job_id)
            except Job.DoesNotExist:
                raise Http404(f"Job with ID {job_id} does not exist")
        
        # Get the slug parameter
        slug_or_uuid = self.kwargs.get(self.slug_url_kwarg)
        
        if not slug_or_uuid:
            raise Http404("No job identifier provided")
        
        # Try to detect if it's a UUID
        try:
            # Attempt to parse as UUID
            uuid_obj = uuid.UUID(slug_or_uuid)
            
            # It's a valid UUID! Try to fetch by UUID
            try:
                job = queryset.get(id=uuid_obj)
                
                # Redirect to the proper slug-based URL for SEO
                # This is optional - comment out if you want to allow UUID URLs
                # return redirect('jobs:detail', slug=job.slug, permanent=True)
                
                return job
            except Job.DoesNotExist:
                raise Http404(f"Job with ID {uuid_obj} does not exist")
                
        except (ValueError, AttributeError):
            # Not a UUID, treat as slug
            pass
        
        # Look up by slug
        try:
            return queryset.get(**{self.slug_field: slug_or_uuid})
        except Job.DoesNotExist:
            raise Http404(f"Job with slug '{slug_or_uuid}' does not exist")

    def get(self, request, *args, **kwargs):
        """Track job view."""
        response = super().get(request, *args, **kwargs)
        
        # Increment view count
        self.object.increment_views()
        
        # Track detailed view
        self._track_view()
        
        return response

    def _track_view(self):
        """Track job view in JobView model."""
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')

        # Create view record
        JobView.objects.create(
            job=self.object,
            user=self.request.user if self.request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255],
            referrer=self.request.META.get('HTTP_REFERER', '')[:255]
        )

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        
        # Check if user has saved this job
        if self.request.user.is_authenticated:
            context['is_saved'] = self.object.is_saved_by(self.request.user)
        
        # Add similar jobs
        from .filters import get_similar_jobs
        context['similar_jobs'] = get_similar_jobs(self.object, limit=5)
        
        return context


class SavedJobsView(LoginRequiredMixin, ListView):
    """View user's saved jobs."""
    model = SavedJob
    template_name = 'jobs/saved.html'
    context_object_name = 'saved_jobs'
    paginate_by = 20

    def get_queryset(self):
        """Get user's saved jobs."""
        return SavedJob.objects.filter(
            user=self.request.user
        ).select_related(
            'job', 'job__company', 'job__company__user'
        ).order_by('-saved_at')


@login_required
@require_POST
def toggle_save_job(request, slug):
    """Toggle save/unsave job."""
    job = get_object_or_404(Job, slug=slug)
    
    saved_job, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if not created:
        # Already saved, so unsave
        saved_job.delete()
        message = f'Removed "{job.title}" from saved jobs.'
        is_saved = False
    else:
        message = f'Saved "{job.title}" to your saved jobs.'
        is_saved = True
    
    # Return JSON for AJAX or redirect for regular request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_saved': is_saved,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('jobs:detail', slug=slug)


# ==================== Company Views (Job Management) ====================

class JobManageView(LoginRequiredMixin, CompanyRequiredMixin, ListView):
    """Manage company's job postings."""
    model = Job
    template_name = 'jobs/manage.html'
    context_object_name = 'jobs'
    paginate_by = 20

    def get_queryset(self):
        """Get company's jobs."""
        return Job.objects.filter(
            company=self.request.user.company_profile
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add stats to context."""
        context = super().get_context_data(**kwargs)
        company = self.request.user.company_profile

        jobs = Job.objects.filter(company=company)

        context['stats'] = {
            'total': jobs.count(),
            'active': jobs.filter(status=JobStatus.ACTIVE).count(),
            'draft': jobs.filter(status=JobStatus.DRAFT).count(),
            'closed': jobs.filter(status=JobStatus.CLOSED).count(),
            'total_views': sum(j.views_count for j in jobs),
            'total_applications': sum(j.applications_count for j in jobs),
        }

        return context


class JobCreateView(LoginRequiredMixin, CompanyRequiredMixin, CreateView):
    """Create new job posting."""
    model = Job
    form_class = JobCreateForm
    template_name = 'jobs/create.html'
    success_url = reverse_lazy('jobs:manage')

    def get_form_kwargs(self):
        """Pass company to form."""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company_profile
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        job = form.save()
        
        messages.success(
            self.request,
            f'Job posting "{job.title}" created successfully!'
        )
        
        return super().form_valid(form)


class JobEditView(LoginRequiredMixin, JobOwnerMixin, UpdateView):
    """Edit existing job posting."""
    model = Job
    form_class = JobEditForm
    template_name = 'jobs/edit.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_form_kwargs(self):
        """Pass company to form."""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company_profile
        return kwargs

    def get_success_url(self):
        """Redirect to job detail."""
        return reverse('jobs:detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        """Handle successful update."""
        messages.success(
            self.request,
            f'Job posting "{form.instance.title}" updated successfully!'
        )
        return super().form_valid(form)


class JobDeleteView(LoginRequiredMixin, JobOwnerMixin, DeleteView):
    """Delete job posting."""
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:manage')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def delete(self, request, *args, **kwargs):
        """Delete and show message."""
        job = self.get_object()
        title = job.title
        
        result = super().delete(request, *args, **kwargs)
        
        messages.success(request, f'Job posting "{title}" deleted successfully.')
        return result


@login_required
def duplicate_job(request, slug):
    """Duplicate an existing job."""
    if request.method not in ['POST', 'GET']:
        return HttpResponseNotAllowed(['POST', 'GET'])
    
    # Check company permission
    if not hasattr(request.user, 'company_profile'):
        return HttpResponseForbidden('Company account required')
    
    original_job = get_object_or_404(
        Job,
        slug=slug,
        company=request.user.company_profile
    )
    
    # Create duplicate
    duplicate = Job.objects.get(pk=original_job.pk)
    duplicate.pk = None
    duplicate.id = None
    duplicate.slug = None
    duplicate.title = f"{original_job.title} (Copy)"
    duplicate.status = JobStatus.DRAFT
    duplicate.published_at = None
    duplicate.closed_at = None
    duplicate.views_count = 0
    duplicate.applications_count = 0
    duplicate.save()
    
    messages.success(
        request,
        f'Job "{original_job.title}" duplicated successfully. Edit the new job posting.'
    )
    
    return redirect('jobs:edit', slug=duplicate.slug)


@login_required
@require_POST
def change_job_status(request, slug):
    """Quick change job status."""
    # Check company permission
    if not hasattr(request.user, 'company_profile'):
        return HttpResponseForbidden('Company account required')
    
    job = get_object_or_404(
        Job,
        slug=slug,
        company=request.user.company_profile
    )
    
    new_status = request.POST.get('status')
    
    if new_status in dict(JobStatus.choices):
        job.status = new_status
        job.save()
        
        messages.success(
            request,
            f'Job status changed to "{job.get_status_display()}".'
        )
    else:
        messages.error(request, 'Invalid status.')
    
    return redirect('jobs:manage')


class JobStatsView(LoginRequiredMixin, JobOwnerMixin, DetailView):
    """View job analytics and statistics."""
    model = Job
    template_name = 'jobs/stats.html'
    context_object_name = 'job'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        """Add analytics data."""
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Get views over time (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        views_query = JobView.objects.filter(
            job=job,
            viewed_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(viewed_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        views_by_day = list(views_query)
        max_views = max((entry['count'] for entry in views_by_day), default=0)
        for entry in views_by_day:
            entry['bar_width'] = round((entry['count'] / max_views) * 100, 2) if max_views else 0

        context['views_by_day'] = views_by_day
        context['views_by_day_max'] = max_views
        context['daily_view_labels'] = [entry['day'].strftime('%b %d') if isinstance(entry['day'], date) else entry['day'] for entry in views_by_day]
        context['daily_view_counts'] = [entry['count'] for entry in views_by_day]

        # Application status distribution for charts
        status_counts = {status.value: 0 for status in ApplicationStatus}
        application_status_data = job.applications.values('status').annotate(
            count=Count('id')
        )
        for entry in application_status_data:
            status_counts[entry['status']] = entry['count']
        context['status_labels'] = [label for _, label in ApplicationStatus.choices]
        context['status_values'] = [value for value, _ in ApplicationStatus.choices]
        context['status_counts'] = [status_counts[value] for value, _ in ApplicationStatus.choices]
        context['total_views'] = job.views_count
        context['total_applications'] = job.applications_count
        context['conversion_rate'] = job.application_rate
        
        return context


@login_required
def job_stats_api(request, slug):
    """API endpoint for job statistics."""
    # Check company permission
    if not hasattr(request.user, 'company_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    job = get_object_or_404(
        Job,
        slug=slug,
        company=request.user.company_profile
    )
    
    stats = {
        'views': job.views_count,
        'applications': job.applications_count,
        'conversion_rate': job.application_rate,
        'days_active': job.days_since_posted,
        'status': job.status,
    }
    
    return JsonResponse(stats)
