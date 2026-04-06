from rest_framework import serializers
from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview model
    Used for API endpoints
    """
    
    application_id = serializers.UUIDField(source='application.id', read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    company_name = serializers.CharField(source='application.job.company.company_name', read_only=True)
    candidate_email = serializers.EmailField(source='application.applicant.email', read_only=True)
    candidate_name = serializers.SerializerMethodField()
    
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    end_time = serializers.DateTimeField(source='get_end_time', read_only=True)
    duration_display = serializers.CharField(source='duration_display', read_only=True)
    
    can_reschedule = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_mark_completed = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    all_interviewers = serializers.SerializerMethodField()
    calendar_url = serializers.URLField(source='get_calendar_event_url', read_only=True)
    feedback_template = serializers.CharField(source='feedback_template.name', read_only=True)
    feedback_template_id = serializers.UUIDField(source='feedback_template.id', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id',
            'application_id',
            'job_title',
            'company_name',
            'candidate_email',
            'candidate_name',
            'interview_type',
            'interview_type_display',
            'status',
            'status_display',
            'scheduled_date',
            'end_time',
            'duration_minutes',
            'duration_display',
            'timezone_name',
            'location',
            'video_link',
            'dial_in_number',
            'interviewer_name',
            'interviewer_email',
            'additional_interviewers',
            'all_interviewers',
            'candidate_instructions',
            'company_notes',
            'completion_notes',
            'interview_rating',
            'interviewer_feedback',
            'reminder_24h_sent',
            'reminder_1h_sent',
            'cancelled_by',
            'cancellation_reason',
            'cancelled_at',
            'original_scheduled_date',
            'reschedule_count',
            'feedback_template',
            'feedback_template_id',
            'candidate_response',
            'proposed_times',
            'can_reschedule',
            'can_cancel',
            'can_mark_completed',
            'is_upcoming',
            'calendar_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'application_id',
            'reminder_24h_sent',
            'reminder_1h_sent',
            'cancelled_by',
            'cancelled_at',
            'original_scheduled_date',
            'reschedule_count',
            'candidate_response',
            'proposed_times',
            'feedback_template',
            'feedback_template_id',
            'created_at',
            'updated_at',
        ]
    
    def get_candidate_name(self, obj):
        """Get candidate's full name if available"""
        try:
            return obj.application.applicant.personalprofile.full_name
        except:
            return obj.application.applicant.email
    
    def get_all_interviewers(self, obj):
        """Get list of all interviewers"""
        return obj.get_all_interviewers()


class InterviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new interviews
    """
    
    application_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'application_id',
            'interview_type',
            'scheduled_date',
            'duration_minutes',
            'timezone_name',
            'location',
            'video_link',
            'dial_in_number',
            'interviewer_name',
            'interviewer_email',
            'additional_interviewers',
            'candidate_instructions',
            'company_notes',
        ]
    
    def validate_application_id(self, value):
        """Validate that application exists"""
        from apps.applications.models import Application
        
        try:
            application = Application.objects.get(id=value)
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found")
        
        return value
    
    def create(self, validated_data):
        """Create interview and link to application"""
        from apps.applications.models import Application
        
        application_id = validated_data.pop('application_id')
        application = Application.objects.get(id=application_id)
        
        interview = Interview.objects.create(
            application=application,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        return interview


class InterviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating interviews
    """
    
    class Meta:
        model = Interview
        fields = [
            'interview_type',
            'scheduled_date',
            'duration_minutes',
            'timezone_name',
            'location',
            'video_link',
            'dial_in_number',
            'interviewer_name',
            'interviewer_email',
            'additional_interviewers',
            'candidate_instructions',
            'company_notes',
        ]


class InterviewRescheduleSerializer(serializers.Serializer):
    """
    Serializer for rescheduling interviews
    """
    
    new_scheduled_date = serializers.DateTimeField(required=True)
    reschedule_reason = serializers.CharField(required=True)


class InterviewCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling interviews
    """
    
    cancellation_reason = serializers.CharField(required=True)


class InterviewCompleteSerializer(serializers.Serializer):
    """
    Serializer for completing interviews
    """
    
    completion_notes = serializers.CharField(required=False, allow_blank=True)
    interview_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    interviewer_feedback = serializers.CharField(required=False, allow_blank=True)
    recommend_next_round = serializers.BooleanField(required=False)


class InterviewListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing interviews
    """
    
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    company_name = serializers.CharField(source='application.job.company.company_name', read_only=True)
    candidate_email = serializers.EmailField(source='application.applicant.email', read_only=True)
    
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id',
            'job_title',
            'company_name',
            'candidate_email',
            'interview_type',
            'interview_type_display',
            'status',
            'status_display',
            'scheduled_date',
            'duration_minutes',
            'location',
            'video_link',
        ]
