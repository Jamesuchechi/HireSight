from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Interview
from .forms import InterviewScheduleForm, InterviewRescheduleForm, InterviewCancelForm
from .tasks import send_interview_invitation, send_interview_cancellation
from apps.applications.models import Application, ApplicationStatus


@login_required
def schedule_interview(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    if request.user != application.job.company.user:
        messages.error(request, "You don't have permission to schedule this interview.")
        return redirect('applications:detail', pk=application_id)

    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()

            application.status = ApplicationStatus.INTERVIEW
            application.save(update_fields=['status'])

            send_interview_invitation.delay(interview.id)

            messages.success(request, "Interview scheduled successfully.")
            return redirect('applications:detail', pk=application_id)
    else:
        initial_data = {
            'interviewer_name': request.user.get_full_name() or request.user.email,
            'interviewer_email': request.user.email,
        }
        form = InterviewScheduleForm(initial=initial_data)

    return render(request, 'interviews/schedule_form.html', {
        'form': form,
        'application': application,
    })


@login_required
def upcoming_interviews(request):
    now = timezone.now()
    if request.user.account_type == 'company':
        interviews = Interview.objects.filter(
            application__job__company__user=request.user,
            scheduled_date__gte=now,
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED]
        ).select_related('application__applicant', 'application__job__company')
    else:
        interviews = Interview.objects.filter(
            application__applicant=request.user,
            scheduled_date__gte=now,
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED]
        ).select_related('application__job__company')

    return render(request, 'interviews/upcoming_list.html', {
        'interviews': interviews,
    })


@login_required
def reschedule_interview(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    is_company = request.user == interview.application.job.company.user
    is_candidate = request.user == interview.application.applicant

    if not (is_company or is_candidate):
        messages.error(request, "You don't have permission to reschedule this interview.")
        return redirect('dashboard:dashboard_home')

    if not interview.can_reschedule():
        messages.error(request, "This interview cannot be rescheduled.")
        return redirect('interviews:upcoming')

    if request.method == 'POST':
        form = InterviewRescheduleForm(request.POST)
        if form.is_valid():
            if not interview.original_scheduled_date:
                interview.original_scheduled_date = interview.scheduled_date
            interview.scheduled_date = form.cleaned_data['new_scheduled_date']
            interview.status = Interview.InterviewStatus.RESCHEDULED
            interview.reschedule_count += 1
            interview.reminder_24h_sent = False
            interview.reminder_1h_sent = False
            interview.save()

            send_interview_invitation.delay(interview.id, is_reschedule=True)

            messages.success(request, "Interview rescheduled successfully.")
            return redirect('interviews:upcoming')
    else:
        form = InterviewRescheduleForm()

    return render(request, 'interviews/reschedule_form.html', {
        'form': form,
        'interview': interview,
    })


@login_required
def cancel_interview(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    is_company = request.user == interview.application.job.company.user
    is_candidate = request.user == interview.application.applicant

    if not (is_company or is_candidate):
        messages.error(request, "You don't have permission to cancel this interview.")
        return redirect('dashboard:dashboard_home')

    if request.method == 'POST':
        form = InterviewCancelForm(request.POST)
        if form.is_valid():
            interview.status = Interview.InterviewStatus.CANCELLED
            interview.cancelled_by = request.user
            interview.cancellation_reason = form.cleaned_data['reason']
            interview.save()

            send_interview_cancellation.delay(interview.id)

            messages.success(request, "Interview cancelled.")
            return redirect('applications:detail', pk=interview.application.id)
    else:
        form = InterviewCancelForm()

    return render(request, 'interviews/cancel_form.html', {
        'form': form,
        'interview': interview,
    })


@login_required
def mark_interview_completed(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)

    if request.user != interview.application.job.company.user:
        messages.error(request, "Only the company can mark this interview as completed.")
        return redirect('interviews:upcoming')

    if request.method == 'POST':
        interview.status = Interview.InterviewStatus.COMPLETED
        interview.completion_notes = request.POST.get('completion_notes', '')
        interview.save(update_fields=['status', 'completion_notes'])
        messages.success(request, "Interview marked as completed.")
        return redirect('interviews:upcoming')

    return render(request, 'interviews/complete_form.html', {
        'interview': interview,
    })
