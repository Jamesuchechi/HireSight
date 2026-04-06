"""
Advanced resume analysis features for HireSight.
Includes comparison tools, industry benchmarking, and optimization tracking.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
from django.db.models import Avg, Count, Q
from django.utils import timezone
import re
from .models import Resume, ResumeOptimization, ResumeSuggestion
from .optimization import ResumeOptimizer


class ResumeComparator:
    """Compare multiple resumes for optimization insights."""

    def __init__(self):
        self.optimizer = ResumeOptimizer()

    def compare_resumes(self, resume_ids: List[int], user_id: int) -> Dict[str, Any]:
        """Compare multiple resumes owned by the same user."""
        resumes = Resume.objects.filter(
            id__in=resume_ids,
            user_id=user_id,
            status='parsed'
        ).select_related('optimization')

        if len(resumes) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 parsed resumes to compare'
            }

        comparisons = {}
        resume_data = {}

        # Analyze each resume
        for resume in resumes:
            analysis = self.optimizer.optimize_resume(resume.parsed_text or '')
            resume_data[resume.id] = {
                'title': resume.title,
                'analysis': analysis,
                'uploaded_at': resume.uploaded_at.isoformat(),
                'version': resume.version
            }

        # Compare scores across resumes
        score_comparison = self._compare_scores(resume_data)

        # Compare content evolution
        content_comparison = self._compare_content_evolution(resume_data)

        # Generate improvement trajectory
        trajectory = self._analyze_improvement_trajectory(resume_data)

        return {
            'success': True,
            'resumes': resume_data,
            'score_comparison': score_comparison,
            'content_comparison': content_comparison,
            'improvement_trajectory': trajectory,
            'recommendations': self._generate_comparison_recommendations(resume_data)
        }

    def _compare_scores(self, resume_data: Dict) -> Dict[str, Any]:
        """Compare optimization scores across resumes."""
        scores_by_resume = {}
        score_categories = ['overall_score', 'action_verbs', 'keywords', 'ats']

        for resume_id, data in resume_data.items():
            analysis = data['analysis']
            scores_by_resume[resume_id] = {
                'overall_score': analysis.get('overall_score', 0),
                'action_verbs': analysis.get('action_verbs', {}).get('score', 0),
                'keywords': analysis.get('keywords', {}).get('density_score', 0),
                'ats': analysis.get('ats', {}).get('overall_score', 0)
            }

        # Calculate averages and best scores
        category_averages = {}
        best_scores = {}

        for category in score_categories:
            scores = [scores[category] for scores in scores_by_resume.values()]
            category_averages[category] = round(statistics.mean(scores), 1) if scores else 0

            # Find best score and which resume achieved it
            max_score = max(scores) if scores else 0
            best_resume = None
            for resume_id, resume_scores in scores_by_resume.items():
                if resume_scores[category] == max_score:
                    best_resume = resume_id
                    break

            best_scores[category] = {
                'score': max_score,
                'resume_id': best_resume,
                'resume_title': resume_data[best_resume]['title'] if best_resume else None
            }

        return {
            'scores_by_resume': scores_by_resume,
            'averages': category_averages,
            'best_scores': best_scores,
            'trends': self._analyze_score_trends(resume_data)
        }

    def _compare_content_evolution(self, resume_data: Dict) -> Dict[str, Any]:
        """Compare how content has evolved across resume versions."""
        evolution = {
            'skills_added': [],
            'skills_removed': [],
            'experience_growth': [],
            'keyword_evolution': []
        }

        # Sort resumes by version/upload date
        sorted_resumes = sorted(
            resume_data.items(),
            key=lambda x: (x[1]['version'], x[1]['uploaded_at'])
        )

        if len(sorted_resumes) >= 2:
            prev_resume = None
            for resume_id, data in sorted_resumes:
                if prev_resume:
                    prev_data = resume_data[prev_resume]['analysis']
                    curr_data = data['analysis']

                    # Compare skills
                    prev_skills = set(prev_data.get('keywords', {}).get('keyword_counts', {}).keys())
                    curr_skills = set(curr_data.get('keywords', {}).get('keyword_counts', {}).keys())

                    added = curr_skills - prev_skills
                    removed = prev_skills - curr_skills

                    if added or removed:
                        evolution['skills_added'].extend(list(added))
                        evolution['skills_removed'].extend(list(removed))

                    # Compare experience mentions
                    prev_exp = len(prev_data.get('experience', []))
                    curr_exp = len(curr_data.get('experience', []))
                    evolution['experience_growth'].append({
                        'from_version': resume_data[prev_resume]['version'],
                        'to_version': data['version'],
                        'growth': curr_exp - prev_exp
                    })

                prev_resume = resume_id

        return evolution

    def _analyze_improvement_trajectory(self, resume_data: Dict) -> Dict[str, Any]:
        """Analyze the trajectory of resume improvements."""
        trajectory = {
            'score_improvement': [],
            'consistent_improvements': [],
            'areas_needing_attention': []
        }

        # Sort by version/date
        sorted_resumes = sorted(
            resume_data.items(),
            key=lambda x: (x[1]['version'], x[1]['uploaded_at'])
        )

        if len(sorted_resumes) >= 2:
            prev_score = None
            for resume_id, data in sorted_resumes:
                curr_score = data['analysis'].get('overall_score', 0)

                if prev_score is not None:
                    improvement = curr_score - prev_score
                    trajectory['score_improvement'].append({
                        'from_version': resume_data[sorted_resumes[sorted_resumes.index((resume_id, data)) - 1][0]]['version'],
                        'to_version': data['version'],
                        'improvement': round(improvement, 1),
                        'from_score': prev_score,
                        'to_score': curr_score
                    })

                prev_score = curr_score

        # Identify consistent improvements
        improvements = [item['improvement'] for item in trajectory['score_improvement']]
        if improvements and all(imp > 0 for imp in improvements):
            trajectory['consistent_improvements'].append("Consistently improving overall scores")
        elif improvements and all(imp < 0 for imp in improvements):
            trajectory['areas_needing_attention'].append("Scores are declining - review recent changes")

        return trajectory

    def _analyze_score_trends(self, resume_data: Dict) -> Dict[str, Any]:
        """Analyze scoring trends across resume versions."""
        trends = {}

        # Group by category
        categories = ['overall_score', 'action_verbs', 'keywords', 'ats']
        for category in categories:
            scores = []
            versions = []

            for resume_id, data in resume_data.items():
                if category == 'overall_score':
                    score = data['analysis'].get('overall_score', 0)
                else:
                    score = data['analysis'].get(category, {}).get('score', 0) if category == 'action_verbs' else \
                           data['analysis'].get(category, {}).get('density_score' if category == 'keywords' else 'overall_score', 0)

                scores.append(score)
                versions.append(data['version'])

            if len(scores) >= 2:
                # Calculate trend
                trend = "stable"
                if scores[-1] > scores[0]:
                    trend = "improving"
                elif scores[-1] < scores[0]:
                    trend = "declining"

                trends[category] = {
                    'trend': trend,
                    'change': round(scores[-1] - scores[0], 1),
                    'best_score': max(scores),
                    'average_score': round(statistics.mean(scores), 1)
                }

        return trends

    def _generate_comparison_recommendations(self, resume_data: Dict) -> List[str]:
        """Generate recommendations based on resume comparison."""
        recommendations = []

        if len(resume_data) < 2:
            return recommendations

        # Find best performing resume
        best_resume = max(
            resume_data.items(),
            key=lambda x: x[1]['analysis'].get('overall_score', 0)
        )

        recommendations.append(
            f"Your best performing resume is '{best_resume[1]['title']}' "
            f"with a score of {best_resume[1]['analysis'].get('overall_score', 0)}. "
            "Consider using it as a template for future versions."
        )

        # Check for declining trends
        trends = self._analyze_score_trends(resume_data)
        declining_categories = [
            category for category, data in trends.items()
            if data['trend'] == 'declining'
        ]

        if declining_categories:
            recommendations.append(
                f"Scores are declining in: {', '.join(declining_categories)}. "
                "Review recent changes that may have negatively impacted these areas."
            )

        return recommendations


class IndustryBenchmarker:
    """Compare resume performance against industry benchmarks."""

    # Industry benchmarks (based on general resume optimization data)
    INDUSTRY_BENCHMARKS = {
        'technology': {
            'overall_score': 75,
            'action_verbs': 80,
            'keywords': 70,
            'ats': 78,
            'top_keywords': ['python', 'javascript', 'aws', 'docker', 'agile', 'react', 'sql', 'git']
        },
        'finance': {
            'overall_score': 72,
            'action_verbs': 75,
            'keywords': 68,
            'ats': 75,
            'top_keywords': ['financial analysis', 'budgeting', 'forecasting', 'excel', 'sql', 'regulatory compliance']
        },
        'healthcare': {
            'overall_score': 70,
            'action_verbs': 72,
            'keywords': 65,
            'ats': 72,
            'top_keywords': ['patient care', 'medical records', 'compliance', 'emr', 'hipaa', 'clinical']
        },
        'marketing': {
            'overall_score': 68,
            'action_verbs': 70,
            'keywords': 72,
            'ats': 68,
            'top_keywords': ['digital marketing', 'seo', 'social media', 'analytics', 'campaign management', 'crm']
        },
        'general': {
            'overall_score': 65,
            'action_verbs': 68,
            'keywords': 60,
            'ats': 70,
            'top_keywords': ['leadership', 'communication', 'project management', 'teamwork', 'analysis']
        }
    }

    def benchmark_resume(self, resume_analysis: Dict, industry: str = 'general') -> Dict[str, Any]:
        """Benchmark a resume against industry standards."""
        benchmark = self.INDUSTRY_BENCHMARKS.get(industry, self.INDUSTRY_BENCHMARKS['general'])

        comparison = {
            'industry': industry,
            'benchmark_scores': benchmark,
            'resume_scores': {},
            'performance_rating': {},
            'gaps': [],
            'strengths': []
        }

        # Compare scores
        score_mappings = {
            'overall_score': 'overall_score',
            'action_verbs': ('action_verbs', 'score'),
            'keywords': ('keywords', 'density_score'),
            'ats': ('ats', 'overall_score')
        }

        for benchmark_key, resume_key in score_mappings.items():
            benchmark_score = benchmark[benchmark_key]

            if isinstance(resume_key, tuple):
                resume_score = resume_analysis.get(resume_key[0], {}).get(resume_key[1], 0)
            else:
                resume_score = resume_analysis.get(resume_key, 0)

            comparison['resume_scores'][benchmark_key] = resume_score

            # Calculate performance rating
            if resume_score >= benchmark_score:
                rating = 'above_average'
                comparison['strengths'].append(f"Exceeds {benchmark_key.replace('_', ' ')} benchmark")
            elif resume_score >= benchmark_score * 0.9:
                rating = 'average'
            else:
                rating = 'below_average'
                comparison['gaps'].append(f"Below {benchmark_key.replace('_', ' ')} benchmark")

            comparison['performance_rating'][benchmark_key] = {
                'rating': rating,
                'benchmark': benchmark_score,
                'resume': resume_score,
                'gap': round(resume_score - benchmark_score, 1)
            }

        # Keyword analysis
        resume_keywords = set()
        for category_data in resume_analysis.get('keywords', {}).get('keyword_counts', {}).values():
            resume_keywords.update(category_data.keys())

        benchmark_keywords = set(benchmark['top_keywords'])
        missing_keywords = benchmark_keywords - resume_keywords

        if missing_keywords:
            comparison['gaps'].append(f"Missing industry keywords: {', '.join(list(missing_keywords)[:5])}")

        # Calculate overall scores for template compatibility
        overall_resume_score = resume_analysis.get('overall_score', 0)
        overall_benchmark_score = benchmark['overall_score']

        return {
            'your_score': overall_resume_score,
            'industry_average': overall_benchmark_score,
            'performance_gap': round(overall_resume_score - overall_benchmark_score, 1),
            'selected_industry': industry,
            'metrics': self._format_metrics_for_template(comparison),
            'insights': self.get_industry_insights(industry, comparison),
            **comparison  # Include all original comparison data
        }

    def _format_metrics_for_template(self, comparison: Dict) -> List[Dict]:
        """Format metrics for template display."""
        metrics = []
        metric_names = {
            'overall_score': 'Overall Score',
            'action_verbs': 'Action Verbs',
            'keywords': 'Keyword Density',
            'ats': 'ATS Compatibility'
        }

        for key, name in metric_names.items():
            rating = comparison['performance_rating'][key]
            metrics.append({
                'name': name,
                'your_score': rating['resume'],
                'industry_score': rating['benchmark'],
                'description': f"How your {name.lower()} compares to industry standards",
                'recommendations': self._get_metric_recommendations(key, rating)
            })

        return metrics

    def get_industry_insights(self, industry: str, comparison: Dict) -> List[Dict]:
        """Generate industry-specific insights."""
        insights = []

        if industry == 'technology':
            insights.append({
                'title': 'Tech Industry Trends',
                'description': 'Technology resumes should emphasize technical skills, frameworks, and cloud technologies.'
            })
        elif industry == 'finance':
            insights.append({
                'title': 'Finance Industry Focus',
                'description': 'Financial resumes should highlight analytical skills, regulatory knowledge, and risk management.'
            })
        else:
            insights.append({
                'title': 'General Best Practices',
                'description': 'Focus on quantifiable achievements and industry-specific keywords.'
            })

        # Add insights based on performance
        strengths = comparison.get('strengths', [])
        if strengths:
            insights.append({
                'title': 'Your Strengths',
                'description': f"You excel in: {', '.join(strengths[:2])}"
            })

        return insights

    def _get_metric_recommendations(self, metric_key: str, rating: Dict) -> List[str]:
        """Get recommendations for a specific metric."""
        recommendations = []

        if rating['rating'] == 'below_average':
            if metric_key == 'action_verbs':
                recommendations.append("Use more action verbs like 'developed', 'implemented', 'optimized'")
            elif metric_key == 'keywords':
                recommendations.append("Include more industry-specific keywords")
            elif metric_key == 'ats':
                recommendations.append("Ensure consistent formatting and avoid complex layouts")
        elif rating['rating'] == 'average':
            recommendations.append("You're on track - focus on continuous improvement")

        return recommendations

    def get_industry_recommendations(self, benchmark_comparison: Dict) -> List[str]:
        """Generate industry-specific recommendations."""
        recommendations = []
        industry = benchmark_comparison['industry']

        # General recommendations based on gaps
        gaps = benchmark_comparison.get('gaps', [])
        for gap in gaps:
            if 'below' in gap.lower():
                category = gap.split('benchmark')[0].strip()
                recommendations.append(
                    f"Focus on improving {category} to meet {industry} industry standards."
                )
            elif 'missing industry keywords' in gap.lower():
                recommendations.append(
                    f"Incorporate relevant {industry} keywords to improve ATS compatibility."
                )

        # Industry-specific advice
        industry_advice = {
            'technology': [
                "Include specific programming languages and frameworks",
                "Highlight cloud platform experience",
                "Emphasize agile development practices"
            ],
            'finance': [
                "Quantify financial achievements with specific metrics",
                "Highlight regulatory compliance experience",
                "Include financial software proficiency"
            ],
            'healthcare': [
                "Emphasize patient care achievements",
                "Include relevant certifications",
                "Highlight compliance and regulatory knowledge"
            ],
            'marketing': [
                "Quantify campaign results and ROI",
                "Include specific marketing tools and platforms",
                "Highlight data-driven marketing experience"
            ]
        }

        if industry in industry_advice:
            recommendations.extend(industry_advice[industry][:2])  # Limit to 2 specific recommendations

        return recommendations


class OptimizationTracker:
    """Track optimization progress over time."""

    def get_optimization_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get optimization history for a user over the specified period."""
        since_date = timezone.now() - timedelta(days=days)

        optimizations = ResumeOptimization.objects.filter(
            resume__user_id=user_id,
            analyzed_at__gte=since_date
        ).select_related('resume').order_by('-analyzed_at')

        history = {
            'total_optimizations': optimizations.count(),
            'score_trends': [],
            'most_improved_areas': [],
            'recent_activity': []
        }

        if optimizations.exists():
            # Score trends
            scores_over_time = []
            for opt in optimizations[:10]:  # Last 10 optimizations
                scores_over_time.append({
                    'date': opt.analyzed_at.isoformat(),
                    'overall_score': opt.overall_score,
                    'ats_score': opt.ats_score,
                    'action_verb_score': opt.action_verb_score,
                    'keyword_score': opt.keyword_score,
                    'resume_title': opt.resume.title
                })

            history['score_trends'] = scores_over_time

            # Most improved areas (compare first vs last optimization)
            if len(scores_over_time) >= 2:
                first_scores = scores_over_time[-1]  # Oldest
                last_scores = scores_over_time[0]   # Newest

                improvements = {}
                for key in ['overall_score', 'ats_score', 'action_verb_score', 'keyword_score']:
                    improvement = last_scores[key] - first_scores[key]
                    if improvement > 0:
                        improvements[key] = round(improvement, 1)

                if improvements:
                    # Sort by improvement amount
                    sorted_improvements = sorted(
                        improvements.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    history['most_improved_areas'] = [
                        {'area': area.replace('_', ' ').title(), 'improvement': imp}
                        for area, imp in sorted_improvements[:3]
                    ]

            # Recent activity (rename to timeline for template compatibility)
            recent_opts = optimizations[:5]
            history['timeline'] = [
                {
                    'date': opt.analyzed_at,
                    'resume_title': opt.resume.title,
                    'overall_score': opt.overall_score,
                    'ats_score': opt.ats_score,
                    'action_verb_score': opt.action_verb_score,
                    'keyword_score': opt.keyword_score,
                    'improvement': self._calculate_improvement(opt)
                }
                for opt in recent_opts
            ]

        return history

    def _calculate_improvement(self, optimization: ResumeOptimization) -> Optional[float]:
        """Calculate improvement from previous optimization of the same resume."""
        try:
            previous_opt = ResumeOptimization.objects.filter(
                resume=optimization.resume,
                analyzed_at__lt=optimization.analyzed_at
            ).order_by('-analyzed_at').first()

            if previous_opt:
                return round(optimization.overall_score - previous_opt.overall_score, 1)

        except Exception:
            pass

        return None

    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Get aggregated insights for a user."""
        optimizations = ResumeOptimization.objects.filter(
            resume__user_id=user_id
        ).aggregate(
            avg_overall=Avg('overall_score'),
            avg_ats=Avg('ats_score'),
            avg_action_verbs=Avg('action_verb_score'),
            avg_keywords=Avg('keyword_score'),
            total_optimizations=Count('id')
        )

        insights = {
            'total_optimizations': optimizations['total_optimizations'] or 0,
            'average_scores': {
                'overall': round(optimizations['avg_overall'] or 0, 1),
                'ats': round(optimizations['avg_ats'] or 0, 1),
                'action_verbs': round(optimizations['avg_action_verbs'] or 0, 1),
                'keywords': round(optimizations['avg_keywords'] or 0, 1)
            },
            'strengths': [],
            'focus_areas': []
        }

        # Identify strengths and focus areas
        avg_scores = insights['average_scores']

        # Strengths: scores above 70
        for area, score in avg_scores.items():
            if score >= 70:
                insights['strengths'].append(area.replace('_', ' ').title())

        # Focus areas: scores below 60
        for area, score in avg_scores.items():
            if score < 60:
                insights['focus_areas'].append(area.replace('_', ' ').title())

        return insights


class AdvancedResumeAdvisor:
    """Advanced AI-powered resume optimization with learning capabilities."""

    def __init__(self):
        from .optimization import MistralResumeAdvisor
        self.ai_advisor = MistralResumeAdvisor()

    def generate_advanced_suggestions(self, resume_text: str, job_description: str = None,
                                    user_history: Dict = None) -> Dict[str, Any]:
        """Generate advanced suggestions incorporating user history and patterns."""
        base_suggestions = self.ai_advisor.generate_suggestions(resume_text, job_description)

        if not base_suggestions.get('success', False):
            return base_suggestions

        # Enhance suggestions with user history insights
        if user_history:
            enhanced_suggestions = self._enhance_with_history(
                base_suggestions['suggestions'],
                user_history
            )
        else:
            enhanced_suggestions = base_suggestions['suggestions']

        # Add personalized recommendations based on patterns
        personalized = self._add_personalized_recommendations(
            enhanced_suggestions,
            resume_text,
            user_history
        )

        return {
            'success': True,
            'suggestions': personalized,
            'enhancement_type': 'advanced_with_history' if user_history else 'advanced'
        }

    def _enhance_with_history(self, suggestions: List[Dict], user_history: Dict) -> List[Dict]:
        """Enhance suggestions based on user's optimization history."""
        enhanced = []

        # Identify user's improvement patterns
        strengths = user_history.get('strengths', [])
        focus_areas = user_history.get('focus_areas', [])

        for suggestion in suggestions:
            enhanced_suggestion = suggestion.copy()

            # Boost priority for focus areas
            if any(area.lower() in suggestion.get('category', '').lower() for area in focus_areas):
                enhanced_suggestion['impact_level'] = 'high'
                enhanced_suggestion['title'] = f"[Priority] {suggestion['title']}"

            # Note if this builds on user strengths
            if any(area.lower() in suggestion.get('category', '').lower() for area in strengths):
                enhanced_suggestion['description'] += " (Builds on your strengths)"

            enhanced.append(enhanced_suggestion)

        return enhanced

    def _add_personalized_recommendations(self, existing_suggestions: List[Dict],
                                        resume_text: str, user_history: Dict = None) -> List[Dict]:
        """Add personalized recommendations based on analysis."""
        personalized = existing_suggestions.copy()

        # Analyze resume for specific patterns and add targeted advice
        resume_lower = resume_text.lower()

        # Check for common issues and add specific suggestions
        patterns_and_suggestions = [
            {
                'pattern': r'\b(i|we|our)\s+(am|are|was|were)\s+responsible\s+for\b',
                'suggestion': {
                    'impact_level': 'medium',
                    'category': 'action_verbs',
                    'title': 'Replace passive "responsible for" phrases',
                    'description': 'Change "was responsible for" to strong action verbs like "managed", "led", or "directed"',
                    'suggestion': 'Replace passive constructions with active, powerful verbs that demonstrate leadership and initiative.'
                }
            },
            {
                'pattern': r'\b\d+(\.\d+)?\s*years?\s+(of\s+)?experience\b',
                'suggestion': {
                    'impact_level': 'high',
                    'category': 'quantifiable_achievements',
                    'title': 'Add specific metrics to experience',
                    'description': 'Instead of just mentioning years of experience, quantify your achievements with specific metrics',
                    'suggestion': 'Replace generic experience statements with measurable accomplishments (e.g., "Increased sales by 35%" instead of "5 years sales experience")'
                }
            },
            {
                'pattern': r'\b(helped|assisted|supported)\b',
                'suggestion': {
                    'impact_level': 'medium',
                    'category': 'action_verbs',
                    'title': 'Strengthen supporting role descriptions',
                    'description': 'Words like "helped" and "assisted" minimize your contributions. Use more powerful alternatives.',
                    'suggestion': 'Replace "helped" with "collaborated", "assisted" with "facilitated", "supported" with "enabled" or "drove".'
                }
            }
        ]

        for pattern_check in patterns_and_suggestions:
            if re.search(pattern_check['pattern'], resume_lower, re.IGNORECASE):
                # Check if similar suggestion already exists
                existing_categories = {s.get('category', '').lower() for s in personalized}
                if pattern_check['suggestion']['category'].lower() not in existing_categories:
                    personalized.append(pattern_check['suggestion'])

        return personalized[:8]  # Limit to 8 total suggestions