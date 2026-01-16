"""
Resume optimization utilities for HireSight.
Provides AI-powered resume analysis and optimization suggestions.
"""

import re
import json
import textwrap
from typing import Dict, List, Any, Tuple
from collections import Counter
import requests
from django.conf import settings


class ActionVerbAnalyzer:
    """Analyze action verbs in resume text."""

    # Strong action verbs by category
    STRONG_VERBS = {
        'leadership': [
            'led', 'directed', 'managed', 'supervised', 'coordinated', 'oversaw',
            'guided', 'mentored', 'trained', 'delegated', 'orchestrated', 'spearheaded'
        ],
        'achievement': [
            'achieved', 'accomplished', 'delivered', 'exceeded', 'surpassed', 'improved',
            'increased', 'reduced', 'enhanced', 'optimized', 'streamlined', 'accelerated'
        ],
        'communication': [
            'presented', 'negotiated', 'collaborated', 'liaised', 'corresponded',
            'facilitated', 'mediated', 'advised', 'consulted', 'influenced', 'persuaded'
        ],
        'technical': [
            'developed', 'implemented', 'designed', 'engineered', 'programmed',
            'configured', 'integrated', 'deployed', 'maintained', 'debugged', 'optimized'
        ],
        'analytical': [
            'analyzed', 'researched', 'investigated', 'evaluated', 'assessed',
            'identified', 'diagnosed', 'quantified', 'measured', 'calculated', 'forecasted'
        ],
        'creative': [
            'created', 'designed', 'innovated', 'conceptualized', 'developed',
            'crafted', 'produced', 'generated', 'formulated', 'invented'
        ]
    }

    # Weak verbs to avoid
    WEAK_VERBS = [
        'was', 'were', 'is', 'are', 'am', 'be', 'been', 'being',
        'did', 'do', 'does', 'done', 'doing',
        'had', 'has', 'have', 'having',
        'worked', 'worked on', 'responsible for', 'in charge of',
        'helped', 'assisted', 'supported'
    ]

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze action verbs in resume text."""
        text_lower = text.lower()

        # Count strong verbs by category
        strong_verb_counts = {}
        total_strong_verbs = 0

        for category, verbs in self.STRONG_VERBS.items():
            count = 0
            found_verbs = []
            for verb in verbs:
                # Count occurrences (word boundaries)
                matches = len(re.findall(r'\b' + re.escape(verb) + r'\b', text_lower))
                if matches > 0:
                    count += matches
                    found_verbs.extend([verb] * matches)
            strong_verb_counts[category] = {
                'count': count,
                'verbs': found_verbs[:10]  # Limit to top 10
            }
            total_strong_verbs += count

        # Count weak verbs
        weak_verb_count = 0
        found_weak_verbs = []
        for verb in self.WEAK_VERBS:
            matches = len(re.findall(r'\b' + re.escape(verb) + r'\b', text_lower))
            if matches > 0:
                weak_verb_count += matches
                found_weak_verbs.extend([verb] * matches)

        # Calculate score (0-100)
        if total_strong_verbs + weak_verb_count == 0:
            score = 50  # Neutral score if no verbs found
        else:
            score = min(100, (total_strong_verbs / (total_strong_verbs + weak_verb_count)) * 100)

        return {
            'score': round(score, 1),
            'strong_verbs': strong_verb_counts,
            'total_strong_verbs': total_strong_verbs,
            'weak_verbs': {
                'count': weak_verb_count,
                'verbs': found_weak_verbs[:10]
            },
            'recommendations': self._generate_recommendations(strong_verb_counts, weak_verb_count)
        }

    def _generate_recommendations(self, strong_verbs: Dict, weak_verb_count: int) -> List[str]:
        """Generate recommendations for action verb improvement."""
        recommendations = []

        # Check for categories with low usage
        low_usage_categories = []
        for category, data in strong_verbs.items():
            if data['count'] < 2:  # Less than 2 verbs per category
                low_usage_categories.append(category.title())

        if low_usage_categories:
            recommendations.append(
                f"Add more {', '.join(low_usage_categories)} action verbs to strengthen your resume."
            )

        if weak_verb_count > 5:
            recommendations.append(
                "Replace weak verbs like 'was responsible for' with strong action verbs like 'managed' or 'led'."
            )

        # Suggest specific verbs for underused categories
        for category, data in strong_verbs.items():
            if data['count'] == 0:
                sample_verbs = self.STRONG_VERBS[category][:3]
                recommendations.append(
                    f"Consider using {category} verbs like: {', '.join(sample_verbs)}"
                )

        return recommendations


class KeywordOptimizer:
    """Optimize keywords for job applications."""

    def __init__(self):
        self.common_job_keywords = {
            'technical': [
                'python', 'javascript', 'java', 'sql', 'react', 'node.js', 'aws', 'docker',
                'kubernetes', 'git', 'agile', 'scrum', 'ci/cd', 'api', 'database', 'linux'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
                'project management', 'customer service', 'time management'
            ],
            'business': [
                'sales', 'marketing', 'strategy', 'analysis', 'reporting', 'budget',
                'forecasting', 'negotiation', 'stakeholder management'
            ]
        }

    def analyze_keywords(self, resume_text: str, job_description: str = None) -> Dict[str, Any]:
        """Analyze keyword usage in resume."""
        resume_lower = resume_text.lower()

        # Count keyword occurrences
        keyword_counts = {}
        total_keywords = 0

        for category, keywords in self.common_job_keywords.items():
            category_counts = {}
            category_total = 0

            for keyword in keywords:
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', resume_lower))
                if count > 0:
                    category_counts[keyword] = count
                    category_total += count

            keyword_counts[category] = {
                'keywords': category_counts,
                'total': category_total
            }
            total_keywords += category_total

        # Calculate density score
        word_count = len(resume_text.split())
        density_score = min(100, (total_keywords / max(word_count, 1)) * 1000)  # Keywords per 1000 words

        # Job-specific analysis if job description provided
        job_match_score = 0
        missing_keywords = []

        if job_description:
            job_keywords = self._extract_job_keywords(job_description.lower())
            job_match_score, missing_keywords = self._calculate_job_match(resume_lower, job_keywords)

        return {
            'density_score': round(density_score, 1),
            'keyword_counts': keyword_counts,
            'total_keywords': total_keywords,
            'job_match_score': round(job_match_score, 1) if job_description else None,
            'missing_keywords': missing_keywords,
            'recommendations': self._generate_keyword_recommendations(keyword_counts, missing_keywords)
        }

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description."""
        # Simple extraction - could be enhanced with NLP
        all_keywords = []
        for category_keywords in self.common_job_keywords.values():
            all_keywords.extend(category_keywords)

        found_keywords = []
        for keyword in all_keywords:
            if keyword in job_description:
                found_keywords.append(keyword)

        return found_keywords

    def _calculate_job_match(self, resume_text: str, job_keywords: List[str]) -> Tuple[float, List[str]]:
        """Calculate how well resume matches job keywords."""
        if not job_keywords:
            return 0, []

        matched_keywords = []
        missing_keywords = []

        for keyword in job_keywords:
            if keyword in resume_text:
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        match_score = (len(matched_keywords) / len(job_keywords)) * 100
        return match_score, missing_keywords

    def _generate_keyword_recommendations(self, keyword_counts: Dict, missing_keywords: List[str]) -> List[str]:
        """Generate keyword optimization recommendations."""
        recommendations = []

        # Check for low keyword density
        total_keywords = sum(cat['total'] for cat in keyword_counts.values())
        if total_keywords < 5:
            recommendations.append("Add more industry-relevant keywords to improve ATS compatibility.")

        # Suggest missing keywords
        if missing_keywords:
            top_missing = missing_keywords[:5]
            recommendations.append(f"Consider adding these job-relevant keywords: {', '.join(top_missing)}")

        # Check category balance
        categories = list(keyword_counts.keys())
        totals = [keyword_counts[cat]['total'] for cat in categories]

        if max(totals) > min(totals) * 3:  # Imbalanced
            max_cat = categories[totals.index(max(totals))]
            min_cat = categories[totals.index(min(totals))]
            recommendations.append(f"Balance your keywords - you have more {max_cat} terms than {min_cat} terms.")

        return recommendations


class ATSScorer:
    """Score resumes for ATS compatibility."""

    def calculate_ats_score(self, resume_text: str, resume_data: Dict = None) -> Dict[str, Any]:
        """Calculate overall ATS compatibility score."""
        scores = {}

        # Length and formatting score
        scores['length'] = self._score_length(resume_text)
        scores['formatting'] = self._score_formatting(resume_text)
        scores['structure'] = self._score_structure(resume_text)
        scores['keywords'] = self._score_keywords(resume_text, resume_data or {})
        scores['readability'] = self._score_readability(resume_text)

        # Calculate weighted overall score
        weights = {
            'length': 0.2,
            'formatting': 0.2,
            'structure': 0.25,
            'keywords': 0.25,
            'readability': 0.1
        }

        overall_score = sum(scores[component] * weights[component] for component in scores.keys())

        return {
            'overall_score': round(overall_score, 1),
            'component_scores': scores,
            'issues': self._identify_issues(scores),
            'recommendations': self._generate_ats_recommendations(scores)
        }

    def _score_length(self, text: str) -> float:
        """Score resume length (ideal: 400-800 words)."""
        word_count = len(text.split())
        if 400 <= word_count <= 800:
            return 100
        elif 300 <= word_count <= 1000:
            return 80
        elif 200 <= word_count <= 1200:
            return 60
        else:
            return 40

    def _score_formatting(self, text: str) -> float:
        """Score formatting (simple text analysis)."""
        score = 100

        # Penalize excessive special characters
        special_chars = len(re.findall(r'[^\w\s]', text))
        if special_chars > len(text) * 0.05:  # More than 5% special chars
            score -= 20

        # Penalize very long lines (might indicate formatting issues)
        lines = text.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > len(lines) * 0.3:  # More than 30% long lines
            score -= 15

        return max(0, score)

    def _score_structure(self, text: str) -> float:
        """Score resume structure (presence of sections)."""
        text_lower = text.lower()
        sections = ['experience', 'education', 'skills', 'contact', 'summary', 'objective']
        found_sections = sum(1 for section in sections if section in text_lower)

        # Score based on sections found
        if found_sections >= 4:
            return 100
        elif found_sections >= 3:
            return 80
        elif found_sections >= 2:
            return 60
        else:
            return 40

    def _score_keywords(self, text: str, resume_data: Dict) -> float:
        """Score keyword optimization."""
        optimizer = KeywordOptimizer()
        analysis = optimizer.analyze_keywords(text)

        # Base score on keyword density
        density = analysis['density_score']
        if density >= 20:
            return 100
        elif density >= 15:
            return 80
        elif density >= 10:
            return 60
        else:
            return 40

    def _score_readability(self, text: str) -> float:
        """Score readability (sentence length, complexity)."""
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length <= 20:
            return 100
        elif avg_sentence_length <= 25:
            return 80
        elif avg_sentence_length <= 30:
            return 60
        else:
            return 40

    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identify specific ATS issues."""
        issues = []

        if scores['length'] < 70:
            word_count = len("sample text".split())  # This would need actual word count
            issues.append("Resume length may be too short or too long for ATS parsing")

        if scores['formatting'] < 70:
            issues.append("Formatting issues detected that may confuse ATS")

        if scores['structure'] < 70:
            issues.append("Missing standard resume sections")

        if scores['keywords'] < 70:
            issues.append("Low keyword density may reduce ATS ranking")

        if scores['readability'] < 70:
            issues.append("Complex sentence structure may affect parsing")

        return issues

    def _generate_ats_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate ATS improvement recommendations."""
        recommendations = []

        if scores['length'] < 70:
            recommendations.append("Aim for 400-800 words to optimize ATS parsing")

        if scores['formatting'] < 70:
            recommendations.append("Use simple formatting - avoid complex layouts, tables, or graphics")

        if scores['structure'] < 70:
            recommendations.append("Include standard sections: Contact Info, Summary, Experience, Education, Skills")

        if scores['keywords'] < 70:
            recommendations.append("Incorporate relevant keywords naturally throughout your resume")

        if scores['readability'] < 70:
            recommendations.append("Use shorter sentences and simpler language for better ATS parsing")

        return recommendations


class MistralResumeAdvisor:
    """AI-powered resume optimization using Mistral API."""

    def __init__(self):
        self.api_key = getattr(settings, 'MISTRAL_API_KEY', None) or getattr(settings, 'MISTRAL_AI_API_KEY', None)
        base_url = getattr(settings, 'MISTRAL_API_URL', None) or getattr(settings, 'MISTRAL_AI_BASE_URL', 'https://api.mistral.ai/v1')
        if base_url.endswith('/chat/completions'):
            self.api_url = base_url
        else:
            self.api_url = base_url.rstrip('/') + '/chat/completions'
        self.model = getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-medium')

    def generate_suggestions(self, resume_text: str, job_description: str = None) -> Dict[str, Any]:
        """Generate AI-powered resume optimization suggestions."""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Mistral API key not configured',
                'suggestions': []
            }

        try:
            prompt = self._build_prompt(resume_text, job_description)
            response = self._call_mistral_api(prompt)

            if response and 'choices' in response:
                suggestions_text = response['choices'][0]['message']['content']
                suggestions = self._parse_suggestions(suggestions_text)

                return {
                    'success': True,
                    'suggestions': suggestions,
                    'raw_response': suggestions_text
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid API response',
                    'suggestions': []
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestions': []
            }

    def _build_prompt(self, resume_text: str, job_description: str = None) -> str:
        """Build the prompt for Mistral API."""
        prompt = f"""
You are an expert resume optimization consultant. Analyze the following resume and provide specific, actionable suggestions for improvement.

Resume Text:
{resume_text[:2000]}  # Limit to first 2000 chars

"""

        if job_description:
            prompt += f"""
Job Description (for tailoring suggestions):
{job_description[:1000]}

"""

        prompt += """
Please provide suggestions in the following format:

1. **IMPACT LEVEL**: [HIGH/MEDIUM/LOW]
   **CATEGORY**: [Action Verbs/Formatting/Content/Keywords/Structure]
   **SUGGESTION**: [Specific actionable advice]
   **EXAMPLE**: [Before and after example if applicable]

Focus on:
- Strong action verbs vs weak verbs
- Quantifiable achievements
- ATS compatibility
- Keyword optimization
- Clear structure and formatting
- Relevance to target job

Provide 3-5 specific suggestions.
"""

        return prompt

    def _call_mistral_api(self, prompt: str) -> Dict:
        """Call Mistral API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 1000,
            'temperature': 0.7
        }

        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()

    def _parse_suggestions(self, suggestions_text: str) -> List[Dict[str, Any]]:
        """Parse AI suggestions into structured format."""
        suggestions = []

        # Simple parsing - split by numbered items
        items = re.split(r'\d+\.\s+', suggestions_text)[1:]  # Skip first empty item

        for item in items:
            if not item.strip():
                continue

            suggestion = {
                'impact_level': 'medium',
                'category': 'general',
                'title': '',
                'description': item.strip()[:200],
                'suggestion': item.strip(),
                'example_before': '',
                'example_after': ''
            }

            # Try to extract structured info
            if '**IMPACT LEVEL**:' in item:
                impact_match = re.search(r'\*\*IMPACT LEVEL\*\*:\s*(\w+)', item, re.IGNORECASE)
                if impact_match:
                    suggestion['impact_level'] = impact_match.group(1).lower()

            if '**CATEGORY**:' in item:
                category_match = re.search(r'\*\*CATEGORY\*\*:\s*([^\\n]+)', item, re.IGNORECASE)
                if category_match:
                    suggestion['category'] = category_match.group(1).strip().lower()

            if '**SUGGESTION**:' in item:
                suggestion_match = re.search(r'\*\*SUGGESTION\*\*:\s*([^\\n]+)', item, re.IGNORECASE)
                if suggestion_match:
                    suggestion['title'] = suggestion_match.group(1).strip()[:100]

            suggestions.append(suggestion)

            if len(suggestions) >= 5:  # Limit to 5 suggestions
                break

        return suggestions

    def generate_rewrite(self, resume_text: str, job_title: str = None, industry: str = None,
                         highlights: str = None, metrics_focus: str = None, job_description: str = None) -> Dict[str, Any]:
        """Generate a rewritten resume using the Mistral API."""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Mistral API key not configured. Please set MISTRAL_API_KEY to enable rewrites.',
                'rewritten_text': ''
            }

        try:
            prompt = self._build_rewrite_prompt(
                resume_text,
                job_title=job_title,
                industry=industry,
                highlights=highlights,
                metrics_focus=metrics_focus,
                job_description=job_description
            )
            response = self._call_mistral_api(prompt)

            if response and 'choices' in response:
                suggestions_text = response['choices'][0]['message']['content']
                return {
                    'success': True,
                    'rewritten_text': suggestions_text.strip(),
                    'raw_response': suggestions_text
                }

            return {
                'success': False,
                'error': 'Invalid rewrite response from AI',
                'rewritten_text': ''
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'rewritten_text': ''
            }

    def _build_rewrite_prompt(self, resume_text: str, job_title: str = None, industry: str = None,
                              highlights: str = None, metrics_focus: str = None, job_description: str = None) -> str:
        """Build a specialized prompt for rewriting resumes."""
        base_text = resume_text[:4000]
        prompt = textwrap.dedent(f"""
        You are an expert resume writer. Rewrite the resume below so it follows modern resume conventions, highlights achievements, and addresses any gaps related to the provided role context.

        Original Resume:
        {base_text}
        """).strip()

        additional_context = []
        if job_title:
            additional_context.append(f"Target Job Title: {job_title}")
        if industry:
            additional_context.append(f"Industry: {industry}")
        if highlights:
            additional_context.append(f"Highlights to emphasize: {highlights}")
        if metrics_focus:
            additional_context.append(f"Metrics focus: {metrics_focus}")
        if job_description:
            additional_context.append(f"Job Description/Goals:\n{job_description[:2000]}")

        if additional_context:
            prompt += "\n\nContext:\n" + "\n".join(additional_context)

        prompt += textwrap.dedent("""

        Instructions:
        - Output a rewritten resume with clearly labeled sections (Summary, Experience, Skills, Education, etc.).
        - Use strong action verbs, quantify achievements where possible, and improve ATS readability.
        - Keep formatting simple (no tables), but use bullet points and short paragraphs.
        - Do not explain your process, only return the rewritten resume text.
        """)

        return prompt


class ResumeOptimizer:
    """Main resume optimization orchestrator."""

    def __init__(self):
        self.action_analyzer = ActionVerbAnalyzer()
        self.keyword_optimizer = KeywordOptimizer()
        self.ats_scorer = ATSScorer()
        self.ai_advisor = MistralResumeAdvisor()

    def optimize_resume(self, resume_text: str, job_description: str = None) -> Dict[str, Any]:
        """Run complete resume optimization analysis."""
        results = {}

        # Action verb analysis
        results['action_verbs'] = self.action_analyzer.analyze_text(resume_text)

        # Keyword analysis
        results['keywords'] = self.keyword_optimizer.analyze_keywords(resume_text, job_description)

        # ATS scoring
        resume_data = {
            'skills': results['keywords']['keyword_counts'],
            'experience_years': len(re.findall(r'\b\d+\s+years?\b', resume_text.lower()))
        }
        results['ats'] = self.ats_scorer.calculate_ats_score(resume_text, resume_data)

        # AI suggestions (optional - only if API key configured)
        ai_results = self.ai_advisor.generate_suggestions(resume_text, job_description)
        results['ai_suggestions'] = ai_results.get('suggestions', [])

        # Calculate overall optimization score
        component_scores = [
            results['action_verbs']['score'],
            results['keywords']['density_score'] * 2,  # Weight keywords more
            results['ats']['overall_score']
        ]

        overall_score = sum(component_scores) / len(component_scores)
        results['overall_score'] = round(overall_score, 1)

        return results
