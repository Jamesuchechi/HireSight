"""
Analytics views for displaying company and personal analytics dashboards.
"""
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse, HttpResponse
from django.views import View
import csv
from io import BytesIO
from django.http import HttpResponse, request
from apps.assessments.analytics_helpers import (
    get_skill_proficiency_data,
    get_assessment_trends,
    generate_assessment_report_for_user,
)

from .models import (
    ProfileView, JobView, SearchQuery, 
    CompanyAnalyticsSnapshot, PersonalAnalyticsSnapshot,
    SkillAssessmentResult, PredictiveAnalyticsSnapshot,
    SalaryNegotiationInsight, CultureFitAssessment,
    DiversityAnalyticsSnapshot
)
from .pdf_export import AnalyticsPDFExporter
from .utils import get_industry_benchmarks

# Import models from other apps
try:
    from apps.jobs.models import Job
    from apps.applications.models import Application
    from apps.following.models import Follow
except ImportError:
    Job = None
    Application = None
    Follow = None


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Main analytics dashboard - routes to company or personal based on account type."""
    
    template_name = 'analytics/dashboard.html'
    
    def get_template_names(self):
        if self.request.user.account_type == 'company':
            return ['analytics/company_dashboard.html']
        else:
            return ['analytics/personal_dashboard.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.account_type == 'company':
            context.update(self.get_company_analytics())
        else:
            context.update(self.get_personal_analytics())
        
        return context
    
    def get_company_analytics(self):
        """Get analytics for company accounts."""
        user = self.request.user
        company_profile = getattr(user, 'company_profile', None)
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        last_7_days = today - timedelta(days=7)

        context = {
            'overview': {},
            'job_analytics': [],
            'application_funnel': {},
            'screening_analytics': {},
            'trends': {},
            'source_breakdown': {},
            'top_skills': [],
            'skill_gaps': [],
            'drop_off': [],
            'predictive': None,
        }

        if Job is None or Application is None or company_profile is None:
            return context

        snapshot = CompanyAnalyticsSnapshot.objects.filter(company=user).order_by('-date').first()
        source_breakdown = snapshot.applications_by_source if snapshot else {}
        top_skills = snapshot.top_skills if snapshot else []
        skill_gaps = snapshot.skill_gaps if snapshot else []
        cost_per_hire = snapshot.cost_per_hire if snapshot else None
        resumes_screened = snapshot.resumes_screened if snapshot else 0
        predictive = PredictiveAnalyticsSnapshot.objects.filter(company=user).order_by('-date').first()
        if predictive:
            context['predictive'] = {
                'likelihood': predictive.likelihood_to_hire,
                'confidence': predictive.confidence,
                'key_drivers': predictive.key_drivers,
                'notes': predictive.notes,
            }

        total_jobs = Job.objects.filter(company=company_profile).count()
        active_jobs = Job.objects.filter(company=company_profile, status='active').count()
        closed_jobs = Job.objects.filter(company=company_profile, status='closed').count()

        total_applications = Application.objects.filter(job__company=company_profile).count()
        total_hires = Application.objects.filter(
            job__company=company_profile,
            status='hired'
        ).count()

        hired_applications = Application.objects.filter(
            job__company=company_profile,
            status='hired',
            hired_at__isnull=False
        ).annotate(
            time_to_hire=ExpressionWrapper(
                F('hired_at') - F('applied_at'),
                output_field=DurationField()
            )
        )

        avg_time_to_hire = None
        if hired_applications.exists():
            avg_duration = hired_applications.aggregate(
                avg=Avg('time_to_hire')
            )['avg']
            if avg_duration:
                avg_time_to_hire = round(avg_duration.total_seconds() / 86400, 1)

        context['overview'] = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'closed_jobs': closed_jobs,
            'total_applications': total_applications,
            'total_hires': total_hires,
            'avg_time_to_hire': avg_time_to_hire,
            'cost_per_hire': cost_per_hire,
        }

        jobs = Job.objects.filter(company=company_profile).annotate(
            application_count=Count('applications'),
            view_count=Count('views'),
        )

        job_analytics = []
        for job in jobs:
            application_rate = 0
            if job.view_count > 0:
                application_rate = (job.application_count / job.view_count) * 100

            avg_match_score = Application.objects.filter(job=job).aggregate(
                avg_score=Avg('match_score')
            )['avg_score'] or 0

            job_analytics.append({
                'job': job,
                'applications': job.application_count,
                'views': job.view_count,
                'application_rate': round(application_rate, 2),
                'avg_match_score': round(avg_match_score, 2) if avg_match_score else 0,
            })

        context['job_analytics'] = job_analytics

        funnel_data = Application.objects.filter(
            job__company=company_profile
        ).values('status').annotate(count=Count('id'))

        funnel = {
            'pending': 0,
            'screening': 0,
            'interview': 0,
            'offer': 0,
            'hired': 0,
            'rejected': 0,
        }

        for item in funnel_data:
            funnel[item['status']] = item['count']

        total_apps = sum(funnel.values())
        funnel_with_rates = {
            status: {
                'count': count,
                'rate': round((count / total_apps * 100) if total_apps > 0 else 0, 2)
            }
            for status, count in funnel.items()
        }

        context['application_funnel'] = funnel_with_rates
        context['drop_off'] = self.calculate_drop_off(funnel)

        all_applications = Application.objects.filter(job__company=company_profile)
        context['screening_analytics'] = {
            'total_screened': resumes_screened or all_applications.count(),
            'avg_match_score': round(
                all_applications.aggregate(avg=Avg('match_score'))['avg'] or 0,
                2
            ),
            'top_skills': top_skills,
            'skill_gaps': skill_gaps,
        }

        context['source_breakdown'] = source_breakdown
        context['top_skills'] = top_skills
        context['skill_gaps'] = skill_gaps
        context['resumes_screened'] = resumes_screened
        context['cost_per_hire'] = cost_per_hire

        applications_by_date = Application.objects.filter(
            job__company=company_profile,
            applied_at__gte=last_30_days
        ).annotate(
            date=TruncDate('applied_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        date_range = [last_30_days + timedelta(days=x) for x in range(31)]
        applications_trend = []
        date_dict = {item['date']: item['count'] for item in applications_by_date}
        for date in date_range:
            applications_trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': date_dict.get(date, 0)
            })

        hires_per_month = Application.objects.filter(
            job__company=company_profile,
            status='hired',
            hired_at__isnull=False
        ).annotate(
            month=TruncMonth('hired_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        hires_trend = [
            {'label': item['month'].strftime('%b %Y'), 'count': item['count']}
            for item in hires_per_month if item['month']
        ]

        avg_time_by_month = hired_applications.filter(
            hired_at__isnull=False
        ).annotate(
            month=TruncMonth('hired_at')
        ).values('month').annotate(
            avg_duration=Avg('time_to_hire')
        ).order_by('month')

        avg_time_trend = []
        for item in avg_time_by_month:
            month = item.get('month')
            avg_duration = item.get('avg_duration')
            if month and avg_duration:
                avg_time_trend.append({
                    'label': month.strftime('%b %Y'),
                    'avg_days': round(avg_duration.total_seconds() / 86400, 1)
                })

        context['trends'] = {
            'applications_over_time': applications_trend,
            'hires_per_month': hires_trend,
            'avg_time_to_hire': avg_time_trend,
        }

        if Follow:
            context['overview']['followers_count'] = Follow.get_follower_count(user)

        return context
    
    def get_personal_analytics(self):
        """Get analytics for personal accounts."""
        user = self.request.user
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        context = {
            'overview': {},
            'application_status': {},
            'activity': {},
            'profile_analytics': {},
            'skill_assessments': {},
            'recent_assessments': [],
            'skill_badges': [],
        }

        if Application is None:
            return context

        snapshot = PersonalAnalyticsSnapshot.objects.filter(user=user).order_by('-date').first()
        applications = Application.objects.filter(applicant=user)

        total_applications = applications.count()
        status_counts = applications.values('status').annotate(count=Count('id'))
        status_breakdown = {
            'pending': 0,
            'screening': 0,
            'interview': 0,
            'offer': 0,
            'hired': 0,
            'rejected': 0,
        }
        for item in status_counts:
            status_breakdown[item['status']] = item['count']

        success_rate = 0
        if total_applications > 0:
            offers = status_breakdown['offer'] + status_breakdown['hired']
            success_rate = (offers / total_applications) * 100

        applications_with_response = applications.filter(
            status_changed_at__gt=F('applied_at'),
            status_changed_at__isnull=False
        ).annotate(
            response_time=ExpressionWrapper(
                F('status_changed_at') - F('applied_at'),
                output_field=DurationField()
            )
        )

        avg_response_time = None
        if applications_with_response.exists():
            avg_duration = applications_with_response.aggregate(avg=Avg('response_time'))['avg']
            if avg_duration:
                avg_response_time = round(avg_duration.total_seconds() / 86400, 1)

        avg_match_score = applications.aggregate(avg=Avg('match_score'))['avg'] or 0

        context['overview'] = {
            'total_applications': total_applications,
            'success_rate': round(success_rate, 2),
            'avg_response_time': avg_response_time,
            'avg_match_score': round(avg_match_score, 2),
        }
        if snapshot:
            context['overview']['success_rate'] = round(success_rate, 2)
            context['overview']['avg_match_score'] = round(snapshot.avg_match_score or context['overview']['avg_match_score'], 2)

        context['application_status'] = status_breakdown

        jobs_viewed = snapshot.jobs_viewed_count if snapshot else JobView.objects.filter(
            viewer=user,
            viewed_at__gte=last_30_days
        ).count()
        jobs_saved = snapshot.jobs_saved_count if snapshot else (user.saved_jobs.count() if hasattr(user, 'saved_jobs') else 0)
        searches_performed = snapshot.searches_performed if snapshot else SearchQuery.objects.filter(
            user=user,
            searched_at__gte=last_30_days
        ).count()

        context['activity'] = {
            'jobs_viewed': jobs_viewed,
            'jobs_saved': jobs_saved,
            'searches_performed': searches_performed,
        }

        profile_views = snapshot.profile_views_count if snapshot else ProfileView.objects.filter(
            profile_owner=user,
            viewed_at__gte=last_30_days
        ).count()
        profile_completion = self.calculate_profile_completion(user)
        recent_viewers = ProfileView.objects.filter(
            profile_owner=user
        ).select_related('viewer')[:10]

        context['profile_analytics'] = {
            'views_count': profile_views,
            'recent_viewers': recent_viewers,
            'completion_score': profile_completion,
        }

        assessments = SkillAssessmentResult.objects.filter(user=user).order_by('-taken_at')
        context['recent_assessments'] = assessments[:5]
        badges = snapshot.badges_earned if snapshot else [
            badge for badge in assessments.values_list('badge_awarded', flat=True).distinct() if badge
        ]
        context['skill_badges'] = badges
        context['skill_assessments'] = {
            'taken': snapshot.skill_assessments_taken if snapshot else assessments.count(),
            'avg_score': snapshot.avg_skill_assessment_score if snapshot else (assessments.aggregate(avg=Avg('score'))['avg'] or 0),
        }

        return context

    def calculate_drop_off(self, funnel):
        """Estimate drop-off counts between pipeline stages."""
        stage_order = ['pending', 'screening', 'interview', 'offer', 'hired']
        drop_off = []
        prev_count = funnel.get(stage_order[0], 0)

        for idx in range(1, len(stage_order)):
            stage = stage_order[idx]
            current = funnel.get(stage, 0)
            drop = max(prev_count - current, 0)
            drop_off.append({
                'from': stage_order[idx - 1],
                'to': stage,
                'drop': drop,
                'rate': round((drop / prev_count * 100) if prev_count > 0 else 0, 2)
            })
            prev_count = current

        return drop_off
    
    def calculate_profile_completion(self, user):
        """Calculate profile completion percentage."""
        # This is a basic implementation
        # You should adjust based on your PersonalProfile model
        score = 0
        
        try:
            profile = user.personalprofile
            
            # Basic info (30%)
            if profile.full_name:
                score += 10
            if profile.phone:
                score += 10
            if profile.location:
                score += 10
            
            # Professional info (40%)
            if profile.headline:
                score += 10
            if profile.bio:
                score += 10
            if profile.skills:
                score += 10
            if profile.experience:
                score += 10
            
            # Additional info (30%)
            if profile.education:
                score += 10
            if profile.certifications:
                score += 10
            if profile.resume_primary_id:
                score += 10
        except:
            pass
        
        return score



class SkillProficiencyDashboard(LoginRequiredMixin, TemplateView):
    """Dashboard focused on skill proficiency and assessment insights."""

    template_name = 'analytics/skill_proficiency.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        proficiency_data = get_skill_proficiency_data(user)
        trends = get_assessment_trends(user, days=90)
        report = generate_assessment_report_for_user(user)

        default_report = {
            'total_attempts': 0,
            'total_passed': 0,
            'pass_rate': 0,
            'total_badges': 0,
            'average_score': 0,
            'total_time_spent': 0,
            'skills_tested': 0,
            'recent_activity': [],
            'top_skills': [],
        }

        context.update({
            'proficiency_data': proficiency_data,
            'trends': trends,
            'report': report or default_report,
        })

        return context


class JobAnalyticsDetailView(LoginRequiredMixin, TemplateView):
    """Detailed analytics for a specific job."""
    
    template_name = 'analytics/job_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_id = kwargs.get('job_id')
        
        if Job is None or Application is None:
            return context
        
        company = getattr(self.request.user, 'company_profile', None)
        if not company:
            return context

        try:
            job = Job.objects.get(id=job_id, company=company)
        except Job.DoesNotExist:
            return context
        
        # Application breakdown
        applications = Application.objects.filter(job=job)
        
        context['job'] = job
        context['total_applications'] = applications.count()
        
        # Status breakdown
        status_data = applications.values('status').annotate(
            count=Count('id')
        )
        context['status_breakdown'] = {
            item['status']: item['count'] for item in status_data
        }
        
        # Match score distribution
        score_ranges = {
            '0-20': applications.filter(match_score__lt=20).count(),
            '20-40': applications.filter(match_score__gte=20, match_score__lt=40).count(),
            '40-60': applications.filter(match_score__gte=40, match_score__lt=60).count(),
            '60-80': applications.filter(match_score__gte=60, match_score__lt=80).count(),
            '80-100': applications.filter(match_score__gte=80).count(),
        }
        context['score_distribution'] = score_ranges
        
        # Views and application rate
        total_views = JobView.objects.filter(job=job).count()
        context['total_views'] = total_views
        context['application_rate'] = (
            (applications.count() / total_views * 100) if total_views > 0 else 0
        )
        
        return context


class ExportAnalyticsView(LoginRequiredMixin, View):
    """Export analytics data to CSV."""
    
    def get(self, request, *args, **kwargs):
        export_type = request.GET.get('type', 'overview')
        export_format = request.GET.get('format', 'csv')
        
        if request.user.account_type == 'company':
            return self.export_company_analytics(export_type, export_format)
        else:
            return self.export_personal_analytics(export_type, export_format)
    
    def export_company_analytics(self, export_type, export_format):
        """Export company analytics to CSV."""
        if export_format == 'pdf':
            return self.export_company_pdf(export_type)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        
        company_profile = getattr(self.request.user, 'company_profile', None)
        if company_profile is None:
            return response

        if export_type == 'jobs' and Job:
            writer.writerow(['Job Title', 'Status', 'Applications', 'Views', 'Application Rate', 'Avg Match Score'])
            
            jobs = Job.objects.filter(company=company_profile).annotate(
                application_count=Count('applications'),
                view_count=Count('views'),
                avg_match=Avg('applications__match_score')
            )
            
            for job in jobs:
                app_rate = (job.application_count / job.view_count * 100) if job.view_count > 0 else 0
                writer.writerow([
                    job.title,
                    job.status,
                    job.application_count,
                    job.view_count,
                    f"{app_rate:.2f}%",
                    f"{job.avg_match:.2f}" if job.avg_match else "0"
                ])

        elif export_type == 'applications' and Application:
            writer.writerow(['Applicant', 'Job', 'Status', 'Match Score', 'Applied At'])
            
            applications = Application.objects.filter(
                job__company=company_profile
            ).select_related('user', 'job')
            
            for app in applications:
                writer.writerow([
                    app.user.email,
                    app.job.title,
                    app.status,
                    app.match_score,
                    app.applied_at.strftime('%Y-%m-%d %H:%M')
                ])
        
        return response
    
    def export_personal_analytics(self, export_type, export_format):
        """Export personal analytics to CSV."""
        if export_format == 'pdf':
            return self.export_personal_pdf(export_type)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="my_analytics_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        
        if Application:
            writer.writerow(['Job Title', 'Company', 'Status', 'Match Score', 'Applied At'])
            
            applications = Application.objects.filter(
                user=self.request.user
            ).select_related('job', 'job__company')
            
            for app in applications:
                company_name = getattr(
                    app.job.company.companyprofile, 
                    'company_name', 
                    app.job.company.email
                ) if hasattr(app.job.company, 'companyprofile') else app.job.company.email
                
                writer.writerow([
                    app.job.title,
                    company_name,
                    app.status,
                    app.match_score,
                    app.applied_at.strftime('%Y-%m-%d %H:%M')
                ])
        
        return response

    def export_company_pdf(self, export_type):
        """Export company analytics to PDF."""
        company = getattr(self.request.user, 'company_profile', None)
        if company is None:
            return HttpResponse(status=404)

        snapshot = CompanyAnalyticsSnapshot.objects.filter(company=self.request.user).order_by('-date').first()
        overview = {
            'total_applications': snapshot.total_applications if snapshot else 0,
            'total_hires': snapshot.total_hires if snapshot else 0,
            'avg_time_to_hire': snapshot.avg_time_to_hire if snapshot else None,
            'cost_per_hire': snapshot.cost_per_hire if snapshot else None,
        }
        details = {
            'source_breakdown': snapshot.applications_by_source if snapshot else {},
            'top_skills': snapshot.top_skills if snapshot else [],
            'skill_gaps': snapshot.skill_gaps if snapshot else [],
        }
        buffer = AnalyticsPDFExporter(
            user=self.request.user,
            overview=overview,
            details=details,
            report_type='Company'
        ).generate()

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics_company_{timezone.now().date()}.pdf"'
        return response

    def export_personal_pdf(self, export_type):
        """Export personal analytics to PDF."""
        snapshot = PersonalAnalyticsSnapshot.objects.filter(user=self.request.user).order_by('-date').first()
        overview = {
            'total_applications': snapshot.total_applications if snapshot else 0,
            'success_rate': snapshot.response_rate if snapshot else 0,
            'avg_match_score': snapshot.avg_match_score if snapshot else 0,
        }
        buffer = AnalyticsPDFExporter(
            user=self.request.user,
            overview=overview,
            details={},
            report_type='Personal'
        ).generate()
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics_personal_{timezone.now().date()}.pdf"'
        return response


class AnalyticsAPIView(LoginRequiredMixin, View):
    """API endpoint for fetching analytics data via AJAX."""
    
    def get(self, request, *args, **kwargs):
        metric = request.GET.get('metric')
        
        if request.user.account_type == 'company':
            data = self.get_company_metric(metric)
        else:
            data = self.get_personal_metric(metric)
        
        return JsonResponse(data)
    
    def get_company_metric(self, metric):
        """Get specific company metric."""
        user = self.request.user
        company_profile = getattr(user, 'company_profile', None)
        if company_profile is None:
            return {'error': 'Company profile missing'}
        company_user = user

        if metric == 'applications_trend' and Application:
            last_30_days = timezone.now().date() - timedelta(days=30)
            
            data = Application.objects.filter(
                job__company=company_profile,
                applied_at__gte=last_30_days
            ).annotate(
                date=TruncDate('applied_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            return {
                'labels': [item['date'].strftime('%Y-%m-%d') for item in data],
                'values': [item['count'] for item in data]
            }
        if metric == 'hires_trend' and Application:
            hires = Application.objects.filter(
                job__company=company_profile,
                status='hired',
                hired_at__isnull=False
            ).annotate(
                month=TruncMonth('hired_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')

            return {
                'labels': [item['month'].strftime('%b %Y') for item in hires if item['month']],
                'values': [item['count'] for item in hires if item['month']]
            }
        if metric == 'time_to_hire_trend' and Application:
            hired_qs = Application.objects.filter(
                job__company=company_profile,
                status='hired',
                hired_at__isnull=False
            ).annotate(
                month=TruncMonth('hired_at'),
                duration=ExpressionWrapper(F('hired_at') - F('applied_at'), output_field=DurationField())
            ).values('month').annotate(avg=Avg('duration')).order_by('month')

            return {
                'labels': [item['month'].strftime('%b %Y') for item in hired_qs if item['month']],
                'values': [
                    round(item['avg'].total_seconds() / 86400, 1) if item['avg'] else 0
                    for item in hired_qs if item['month']
                ]
            }
        if metric == 'source_breakdown':
            snapshot = CompanyAnalyticsSnapshot.objects.filter(company=company_user).order_by('-date').first()
            return {
                'data': snapshot.applications_by_source if snapshot else {}
            }
        
        return {'error': 'Invalid metric'}
    def get_personal_metric(self, metric):
        """Get specific personal metric."""
        user = self.request.user
        
        if metric == 'application_status' and Application:
            data = Application.objects.filter(
                user=user
            ).values('status').annotate(count=Count('id'))
            
            return {
                'labels': [item['status'].title() for item in data],
                'values': [item['count'] for item in data]
            }
        if metric == 'salary_insight':
            insight = SalaryNegotiationInsight.objects.filter(user=user).order_by('-generated_at').first()
            if insight:
                return {
                    'salary_floor': insight.salary_floor,
                    'salary_ceiling': insight.salary_ceiling,
                    'market_rate': insight.market_rate,
                    'confidence': insight.confidence_score,
                }
            return {}
        if metric == 'culture_fit':
            assessment = CultureFitAssessment.objects.filter(user=user).order_by('-assessed_at').first()
            if assessment:
                return {
                    'score': assessment.score,
                    'highlights': assessment.highlights,
                }
            return {}
        if metric == 'diversity' and request.user.account_type == 'company':
            company_profile = getattr(user, 'company_profile', None)
            if not company_profile:
                return {}
            snapshot = DiversityAnalyticsSnapshot.objects.filter(company=user).order_by('-date').first()
            if snapshot:
                return {
                    'female_ratio': snapshot.female_ratio,
                    'underrepresented_ratio': snapshot.underrepresented_ratio,
                    'inclusive_score': snapshot.inclusive_score,
                }
            return {}
        if metric == 'assessments':
            assessments = SkillAssessmentResult.objects.filter(user=user).order_by('-taken_at')[:5]
            return {
                'items': [
                    {
                        'test': assessment.test_name,
                        'score': assessment.score,
                        'badge': assessment.badge_awarded,
                        'taken_at': assessment.taken_at.strftime('%Y-%m-%d')
                    }
                    for assessment in assessments
                ]
            }
        
        return {'error': 'Invalid metric'}


class AnalyticsReportBuilderView(LoginRequiredMixin, TemplateView):
    """Custom report builder for analytics data."""

    template_name = 'analytics/report_builder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        days = int(self.request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        end_date = timezone.now().date()

        context['report_days'] = days
        context['report_scope'] = user.account_type

        if user.account_type == 'company':
            context['report'] = self.build_company_report(user, start_date, end_date)
            context['benchmarks'] = get_industry_benchmarks(user, window_days=days)
        else:
            context['report'] = self.build_personal_report(user, start_date, end_date)
            context['benchmarks'] = {}

        return context

    def build_company_report(self, user, start_date, end_date):
        company_profile = getattr(user, 'company_profile', None)
        if company_profile is None:
            return {'has_data': False, 'message': 'Company profile not configured.'}

        snapshots = CompanyAnalyticsSnapshot.objects.filter(
            company=user,
            date__range=(start_date, end_date)
        ).order_by('date')

        if not snapshots.exists():
            return {'has_data': False, 'message': 'No analytics snapshots in the selected range.'}

        earliest = snapshots.first()
        latest = snapshots.last()

        return {
            'has_data': True,
            'start_date': start_date,
            'end_date': end_date,
            'total_applications': latest.total_applications,
            'new_applications': latest.total_applications - earliest.total_applications,
            'total_hires': latest.total_hires,
            'new_hires': latest.total_hires - earliest.total_hires,
            'avg_time_to_hire': latest.avg_time_to_hire,
            'followers_count': latest.followers_count,
        }

    def build_personal_report(self, user, start_date, end_date):
        snapshots = PersonalAnalyticsSnapshot.objects.filter(
            user=user,
            date__range=(start_date, end_date)
        ).order_by('date')

        applications = Application.objects.filter(
            user=user,
            applied_at__date__range=(start_date, end_date)
        )
        total_applications = applications.count()
        avg_match_score = applications.aggregate(avg=Avg('match_score'))['avg'] or 0

        return {
            'has_data': snapshots.exists(),
            'start_date': start_date,
            'end_date': end_date,
            'total_applications': total_applications,
            'avg_match_score': avg_match_score,
            'success_rate': snapshots.last().response_rate if snapshots.exists() else 0,
            'profile_views': snapshots.last().profile_views_count if snapshots.exists() else 0,
        }


class AnalyticsDataExportView(LoginRequiredMixin, View):
    """Export analytics data via API."""

    def get(self, request, *args, **kwargs):
        data_format = request.GET.get('format', 'json')
        start_date = self._parse_date(request.GET.get('start')) or (timezone.now().date() - timedelta(days=30))
        end_date = self._parse_date(request.GET.get('end')) or timezone.now().date()

        if request.user.account_type == 'company':
            data = self._collect_company_data(request.user, start_date, end_date)
        else:
            data = self._collect_personal_data(request.user, start_date, end_date)

        if data_format == 'csv':
            return self._as_csv(data, request.user.account_type)

        return JsonResponse(data, safe=False)

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None

    def _collect_company_data(self, user, start_date, end_date):
        company_profile = getattr(user, 'company_profile', None)
        if company_profile is None:
            return []

        snapshots = CompanyAnalyticsSnapshot.objects.filter(
            company=user,
            date__range=(start_date, end_date)
        ).order_by('date')
        return [
            {
                'date': snapshot.date.isoformat(),
                'total_applications': snapshot.total_applications,
                'total_hires': snapshot.total_hires,
                'avg_time_to_hire': snapshot.avg_time_to_hire,
                'cost_per_hire': snapshot.cost_per_hire,
            }
            for snapshot in snapshots
        ]

    def _collect_personal_data(self, user, start_date, end_date):
        snapshots = PersonalAnalyticsSnapshot.objects.filter(
            user=user,
            date__range=(start_date, end_date)
        ).order_by('date')
        return [
            {
                'date': snapshot.date.isoformat(),
                'total_applications': snapshot.total_applications,
                'applications_hired': snapshot.applications_hired,
                'profile_views': snapshot.profile_views_count,
                'avg_match_score': snapshot.avg_match_score,
                'response_rate': snapshot.response_rate,
            }
            for snapshot in snapshots
        ]

    def _as_csv(self, data, account_type):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_export_{account_type}_{timezone.now().date()}.csv"'
        writer = csv.writer(response)

        if not data:
            writer.writerow(['message'])
            writer.writerow(['No data for the selected range.'])
            return response

        headers = list(data[0].keys())
        writer.writerow(headers)
        for row in data:
            writer.writerow([row.get(col) for col in headers])

        return response
