from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from apps.accounts.models import User
import uuid
import secrets
import random


class QuestionPool(models.Model):
    """Pool of questions for dynamic test generation"""
    
    DIFFICULTY_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]
    
    QUESTION_TYPES = [
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
        ('TRUE_FALSE', 'True/False'),
        ('CODE', 'Coding Challenge'),
        ('ESSAY', 'Essay/Written'),
        ('FILL_BLANK', 'Fill in the Blank'), 
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill_name = models.CharField(max_length=100, db_index=True, help_text="e.g., Python, React, SQL")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='MULTIPLE_CHOICE')
    
    # Question content
    question = models.TextField(help_text="The question text")
    options = models.JSONField(default=list, blank=True, help_text="Answer options for multiple choice")
    correct_answer = models.JSONField(help_text="Correct answer(s)")
    explanation = models.TextField(blank=True, help_text="Explanation of the correct answer")
    
    # Metadata
    points = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(100)])
    estimated_time_seconds = models.PositiveIntegerField(default=60, help_text="Estimated time to answer")
    
    # Usage statistics
    times_used = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    average_time_taken = models.FloatField(default=0.0)
    
    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False, help_text="Verified by admin")
    is_flagged = models.BooleanField(default=False)
    flag_count = models.PositiveIntegerField(default=0)
    explanation_upvotes = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_questions')
    
    class Meta:
        ordering = ['skill_name', 'difficulty']
        indexes = [
            models.Index(fields=['skill_name', 'difficulty', 'is_active']),
            models.Index(fields=['question_type', 'is_active']),
        ]
        verbose_name = 'Question Pool'
        verbose_name_plural = 'Question Pools'
    
    def __str__(self):
        return f"{self.skill_name} - {self.get_difficulty_display()} - {self.question[:50]}"
    
    def get_success_rate(self):
        """Calculate success rate percentage"""
        if self.times_used == 0:
            return 0
        return round((self.times_correct / self.times_used) * 100, 1)
    
    def record_usage(self, is_correct, time_taken_seconds):
        """Record question usage statistics"""
        self.times_used += 1
        if is_correct:
            self.times_correct += 1
        
        # Update average time
        if self.average_time_taken == 0:
            self.average_time_taken = time_taken_seconds
        else:
            self.average_time_taken = (self.average_time_taken * (self.times_used - 1) + time_taken_seconds) / self.times_used
        
        self.save(update_fields=['times_used', 'times_correct', 'average_time_taken'])


class SkillTest(models.Model):
    """Template for skill assessments - can be static or dynamic"""
    
    DIFFICULTY_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]
    
    TEST_TYPES = [
        ('STATIC', 'Static (Fixed Questions)'),
        ('DYNAMIC', 'Dynamic (Random from Pool)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    skill_name = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, default='DYNAMIC')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='BEGINNER')
    
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(180)],
        default=30
    )
    passing_score = models.PositiveIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        default=70
    )
    
    # For static tests
    questions = models.JSONField(default=list, blank=True, help_text="Static questions")
    
    # For dynamic tests
    question_count = models.PositiveIntegerField(default=20, help_text="Number of questions to generate")
    question_pool_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filters for question pool: {'difficulty': 'INTERMEDIATE', 'types': ['MULTIPLE_CHOICE']}"
    )
    
    # Metadata
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    
    # Requirements
    required_skills = models.JSONField(default=list, help_text="Skills required to see this test")
    
    # Stats
    total_attempts = models.PositiveIntegerField(default=0)
    total_passed = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_completion_time = models.FloatField(default=0.0, help_text="Average time in minutes")
    max_retakes_per_day = models.PositiveIntegerField(default=3, help_text="Daily retake cap per user")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['skill_name', 'difficulty']
        indexes = [
            models.Index(fields=['skill_name', 'difficulty', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['slug']),
        ]
        verbose_name = 'Skill Test'
        verbose_name_plural = 'Skill Tests'
    
    def __str__(self):
        return f"{self.skill_name} - {self.get_difficulty_display()} ({self.title})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(f"{self.skill_name}-{self.difficulty}-{self.title}")
            slug = base_slug
            counter = 1
            while SkillTest.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('assessments:test_detail', kwargs={'slug': self.slug})
    
    def generate_questions(self):
        """Generate random questions from pool for dynamic tests"""
        if self.test_type != 'DYNAMIC':
            return self.questions
        
        # Get filters
        filters = self.question_pool_filters or {}
        difficulty = filters.get('difficulty', self.difficulty)
        question_types = filters.get('types', ['MULTIPLE_CHOICE', 'TRUE_FALSE'])
        
        # Query question pool
        pool = QuestionPool.objects.filter(
            skill_name__iexact=self.skill_name,
            difficulty=difficulty,
            question_type__in=question_types,
            is_active=True
        )
        
        # Randomize and limit
        available_questions = list(pool)
        if len(available_questions) < self.question_count:
            # If not enough questions, use all available
            selected = available_questions
        else:
            selected = random.sample(available_questions, self.question_count)
        
        # Format questions
        questions = []
        for idx, q in enumerate(selected, 1):
            questions.append({
                'id': str(q.id),
                'type': q.question_type.lower(),
                'question': q.question,
                'options': q.options if q.options else [],
                'correct_answer': q.correct_answer,
                'points': q.points,
                'explanation': q.explanation,
                'estimated_time': q.estimated_time_seconds
            })
        
        return questions
    
    def get_question_count(self):
        """Get total number of questions"""
        if self.test_type == 'STATIC':
            return len(self.questions)
        return self.question_count
    
    def get_total_points(self):
        """Calculate total possible points"""
        if self.test_type == 'STATIC':
            return sum(q.get('points', 10) for q in self.questions)
        # For dynamic, estimate based on question count
        return self.question_count * 10
    
    def get_pass_rate(self):
        """Calculate pass rate percentage"""
        if self.total_attempts == 0:
            return 0
        return round((self.total_passed / self.total_attempts) * 100, 1)
    
    def matches_user_skills(self, user):
        """Check if user has the required skills"""
        if not self.required_skills:
            return True
        
        if user.account_type != 'personal' or not hasattr(user, 'personal_profile'):
            return False
        
        user_skills = [s.get('skill', '').lower() for s in user.personal_profile.skills]
        required = [s.lower() for s in self.required_skills]
        
        # Check if user has at least one required skill
        return any(skill in user_skills for skill in required)


class SkillAssessmentAttempt(models.Model):
    """User's attempt at a skill test"""
    
    ATTEMPT_STATUS = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_attempts')
    test = models.ForeignKey(SkillTest, on_delete=models.CASCADE, related_name='attempts')
    
    status = models.CharField(max_length=20, choices=ATTEMPT_STATUS, default='IN_PROGRESS')
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Generated questions (frozen at start)
    frozen_questions = models.JSONField(default=list, help_text="Questions generated for this attempt")
    
    # User responses
    answers = models.JSONField(default=dict, help_text="User's answers keyed by question ID")
    
    # Scoring
    score = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    passed = models.BooleanField(null=True, blank=True)
    points_earned = models.PositiveIntegerField(default=0)
    points_possible = models.PositiveIntegerField(default=0)
    
    # Detailed results
    question_results = models.JSONField(default=dict, help_text="Per-question correctness")
    
    # Timing
    time_taken_minutes = models.PositiveIntegerField(null=True, blank=True)
    time_limit_exceeded = models.BooleanField(default=False)
    is_practice_mode = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'test', 'status']),
            models.Index(fields=['status', 'completed_at']),
            models.Index(fields=['user', '-started_at']),
        ]
        verbose_name = 'Assessment Attempt'
        verbose_name_plural = 'Assessment Attempts'
    
    def __str__(self):
        return f"{self.user.email} - {self.test.title} - {self.score}%"
    
    def get_absolute_url(self):
        return reverse('assessments:results', kwargs={'attempt_id': self.id})
    
    @property
    def score_needed_to_pass(self):
        """Positive gap between passing score and current score."""
        if self.score is None:
            return None
        deficit = self.test.passing_score - self.score
        return deficit if deficit > 0 else 0

    def calculate_score(self):
        """Calculate score with question pool tracking"""
        if self.status != 'COMPLETED':
            return None
        
        total_points = 0
        earned_points = 0
        results = {}
        
        for question in self.frozen_questions:
            q_id = str(question.get('id'))
            q_type = question.get('type')
            q_points = question.get('points', 10)
            total_points += q_points
            
            user_answer = self.answers.get(q_id)
            is_correct = False
            
            if q_type == 'multiple_choice' or q_type == 'true_false':
                correct_answer = question.get('correct_answer')
                try:
                    user_answer_int = int(user_answer) if user_answer is not None else None
                    is_correct = user_answer_int == correct_answer
                except (ValueError, TypeError):
                    is_correct = False
                
                if is_correct:
                    earned_points += q_points
                
                # Update question pool statistics
                try:
                    pool_question = QuestionPool.objects.get(id=q_id)
                    pool_question.record_usage(is_correct, question.get('estimated_time', 60))
                except QuestionPool.DoesNotExist:
                    pass
            
            results[q_id] = {
                'correct': is_correct,
                'points_earned': q_points if is_correct else 0,
                'points_possible': q_points,
                'user_answer': user_answer,
                'correct_answer': question.get('correct_answer'),
                'explanation': question.get('explanation', '')
            }
        
        self.points_earned = earned_points
        self.points_possible = total_points
        self.score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        self.passed = self.score >= self.test.passing_score
        self.question_results = results
        self.save(update_fields=['score', 'passed', 'points_earned', 'points_possible', 'question_results'])
        
        self.update_test_stats()
        
        return self.score
    
    def update_test_stats(self):
        """Update aggregate test statistics"""
        from django.db.models import Avg
        
        test = self.test
        completed_attempts = test.attempts.filter(status='COMPLETED')
        
        test.total_attempts = completed_attempts.count()
        test.total_passed = completed_attempts.filter(passed=True).count()
        test.average_score = completed_attempts.aggregate(avg=Avg('score'))['avg'] or 0
        test.average_completion_time = completed_attempts.aggregate(avg=Avg('time_taken_minutes'))['avg'] or 0
        test.save(update_fields=['total_attempts', 'total_passed', 'average_score', 'average_completion_time'])
    
    def get_elapsed_time(self):
        """Get elapsed time in minutes"""
        if self.status == 'COMPLETED' and self.completed_at:
            elapsed = (self.completed_at - self.started_at).total_seconds() / 60
        else:
            elapsed = (timezone.now() - self.started_at).total_seconds() / 60
        return int(elapsed)
    
    def is_time_expired(self):
        """Check if time limit has been exceeded"""
        return self.get_elapsed_time() > self.test.duration_minutes


class SkillBadge(models.Model):
    """Awarded badge for completed assessments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_badges')
    test = models.ForeignKey(SkillTest, on_delete=models.CASCADE, related_name='badges')
    attempt = models.OneToOneField(SkillAssessmentAttempt, on_delete=models.CASCADE, related_name='badge')
    
    badge_name = models.CharField(max_length=255)
    badge_level = models.CharField(max_length=20, choices=SkillTest.DIFFICULTY_LEVELS)
    badge_image_url = models.ImageField(upload_to='badges/', blank=True, null=True)
    
    issued_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    verification_code = models.CharField(max_length=32, unique=True, db_index=True)
    verification_url = models.URLField(blank=True)
    
    is_public = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)
    
    # Sharing stats
    view_count = models.PositiveIntegerField(default=0)
    shared_with_companies = models.ManyToManyField(
        'accounts.CompanyProfile', 
        blank=True, 
        related_name='viewed_badges'
    )
    
    class Meta:
        ordering = ['-issued_at']
        unique_together = [['user', 'test']]
        indexes = [
            models.Index(fields=['user', 'is_public']),
            models.Index(fields=['verification_code']),
        ]
        verbose_name = 'Skill Badge'
        verbose_name_plural = 'Skill Badges'
    
    def __str__(self):
        return f"{self.user.email} - {self.badge_name}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = secrets.token_urlsafe(24)
        if not self.badge_name:
            self.badge_name = f"{self.test.skill_name} - {self.test.get_difficulty_display()}"
        if not self.badge_level:
            self.badge_level = self.test.difficulty
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('assessments:badge_detail', kwargs={'verification_code': self.verification_code})
    
    def is_expired(self):
        """Check if badge has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class StudyGroup(models.Model):
    """Study groups for collaborative learning."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    skill_focus = models.CharField(max_length=100)

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_study_groups'
    )
    members = models.ManyToManyField(
        User,
        through='StudyGroupMembership',
        related_name='study_groups'
    )

    is_public = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_average_score(self):
        from django.db.models import Avg

        return SkillAssessmentAttempt.objects.filter(
            user__in=self.members.all(),
            test__skill_name__iexact=self.skill_focus,
            status='COMPLETED'
        ).aggregate(avg=Avg('score'))['avg'] or 0


class StudyGroupMembership(models.Model):
    """Link between users and study groups."""

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['joined_at']


class GroupChallenge(models.Model):
    """Challenges that a study group can run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='challenges')
    test = models.ForeignKey(SkillTest, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField()
    prize_description = models.TextField(blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def get_leaderboard(self):
        from django.db.models import Max

        participants = SkillAssessmentAttempt.objects.filter(
            user__study_groups=self.group,
            test=self.test,
            status='COMPLETED',
            completed_at__gte=self.start_date,
            completed_at__lte=self.end_date
        ).values(
            'user',
            'user__email',
            'user__personal_profile__full_name'
        ).annotate(
            best_score=Max('score')
        ).order_by('-best_score')
        return participants[:10]


class QuestionDiscussion(models.Model):
    """Discussions tied to specific questions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey('QuestionPool', on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    upvotes = models.ManyToManyField(User, related_name='upvoted_discussions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_upvote_count(self):
        return self.upvotes.count()


class BookmarkedQuestion(models.Model):
    """User bookmarks for later review or practice."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarked_questions')
    question = models.ForeignKey('QuestionPool', on_delete=models.CASCADE, related_name='bookmarks')
    attempt = models.ForeignKey(SkillAssessmentAttempt, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookmarked_questions')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'question']]
        ordering = ['-created_at']

    def __str__(self):
        return f"Bookmark by {self.user.email} · {self.question.skill_name}"


class Achievement(models.Model):
    """Gamified achievements for assessment milestones."""

    ACHIEVEMENT_TYPES = [
        ('first_attempt_pass', 'First Attempt Pass'),
        ('perfect_score', 'Perfect Score'),
        ('speed_demon', 'Speed Demon'),
        ('consistency_king', 'Consistency King'),
        ('skill_master', 'Skill Master'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏅')
    type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    criteria = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Track achievements earned by users."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='earned_by')
    earned_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [['user', 'achievement']]
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.email} · {self.achievement.name}"


class AssessmentCategory(models.Model):
    """Organize tests by category"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    tests = models.ManyToManyField(SkillTest, related_name='categories', blank=True)
    
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Assessment Category'
        verbose_name_plural = 'Assessment Categories'
    
    def __str__(self):
        return self.name
