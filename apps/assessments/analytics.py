import statistics
from collections import Counter, defaultdict
from typing import Dict, List

from .models import SkillAssessmentAttempt, SkillTest


class AssessmentAnalytics:
    """Analytics helper for assessments."""

    TIME_BUCKETS = [
        ('Morning', range(5, 12)),
        ('Afternoon', range(12, 17)),
        ('Evening', range(17, 22)),
        ('Night', list(range(22, 24)) + list(range(0, 5)))
    ]

    def __init__(self, user):
        queryset = SkillAssessmentAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).select_related('test').order_by('-completed_at')
        self.attempts: List[SkillAssessmentAttempt] = list(queryset)
        self.skill_attempts = defaultdict(list)
        for attempt in self.attempts:
            self.skill_attempts[attempt.test.skill_name].append(attempt)

    def _bucket_for_hour(self, hour: int) -> str:
        for label, hours in self.TIME_BUCKETS:
            if hour in hours:
                return label
        return 'Unknown'

    def get_time_analysis(self) -> List[Dict]:
        buckets = {
            label: {'bucket': label, 'attempts': 0, 'score_total': 0, 'passed': 0}
            for label, _ in self.TIME_BUCKETS
        }

        for attempt in self.attempts:
            if not attempt.completed_at:
                continue
            label = self._bucket_for_hour(attempt.completed_at.hour)
            bucket = buckets[label]
            bucket['attempts'] += 1
            bucket['score_total'] += attempt.score or 0
            if attempt.passed:
                bucket['passed'] += 1

        analysis = []
        for bucket in buckets.values():
            attempts = bucket['attempts']
            analysis.append({
                'bucket': bucket['bucket'],
                'attempts': attempts,
                'avg_score': round(bucket['score_total'] / attempts, 1) if attempts else 0,
                'pass_rate': round((bucket['passed'] / attempts) * 100, 1) if attempts else 0
            })
        return analysis

    def get_difficulty_progression(self) -> List[Dict]:
        progression = []
        for difficulty, label in SkillTest.DIFFICULTY_LEVELS:
            attempts = [a for a in self.attempts if a.test.difficulty == difficulty]
            count = len(attempts)
            avg_score = round(sum(a.score or 0 for a in attempts) / count, 1) if count else 0
            pass_rate = round((sum(1 for a in attempts if a.passed) / count) * 100, 1) if count else 0
            progression.append({
                'difficulty': difficulty,
                'label': label,
                'count': count,
                'avg_score': avg_score,
                'pass_rate': pass_rate
            })
        return progression

    def get_skill_radar_data(self) -> Dict:
        skill_stats = []
        for skill, attempts in self.skill_attempts.items():
            count = len(attempts)
            avg_score = round(sum(a.score or 0 for a in attempts) / count, 1) if count else 0
            pass_rate = round((sum(1 for a in attempts if a.passed) / count) * 100, 1) if count else 0
            skill_stats.append({
                'skill': skill,
                'avg_score': avg_score,
                'pass_rate': pass_rate,
                'attempts': count
            })

        skill_stats.sort(key=lambda s: s['attempts'], reverse=True)
        top_skills = skill_stats[:8]
        return {
            'labels': [s['skill'] for s in top_skills],
            'avg_scores': [s['avg_score'] for s in top_skills],
            'pass_rates': [s['pass_rate'] for s in top_skills]
        }

    def get_improvement_rate(self) -> Dict:
        if not self.attempts:
            return {'first_avg': 0, 'last_avg': 0, 'change': 0}

        earliest = list(reversed(self.attempts))
        first_scores = [a.score for a in earliest[:10] if a.score is not None]
        last_scores = [a.score for a in self.attempts[:10] if a.score is not None]
        first_avg = round(sum(first_scores) / len(first_scores), 1) if first_scores else 0
        last_avg = round(sum(last_scores) / len(last_scores), 1) if last_scores else 0
        change = round(last_avg - first_avg, 1)
        return {'first_avg': first_avg, 'last_avg': last_avg, 'change': change}

    def get_consistency_score(self) -> float:
        scores = [a.score for a in self.attempts if a.score is not None]
        if not scores:
            return 0.0
        if len(scores) == 1:
            return 100.0
        deviation = statistics.pstdev(scores)
        return max(0.0, round(100 - deviation, 1))

    def get_question_type_performance(self) -> List[Dict]:
        type_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        for attempt in self.attempts:
            question_map = {q['id']: q.get('type', 'unknown') for q in attempt.frozen_questions}
            if not attempt.question_results:
                continue
            for q_id, result in attempt.question_results.items():
                q_type = question_map.get(q_id, 'unknown')
                type_stats[q_type]['total'] += 1
                if result.get('correct'):
                    type_stats[q_type]['correct'] += 1

        performance = []
        for q_type, data in type_stats.items():
            total = data['total']
            performance.append({
                'type': q_type,
                'label': q_type.replace('_', ' ').title(),
                'pass_rate': round((data['correct'] / total) * 100, 1) if total else 0,
                'attempts': total
            })
        performance.sort(key=lambda entry: entry['attempts'], reverse=True)
        return performance

    def generate_insights(self) -> List[Dict]:
        if not self.attempts:
            return [{
                'title': 'Get started',
                'message': 'Take your first assessment to unlock analytics and targeted recommendations.',
                'tone': 'neutral'
            }]

        insights = []
        time_analysis = self.get_time_analysis()
        worst_time = min(time_analysis, key=lambda x: x['pass_rate'])
        if worst_time['attempts'] and worst_time['pass_rate'] < 60:
            insights.append({
                'title': f"Improve your {worst_time['bucket']} performance",
                'message': f"Your pass rate is lowest during {worst_time['bucket']} ({worst_time['pass_rate']}%). Try planning focused practice sessions then.",
                'tone': 'warning'
            })

        difficulty = self.get_difficulty_progression()
        hardest = min(difficulty, key=lambda x: x['pass_rate'])
        if hardest['count'] and hardest['pass_rate'] < 60:
            insights.append({
                'title': f"{hardest['label']} is a bottleneck",
                'message': f"You have {hardest['count']} attempts at {hardest['label']}, but only {hardest['pass_rate']}% pass rate. Review key concepts and retry with short drills.",
                'tone': 'warning'
            })

        question_types = self.get_question_type_performance()
        if question_types:
            weakest = min(question_types, key=lambda x: x['pass_rate'])
            if weakest['attempts'] >= 5:
                insights.append({
                    'title': f"Focus on {weakest['label']}",
                    'message': f"Your {weakest['label']} pass rate is {weakest['pass_rate']}% across {weakest['attempts']} questions. Reinforce syntax and patterns for that type.",
                    'tone': 'info'
                })

        improvement = self.get_improvement_rate()
        if improvement['change'] >= 5:
            insights.append({
                'title': 'Improving steadily',
                'message': f"Last 10 attempts average {improvement['last_avg']}% versus {improvement['first_avg']}% earlier — keep up the momentum!",
                'tone': 'success'
            })
        elif improvement['change'] <= -5:
            insights.append({
                'title': 'Recent dip detected',
                'message': f"Your latest average ({improvement['last_avg']}%) is below your early average ({improvement['first_avg']}%). Revisit fundamentals before the next attempt.",
                'tone': 'warning'
            })

        consistency = self.get_consistency_score()
        if consistency < 70:
            insights.append({
                'title': 'Boost consistency',
                'message': f"Your consistency score is {consistency}%. Aim for steadier pacing and note which question types cause swings.",
                'tone': 'info'
            })

        return insights
