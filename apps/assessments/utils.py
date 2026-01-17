from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import landscape, letter
from django.core.cache import cache
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_certificate_pdf(badge):
    """Generate a professional certificate PDF for a badge"""
    buffer = BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # Draw border
    c.setStrokeColorRGB(0.2, 0.4, 0.8)
    c.setLineWidth(3)
    c.rect(0.5*inch, 0.5*inch, width-1*inch, height-1*inch)
    
    # Inner decorative border
    c.setStrokeColorRGB(0.8, 0.85, 0.95)
    c.setLineWidth(1)
    c.rect(0.6*inch, 0.6*inch, width-1.2*inch, height-1.2*inch)
    
    # Title
    c.setFont('Helvetica-Bold', 42)
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.drawCentredString(width/2, height-1.3*inch, 'Certificate of Achievement')
    
    # Subtitle
    c.setFont('Helvetica', 14)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width/2, height-1.7*inch, 'This certifies that')
    
    # Candidate name
    c.setFont('Helvetica-Bold', 32)
    c.setFillColorRGB(0, 0, 0)
    candidate_name = badge.user.get_full_name() or badge.user.email
    c.drawCentredString(width/2, height-2.5*inch, candidate_name)
    
    # Achievement text
    c.setFont('Helvetica', 16)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width/2, height-3.1*inch, 'has successfully completed the')
    
    # Test name
    c.setFont('Helvetica-Bold', 24)
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.drawCentredString(width/2, height-3.8*inch, badge.test.title)
    
    # Test details
    c.setFont('Helvetica', 14)
    c.setFillColorRGB(0, 0, 0)
    details = f"Skill: {badge.test.skill_name} | Difficulty: {badge.test.get_difficulty_display()}"
    c.drawCentredString(width/2, height-4.4*inch, details)
    
    # Score
    c.setFont('Helvetica-Bold', 18)
    score_color = colors.HexColor('#00C853') if badge.attempt.score >= 90 else colors.HexColor('#FF9500')
    c.setFillColor(score_color)
    c.drawCentredString(width/2, height-5.0*inch, f"Score: {badge.attempt.score}%")
    
    # Date
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    issue_date = badge.issued_at.strftime('%B %d, %Y')
    c.drawCentredString(width/2, height-5.6*inch, f"Issued on {issue_date}")
    
    # Verification section
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width/2, 1.2*inch, f"Verification Code: {badge.verification_code}")
    c.drawCentredString(width/2, 0.9*inch, 'Verify this certificate at: hiresight.io/verify')
    
    # Logo placeholder (you can add actual logo)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.drawCentredString(width/2, 0.6*inch, 'HireSight - AI-Powered Recruitment')
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()


def calculate_time_bonus(time_taken_minutes, duration_minutes):
    """Calculate bonus points for completing test quickly"""
    if time_taken_minutes >= duration_minutes:
        return 0
    
    time_saved = duration_minutes - time_taken_minutes
    percentage_saved = (time_saved / duration_minutes) * 100
    
    # Award up to 10% bonus for completing in half the time
    if percentage_saved >= 50:
        return 10
    else:
        return int(percentage_saved / 5)


def get_difficulty_color(difficulty):
    """Get color code for difficulty level"""
    colors = {
        'BEGINNER': '#00C853',
        'INTERMEDIATE': '#FF9500',
        'ADVANCED': '#FF3B30',
        'EXPERT': '#9333EA'
    }
    return colors.get(difficulty, '#666666')


def format_duration(minutes):
    """Format duration in human-readable format"""
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if mins == 0:
        return f"{hours} hr"
    
    return f"{hours} hr {mins} min"


def get_performance_level(score):
    """Get performance level description based on score"""
    if score >= 95:
        return "Outstanding", "🏆"
    elif score >= 90:
        return "Excellent", "⭐"
    elif score >= 80:
        return "Very Good", "✨"
    elif score >= 70:
        return "Good", "✓"
    elif score >= 60:
        return "Fair", "○"
    else:
        return "Needs Improvement", "×"


def generate_skill_recommendations(user, completed_tests):
    """Generate skill recommendations based on completed tests"""
    from .models import SkillTest
    
    # Get skills from completed tests
    tested_skills = set()
    for attempt in completed_tests:
        tested_skills.add(attempt.test.skill_name.lower())
    
    # Get user's profile skills
    user_skills = set()
    if hasattr(user, 'personal_profile'):
        user_skills = {s.get('skill', '').lower() for s in user.personal_profile.skills}
    
    # Find untested skills from user's profile
    untested_skills = user_skills - tested_skills
    
    # Get available tests for untested skills
    recommendations = SkillTest.objects.filter(
        skill_name__in=[s.title() for s in untested_skills],
        is_active=True
    ).order_by('-total_attempts')[:5]
    
    return list(recommendations)


def get_test_stats(test_id):
    """Cache frequently accessed test statistics."""
    cache_key = f"test_stats_{test_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    from .models import SkillTest

    try:
        test = SkillTest.objects.get(id=test_id)
    except SkillTest.DoesNotExist:
        cached = {'total_attempts': 0, 'pass_rate': 0, 'avg_score': 0}
        cache.set(cache_key, cached, 60 * 5)
        return cached

    stats = {
        'total_attempts': test.total_attempts,
        'pass_rate': test.get_pass_rate(),
        'avg_score': float(test.average_score or 0),
    }

    cache.set(cache_key, stats, 60 * 5)
    return stats
