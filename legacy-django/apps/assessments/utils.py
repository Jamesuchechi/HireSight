from io import BytesIO
from datetime import datetime
import json
from reportlab.lib.pagesizes import landscape, letter
from django.core.cache import cache
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from collections import Counter, defaultdict
from typing import List, Dict
from .models import SkillAssessmentAttempt, SkillTest, SkillBadge


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


def generate_results_pdf(attempt: SkillAssessmentAttempt) -> bytes:
    """Generate a PDF summary for an assessment attempt."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('Assessment Results', styles['Title']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f'<b>User:</b> {attempt.user.get_full_name() or attempt.user.email}', styles['BodyText']))
    story.append(Paragraph(f'<b>Test:</b> {attempt.test.title} ({attempt.test.skill_name})', styles['BodyText']))
    story.append(Paragraph(f'<b>Difficulty:</b> {attempt.test.get_difficulty_display()}', styles['BodyText']))
    story.append(Paragraph(f'<b>Status:</b> {"Passed" if attempt.passed else "Failed"}', styles['BodyText']))
    story.append(Spacer(1, 0.3 * inch))

    summary_data = [
        ['Metric', 'Value'],
        ['Score', f'{attempt.score or 0}%'],
        ['Time Taken', f'{attempt.time_taken_minutes or 0} minutes'],
        ['Questions', len(attempt.frozen_questions)],
        ['Passed', 'Yes' if attempt.passed else 'No'],
    ]
    table = Table(summary_data, hAlign='LEFT', colWidths=[3 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph('Score Breakdown', styles['Heading2']))
    drawing = Drawing(200, 150)
    pie = Pie()
    pie.x = 40
    pie.y = 15
    pie.width = 120
    pie.height = 120
    score_value = attempt.score or 0
    pie.data = [score_value, 100 - score_value]
    pie.labels = ['Achieved', 'Remaining']
    pie.slices.strokeWidth = 0.5
    pie.slices[0].fillColor = colors.HexColor('#0ea5e9')
    pie.slices[1].fillColor = colors.HexColor('#e5e7eb')
    drawing.add(pie)
    story.append(drawing)
    story.append(Spacer(1, 0.5 * inch))

    story.append(Paragraph('Question-by-question Analysis', styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))
    results = attempt.question_results or {}
    for idx, question in enumerate(attempt.frozen_questions, start=1):
        result = results.get(str(question.get('id')), {})
        story.append(Paragraph(f'<b>Q{idx}:</b> {question.get("question")}', styles['BodyText']))
        user_answer = result.get('user_answer')
        correct_answer_data = question.get('correct_answer')
        if isinstance(correct_answer_data, list):
            correct_display = ', '.join(map(str, correct_answer_data))
        else:
            correct_display = str(correct_answer_data)
        story.append(Paragraph(f'Selected: {user_answer if user_answer not in (None, "") else "No answer"}', styles['BodyText']))
        story.append(Paragraph(f'Correct: {correct_display}', styles['BodyText']))
        story.append(Paragraph(f'Result: {"Correct" if result.get("correct") else "Incorrect"}', styles['BodyText']))
        if question.get('explanation'):
            story.append(Paragraph(f'Explanation: {question.get("explanation")}', styles['BodyText']))
        story.append(Spacer(1, 0.1 * inch))

    story.append(PageBreak())
    story.append(Paragraph('Recommendations', styles['Heading2']))
    story.append(Spacer(1, 0.1 * inch))
    if attempt.score and attempt.score < attempt.test.passing_score:
        story.append(Paragraph('Focus on the concepts related to this skill and retake the test after reviewing the highlighted areas.', styles['BodyText']))
    else:
        story.append(Paragraph('Maintain momentum, explore harder difficulty levels, and keep your streak going.', styles['BodyText']))

    doc.build(story)
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


class LearningPathGenerator:
    """Generate personalized learning paths for a user."""

    def __init__(self, user):
        self.user = user
        self.attempts = SkillAssessmentAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).select_related('test').order_by('-completed_at')
        self.skill_attempts = defaultdict(list)
        for attempt in self.attempts:
            self.skill_attempts[attempt.test.skill_name].append(attempt)

    def generate_path(self) -> Dict:
        weak_areas = self._identify_weak_areas()
        next_steps = self._suggest_next_steps()
        mastery_skills = self._identify_mastered_skills()
        radar_data = self._create_radar_chart_data()

        return {
            'weak_areas': weak_areas,
            'next_steps': next_steps,
            'mastered_skills': mastery_skills,
            'study_plan': self._create_study_plan(weak_areas, next_steps),
            'radar_data': radar_data
        }

    def _identify_weak_areas(self) -> List[Dict]:
        weak_areas = []

        for skill, attempts in self.skill_attempts.items():
            performances = [{
                'score': attempt.score or 0,
                'passed': attempt.passed,
                'difficulty': attempt.test.difficulty,
                'weak_questions': self._extract_weak_questions(attempt)
            } for attempt in attempts]

            avg_score = sum(p['score'] for p in performances) / len(performances)
            fail_rate = sum(1 for p in performances if not p['passed']) / len(performances)

            if avg_score < 70 or fail_rate > 0.5:
                all_weak_questions = []
                for p in performances:
                    all_weak_questions.extend(p['weak_questions'])

                common_topics = self._find_common_topics(all_weak_questions)

                weak_areas.append({
                    'skill': skill,
                    'avg_score': round(avg_score, 1),
                    'attempts': len(performances),
                    'fail_rate': round(fail_rate * 100, 1),
                    'common_weak_topics': common_topics,
                    'recommended_resources': self._get_learning_resources(skill, common_topics)
                })

        return sorted(weak_areas, key=lambda x: x['avg_score'])

    def _extract_weak_questions(self, attempt) -> List[str]:
        weak = []
        if not attempt.question_results:
            return weak

        for q_id, result in attempt.question_results.items():
            if not result.get('correct'):
                for q in attempt.frozen_questions:
                    if str(q.get('id')) == str(q_id):
                        weak.append(q.get('question', ''))
                        break

        return weak

    def _find_common_topics(self, questions: List[str]) -> List[str]:
        import re

        keywords = []
        for question in questions:
            words = re.findall(r'\b[A-Z][a-z]+\b|\b\w+\(\)\b', question)
            keywords.extend(words)

        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(5)]

    def _suggest_next_steps(self) -> List[Dict]:
        suggestions = []
        attempted_skills = {skill.lower() for skill in self.skill_attempts.keys()}

        for skill, skill_attempts in self.skill_attempts.items():
            max_difficulty = max(
                ['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'].index(a.test.difficulty)
                for a in skill_attempts
            )
            difficulties = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT']
            current_level = difficulties[max_difficulty]

            recent_scores = [a.score for a in skill_attempts[:3] if a.score]
            avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0

            if avg_recent >= 80 and max_difficulty < 3:
                next_level = difficulties[max_difficulty + 1]
                next_tests = SkillTest.objects.filter(
                    skill_name=skill,
                    difficulty=next_level,
                    is_active=True
                )

                if next_tests.exists():
                    suggestions.append({
                        'type': 'level_up',
                        'skill': skill,
                        'current_level': current_level,
                        'next_level': next_level,
                        'message': f"You're crushing {current_level}! Ready for {next_level}?",
                        'tests': list(next_tests[:3])
                    })

            elif avg_recent < 60:
                practice_tests = SkillTest.objects.filter(
                    skill_name=skill,
                    difficulty=current_level,
                    is_active=True
                ).exclude(
                    id__in=[a.test_id for a in skill_attempts]
                )

                if practice_tests.exists():
                    suggestions.append({
                        'type': 'practice',
                        'skill': skill,
                        'level': current_level,
                        'message': f"Practice more {current_level} {skill} to improve",
                        'tests': list(practice_tests[:3])
                    })

        try:
            profile = self.user.personal_profile
            profile_skills = [s.get('skill', '').lower() for s in profile.skills]

            for skill_name in profile_skills:
                if skill_name and skill_name.lower() not in attempted_skills:
                    available_tests = SkillTest.objects.filter(
                        skill_name__iexact=skill_name,
                        difficulty='BEGINNER',
                        is_active=True
                    )

                    if available_tests.exists():
                        suggestions.append({
                            'type': 'new_skill',
                            'skill': skill_name.title(),
                            'message': f"Start testing your {skill_name} skills!",
                            'tests': list(available_tests[:3])
                        })
        except AttributeError:
            pass

        return suggestions

    def _identify_mastered_skills(self) -> List[Dict]:
        mastered = []

        for skill, attempts in self.skill_attempts.items():
            if len(attempts) >= 3:
                recent_three = attempts[:3]
                avg_score = sum(a.score or 0 for a in recent_three) / 3
                all_passed = all(a.passed for a in recent_three)

                if avg_score >= 85 and all_passed:
                    mastered.append({
                        'skill': skill,
                        'avg_score': round(avg_score, 1),
                        'total_attempts': len(attempts),
                        'highest_level': max(a.test.get_difficulty_display() for a in attempts)
                    })

        return sorted(mastered, key=lambda x: x['avg_score'], reverse=True)

    def _create_radar_chart_data(self) -> str:
        labels = []
        avg_scores = []
        pass_rates = []

        for skill, attempts in self.skill_attempts.items():
            labels.append(skill)
            scored_attempts = [a.score or 0 for a in attempts if a.score is not None]
            avg_score = round(sum(scored_attempts) / len(scored_attempts), 1) if scored_attempts else 0
            passed_count = sum(1 for a in attempts if a.passed)
            pass_rate = round((passed_count / len(attempts)) * 100, 1) if attempts else 0

            avg_scores.append(avg_score)
            pass_rates.append(pass_rate)

        return json.dumps({
            'labels': labels,
            'avg_scores': avg_scores,
            'pass_rates': pass_rates
        })

    def _create_study_plan(self, weak_areas, next_steps) -> List[Dict]:
        plan = []

        if weak_areas:
            plan.append({
                'phase': 'Strengthen Foundations',
                'duration': '1-2 weeks',
                'focus': self._normalize_focus_items(weak_areas[:2]),
                'action': 'Review concepts and retake failed tests'
            })

        level_ups = [s for s in next_steps if s['type'] == 'level_up']
        if level_ups:
            plan.append({
                'phase': 'Level Up',
                'duration': '2-3 weeks',
                'focus': self._normalize_focus_items(level_ups[:2]),
                'action': 'Take intermediate/advanced tests'
            })

        new_skills = [s for s in next_steps if s['type'] == 'new_skill']
        if new_skills:
            plan.append({
                'phase': 'Expand Skillset',
                'duration': 'Ongoing',
                'focus': self._normalize_focus_items(new_skills[:3]),
                'action': 'Explore new skills from your profile'
            })

        return plan

    def _normalize_focus_items(self, entries: List[Dict]) -> List[Dict]:
        normalized = []
        for entry in entries:
            skill_label = (
                entry.get('skill')
                or entry.get('skill_name')
                or entry.get('test__skill_name')
                or entry.get('label')
                or 'Skill'
            )
            normalized.append({
                'skill': skill_label,
                'current_level': entry.get('current_level'),
                'level': entry.get('level')
            })
        return normalized

    def _get_learning_resources(self, skill: str, topics: List[str]) -> List[Dict]:
        resources = [
            {
                'type': 'Documentation',
                'title': f'Official {skill} Documentation',
                'url': f'https://docs.{skill.lower()}.com'
            },
            {
                'type': 'Practice',
                'title': f'{skill} Exercises',
                'url': f'https://exercism.org/tracks/{skill.lower()}'
            }
        ]

        return resources
