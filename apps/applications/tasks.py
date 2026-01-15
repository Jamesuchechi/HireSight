"""
Celery tasks for application processing.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import ApplicationStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_application_confirmation_email(self, application_id):
    """
    Send confirmation email to applicant after successful application.

    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application

        application = Application.objects.select_related(
            'job',
            'job__company',
            'applicant',
            'applicant__personal_profile'
        ).get(id=application_id)
        
        # Render email template
        subject = f"Application Received - {application.job.title}"
        
        html_message = render_to_string('applications/emails/application_confirmation.html', {
            'applicant_name': application.applicant.personal_profile.full_name if hasattr(application.applicant, 'personal_profile') else application.applicant.email,
            'job_title': application.job.title,
            'company_name': application.job.company.company_name,
            'application': application,
            'applied_at': application.applied_at,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Thank you for applying to {application.job.title}",  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Confirmation email sent for application {application_id}")
        return f"Email sent successfully to {application.applicant.email}"
        
    except Exception as exc:
        logger.error(f"Error sending confirmation email for application {application_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds


@shared_task(bind=True, max_retries=3)
def calculate_application_match_score(self, application_id):
    """
    Calculate match score for an application.
    
    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application
        from apps.screening.ai_matcher import ai_screener
        from apps.resumes.parsers import ResumeParser
        from django.core.files.storage import default_storage
        
        application = Application.objects.select_related(
            'job',
            'applicant',
            'resume'
        ).get(id=application_id)
        
        # Only calculate if not already done
        if application.match_score is not None:
            logger.info(f"Match score already calculated for application {application_id}")
            return f"Match score already exists: {application.match_score}%"
        
        # Check if application has a resume
        if not application.resume or not application.resume.file:
            logger.warning(f"No resume file for application {application_id}")
            return "No resume file attached"
        
        # Get job description
        job_description = application.job.description or f"Position: {application.job.title}"
        
        # Extract resume text
        try:
            parser = ResumeParser()
            # Get the file path from storage
            file_path = application.resume.file.path if hasattr(application.resume.file, 'path') else str(application.resume.file)
            resume_text = parser._extract_text(file_path, application.resume.file.name)
            logger.info(f"Resume text extracted for application {application_id}")
        except Exception as e:
            logger.error(f"Error extracting resume text: {e}")
            return f"Failed to extract resume text: {str(e)}"
        
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning(f"Resume text too short for application {application_id}")
            return "Resume text is empty or too short"
        
        # Get job requirements
        job_requirements = application.job.requirements or []
        if isinstance(job_requirements, str):
            # Parse requirements if stored as string
            required_skills = [skill.strip() for skill in job_requirements.split(',')][:10]
        else:
            required_skills = job_requirements[:10] if job_requirements else []
        
        # Build criteria for match calculation
        criteria = {
            'required_skills': required_skills,
            'nice_to_have_skills': [],
            'min_experience_years': 0,
            'max_experience_years': None,
            'required_education': [],
            'custom_keywords': [],
            'weight_skills': 0.5,
            'weight_experience': 0.3,
            'weight_education': 0.2,
            'weight_keywords': 0,
        }
        
        # Calculate match score
        try:
            match_result = ai_screener.calculate_match_score(
                resume_text=resume_text,
                job_description=job_description,
                criteria=criteria
            )
            
            application.match_score = int(match_result['match_score'])
            application.match_details = match_result['match_details']
            application.save(update_fields=['match_score', 'match_details'])
            
            logger.info(f"Match score calculated for application {application_id}: {application.match_score}%")
            return f"Match score calculated: {application.match_score}%"
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}", exc_info=True)
            return f"Failed to calculate match score: {str(e)}"
        
    except Application.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return f"Application not found"
    except Exception as exc:
        logger.error(f"Error in match score calculation: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds



@shared_task(bind=True, max_retries=3)
def send_new_application_notification_to_company(self, application_id):
    """
    Send notification email to company when new application is received.
    
    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application
        
        application = Application.objects.select_related(
            'job',
            'job__company',
            'job__company__user',
            'applicant',
            'applicant__personal_profile'
        ).get(id=application_id)
        
        # Get company user email
        company_email = application.job.company.user.email
        
        # Render email template
        subject = f"New Application for {application.job.title}"
        
        html_message = render_to_string('applications/emails/new_application_company.html', {
            'company_name': application.job.company.company_name,
            'job_title': application.job.title,
            'applicant_name': application.applicant.personal_profile.full_name if hasattr(application.applicant, 'personal_profile') else 'A candidate',
            'application': application,
            'match_score': application.match_score,
            'applied_at': application.applied_at,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=f"You have received a new application for {application.job.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[company_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Company notification email sent for application {application_id}")
        return f"Email sent successfully to {company_email}"
        
    except Exception as exc:
        logger.error(f"Error sending company notification for application {application_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_status_update_email(self, application_id):
    """
    Send email notification when application status changes.

    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application

        application = Application.objects.select_related(
            'job',
            'job__company',
            'applicant',
            'applicant__personal_profile'
        ).get(id=application_id)
        
        # Don't send email for pending status (already sent confirmation)
        if application.status == 'pending':
            return "Skipped - pending status"
        
        # Get status-specific subject and template
        status_config = {
            'screening': {
                'subject': f"Your application is under review - {application.job.title}",
                'template': 'applications/emails/status_screening.html',
            },
            'interview': {
                'subject': f"Interview invitation - {application.job.title}",
                'template': 'applications/emails/status_interview.html',
            },
            'offer': {
                'subject': f"Job offer - {application.job.title}",
                'template': 'applications/emails/status_offer.html',
            },
            'hired': {
                'subject': f"Congratulations! - {application.job.title}",
                'template': 'applications/emails/status_hired.html',
            },
            'rejected': {
                'subject': f"Application update - {application.job.title}",
                'template': 'applications/emails/status_rejected.html',
            },
        }
        
        config = status_config.get(application.status)
        if not config:
            return f"Skipped - no email template for status {application.status}"
        
        # Render email template
        html_message = render_to_string(config['template'], {
            'applicant_name': application.applicant.personal_profile.full_name if hasattr(application.applicant, 'personal_profile') else application.applicant.email,
            'job_title': application.job.title,
            'company_name': application.job.company.company_name,
            'application': application,
            'status': application.get_status_display(),
            'rejection_feedback': application.rejection_feedback if hasattr(application, 'rejection_feedback') and application.rejection_feedback else None,
        })
        
        # Send email
        send_mail(
            subject=config['subject'],
            message=f"Your application status has been updated to: {application.get_status_display()}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Status update email sent for application {application_id}")
        return f"Email sent successfully to {application.applicant.email}"
        
    except Exception as exc:
        logger.error(f"Error sending status update email for application {application_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_withdrawal_notification_email(self, application_id):
    """
    Send email notification to company when applicant withdraws their application.

    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application

        application = Application.objects.select_related(
            'job',
            'job__company',
            'job__company__user',
            'applicant',
            'applicant__personal_profile'
        ).get(id=application_id)

        # Get withdrawal reason from status history
        withdrawal_reason = ""
        try:
            latest_history = application.status_history.filter(
                new_status=ApplicationStatus.WITHDRAWN
            ).order_by('-changed_at').first()
            if latest_history:
                withdrawal_reason = latest_history.reason
        except:
            withdrawal_reason = ""

        # Get company user email
        company_email = application.job.company.user.email

        # Render email template
        subject = f"Application Withdrawn - {application.job.title}"

        html_message = render_to_string('applications/emails/withdrawal_notification.html', {
            'applicant_name': application.applicant.personal_profile.full_name if hasattr(application.applicant, 'personal_profile') else application.applicant.email,
            'job_title': application.job.title,
            'company_name': application.job.company.company_name,
            'application': application,
            'withdrawn_at': application.withdrawn_at,
            'withdrawal_reason': withdrawal_reason,
        })

        # Send email
        send_mail(
            subject=subject,
            message=f"An applicant has withdrawn their application for {application.job.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[company_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Withdrawal notification email sent for application {application_id}")
        return f"Email sent successfully to {company_email}"

    except Exception as exc:
        logger.error(f"Error sending withdrawal notification for application {application_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_interview_invitation_email(self, application_id, interview_details):
    """
    Send interview invitation email with schedule details.
    
    Args:
        application_id: UUID of the application
        interview_details: Dict with interview information (date, time, location, etc.)
    """
    try:
        from .models import Application
        
        application = Application.objects.select_related(
            'job',
            'job__company',
            'applicant',
            'applicant__personal_profile'
        ).get(id=application_id)
        
        # Render email template
        subject = f"Interview Invitation - {application.job.title}"
        
        html_message = render_to_string('applications/emails/interview_invitation.html', {
            'applicant_name': application.applicant.personal_profile.full_name if hasattr(application.applicant, 'personal_profile') else application.applicant.email,
            'job_title': application.job.title,
            'company_name': application.job.company.company_name,
            'application': application,
            'interview_details': interview_details,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=f"You have been invited to interview for {application.job.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Interview invitation email sent for application {application_id}")
        return f"Email sent successfully to {application.applicant.email}"
        
    except Exception as exc:
        logger.error(f"Error sending interview invitation for application {application_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def create_application_notification(application_id):
    """
    Create in-app notification for new application.
    
    Args:
        application_id: UUID of the application
    """
    try:
        from .models import Application
        from apps.notifications.models import Notification
        
        application = Application.objects.select_related(
            'job',
            'job__company',
            'job__company__user',
            'applicant'
        ).get(id=application_id)
        
        # Create notification for company
        Notification.objects.create(
            user=application.job.company.user,
            title="New Application Received",
            message=f"New application for {application.job.title}",
            notification_type='application',
            action_url=f"{settings.SITE_URL}/applications/applicants/{application.id}/",
            action_text="View Application",
            related_object_id=str(application.id)
        )
        
        logger.info(f"Notification created for application {application_id}")
        return "Notification created successfully"
        
    except Exception as exc:
        logger.error(f"Error creating notification for application {application_id}: {str(exc)}")
        return f"Error: {str(exc)}"


@shared_task
def update_application_analytics():
    """
    Periodic task to update application analytics.
    
    Runs daily to aggregate application statistics.
    """
    try:
        from .models import Application, ApplicationStatus
        from apps.analytics.models import ApplicationAnalytics
        from django.db.models import Count, Avg
        
        # Calculate daily statistics
        today = timezone.now().date()
        
        stats = Application.objects.filter(
            applied_at__date=today
        ).aggregate(
            total=Count('id'),
            avg_match_score=Avg('match_score'),
            pending=Count('id', filter=Q(status=ApplicationStatus.PENDING)),
            screening=Count('id', filter=Q(status=ApplicationStatus.SCREENING)),
            interview=Count('id', filter=Q(status=ApplicationStatus.INTERVIEW)),
            offer=Count('id', filter=Q(status=ApplicationStatus.OFFER)),
            hired=Count('id', filter=Q(status=ApplicationStatus.HIRED)),
            rejected=Count('id', filter=Q(status=ApplicationStatus.REJECTED)),
        )
        
        # Store analytics
        ApplicationAnalytics.objects.create(
            date=today,
            **stats
        )
        
        logger.info(f"Application analytics updated for {today}")
        return f"Analytics updated for {today}"
        
    except Exception as exc:
        logger.error(f"Error updating application analytics: {str(exc)}")
        return f"Error: {str(exc)}"


@shared_task
def cleanup_old_applications():
    """
    Periodic task to clean up old withdrawn/rejected applications.
    
    Runs weekly to delete applications older than 1 year.
    """
    try:
        from .models import Application, ApplicationStatus
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=365)
        
        # Delete old withdrawn/rejected applications
        deleted_count = Application.objects.filter(
            status__in=[ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED],
            applied_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old applications")
        return f"Deleted {deleted_count} old applications"
        
    except Exception as exc:
        logger.error(f"Error cleaning up old applications: {str(exc)}")
        return f"Error: {str(exc)}"


@shared_task(bind=True, max_retries=3)
def generate_application_report(self, job_id):
    """
    Generate application report for a specific job.
    
    Args:
        job_id: UUID of the job
    """
    try:
        from .models import Application
        from apps.jobs.models import Job
        from django.db.models import Count, Avg
        import json
        
        job = Job.objects.select_related('company').get(id=job_id)
        
        # Get applications for this job
        applications = Application.objects.filter(job=job)
        
        # Calculate statistics
        stats = applications.aggregate(
            total=Count('id'),
            avg_match_score=Avg('match_score'),
            shortlisted=Count('id', filter=Q(is_shortlisted=True)),
        )
        
        # Status breakdown
        status_breakdown = {
            status.value: applications.filter(status=status).count()
            for status in ApplicationStatus
        }
        
        # Top candidates
        top_candidates = applications.order_by('-match_score')[:10].values(
            'id', 'applicant__email', 'match_score', 'status'
        )
        
        # Generate report
        report = {
            'job_id': str(job_id),
            'job_title': job.title,
            'company': job.company.company_name,
            'generated_at': timezone.now().isoformat(),
            'statistics': stats,
            'status_breakdown': status_breakdown,
            'top_candidates': list(top_candidates),
        }
        
        logger.info(f"Application report generated for job {job_id}")
        return json.dumps(report, default=str)
        
    except Exception as exc:
        logger.error(f"Error generating application report for job {job_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
