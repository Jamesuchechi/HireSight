from django.contrib import admin
from .models import Interview


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'interview_type', 'status', 'scheduled_date', 'interviewer_name')
    list_filter = ('status', 'interview_type')
    search_fields = ('application__applicant__email', 'interviewer_name', 'application__job__title')
