"""
Enhanced AI-powered resume screener with Mistral AI integration.

Features:
- Mistral AI as primary intelligence
- Local models (spaCy + sentence-transformers) as fallback
- Intelligent caching for performance
- Comprehensive error handling
"""
import logging
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from functools import lru_cache
import re
from typing import List, Dict, Any, Optional
from django.core.cache import caches

from .mistral_client import mistral_client, MistralAIError

logger = logging.getLogger(__name__)


class AIScreener:
    """
    Hybrid AI-powered resume screener.
    
    Uses Mistral AI for primary analysis with fallback to local models.
    """

    def __init__(self):
        """Initialize AI screener with models."""
        self.cache = caches['default']
        
        # Load local models for fallback
        try:
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None
        
        try:
            self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.similarity_model = None
        
        # Check Mistral AI availability
        self.use_mistral = mistral_client.is_available()
        logger.info(f"Mistral AI {'enabled' if self.use_mistral else 'disabled'}")
        
        # Initialize skill database
        self.skill_database = self._load_skill_database()

    def _load_skill_database(self) -> Dict[str, List[str]]:
        """Load comprehensive skill database with synonyms."""
        return {
            # Programming Languages
            'python': ['python', 'py', 'python3', 'python 3', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'ecmascript', 'node', 'nodejs', 'node.js'],
            'java': ['java', 'j2ee', 'j2se', 'spring', 'spring boot'],
            'typescript': ['typescript', 'ts'],
            'go': ['golang', 'go'],
            'rust': ['rust', 'rust-lang'],
            'c++': ['c++', 'cpp', 'c plus plus'],
            'c#': ['c#', 'csharp', 'c sharp', '.net', 'dotnet'],
            
            # Frameworks
            'react': ['react', 'react.js', 'reactjs', 'react native'],
            'angular': ['angular', 'angularjs', 'angular.js'],
            'vue': ['vue', 'vue.js', 'vuejs'],
            'django': ['django', 'django framework'],
            'flask': ['flask', 'flask framework'],
            
            # Cloud & DevOps
            'aws': ['aws', 'amazon web services', 'amazon aws', 'ec2', 's3', 'lambda'],
            'azure': ['azure', 'microsoft azure'],
            'gcp': ['gcp', 'google cloud', 'google cloud platform'],
            'docker': ['docker', 'containerization', 'containers'],
            'kubernetes': ['kubernetes', 'k8s', 'k9s'],
            
            # Databases
            'sql': ['sql', 'structured query language', 'mysql', 'postgresql', 'sqlite'],
            'nosql': ['nosql', 'mongodb', 'cassandra', 'couchdb'],
            'postgresql': ['postgresql', 'postgres', 'psql'],
            'mongodb': ['mongodb', 'mongo'],
            
            # Data Science & ML
            'machine learning': ['machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch', 'torch'],
            'scikit-learn': ['scikit-learn', 'sklearn', 'scikit'],
            
            # Soft Skills
            'leadership': ['leadership', 'team lead', 'leading teams', 'management'],
            'communication': ['communication', 'presentation', 'public speaking'],
            'project management': ['project management', 'pm', 'agile', 'scrum', 'kanban'],
        }

    @lru_cache(maxsize=1000)
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get sentence embedding with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.similarity_model is None:
            logger.warning("Sentence transformer not available")
            return np.zeros(384)  # Default embedding size
        
        return self.similarity_model.encode(text, show_progress_bar=False)

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume using Mistral AI with local fallback.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Parsed resume data
        """
        # Try Mistral AI first
        if self.use_mistral:
            try:
                parsed = mistral_client.parse_resume(resume_text)
                logger.info("Resume parsed with Mistral AI")
                return parsed
            except MistralAIError as e:
                logger.warning(f"Mistral AI parsing failed, using fallback: {e}")
        
        # Fallback to local parsing
        return self._parse_resume_local(resume_text)

    def _parse_resume_local(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume using local spaCy models.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Parsed resume data
        """
        if self.nlp is None:
            logger.error("spaCy model not available for local parsing")
            return {
                "personal_info": {},
                "summary": resume_text[:200],
                "skills": [],
                "experience": [],
                "education": [],
                "certifications": [],
                "languages": []
            }
        
        doc = self.nlp(resume_text)
        
        # Extract entities
        emails = [ent.text for ent in doc.ents if ent.label_ == 'EMAIL']
        phones = [ent.text for ent in doc.ents if ent.label_ == 'PHONE']
        locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
        
        # Extract skills
        skills = self.extract_skills(resume_text)
        
        # Extract experience years
        experience_years = self.extract_experience_years(resume_text)
        
        # Extract education
        education_level = self.extract_education_level(resume_text)
        
        return {
            "personal_info": {
                "name": "",
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
                "location": locations[0] if locations else ""
            },
            "summary": resume_text[:300],
            "skills": skills,
            "experience": [{
                "title": "",
                "company": "",
                "duration": f"{experience_years} years" if experience_years else "Unknown",
                "description": "",
                "achievements": []
            }] if experience_years else [],
            "education": [{
                "degree": education_level if education_level else "Unknown",
                "institution": "",
                "year": "",
                "field": ""
            }] if education_level else [],
            "certifications": [],
            "languages": []
        }

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text using pattern matching and NLP.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of extracted skills
        """
        text_lower = text.lower()
        skills = set()
        
        # Check against skill database
        for skill, synonyms in self.skill_database.items():
            for synonym in synonyms:
                if re.search(r'\b' + re.escape(synonym) + r'\b', text_lower):
                    skills.add(skill)
                    break
        
        return list(skills)

    def extract_experience_years(self, text: str) -> Optional[float]:
        """
        Extract years of experience from text.
        
        Args:
            text: Text to extract experience from
            
        Returns:
            Years of experience or None
        """
        patterns = [
            r'(\d+)\s*(?:\+)?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*[:\-]?\s*(\d+)\s*(?:\+)?\s*(?:years?|yrs?)',
            r'(\d+)\s*(?:\+)?\s*(?:years?|yrs?)',
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = float(match)
                    max_years = max(max_years, years)
                except ValueError:
                    continue
        
        return max_years if max_years > 0 else None

    def extract_education_level(self, text: str) -> Optional[str]:
        """
        Extract highest education level from text.
        
        Args:
            text: Text to extract education from
            
        Returns:
            Education level or None
        """
        education_levels = [
            ('phd', ['phd', 'ph.d', 'doctorate', 'doctor of philosophy', 'doctoral']),
            ('master', ['master', 'masters', "master's", 'ms', 'msc', 'ma', 'mba', 'm.s.', 'm.a.']),
            ('bachelor', ['bachelor', 'bachelors', "bachelor's", 'bs', 'ba', 'bsc', 'b.s.', 'b.a.']),
            ('associate', ['associate', 'associates', "associate's", 'aa', 'as', 'a.a.', 'a.s.']),
            ('diploma', ['diploma', 'high school', 'secondary school', 'ged'])
        ]
        
        text_lower = text.lower()
        for level, keywords in education_levels:
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return level
        
        return None

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if self.similarity_model is None:
            return 0.0
        
        embedding1 = self._get_embedding(text1)
        embedding2 = self._get_embedding(text2)
        
        similarity = cosine_similarity([embedding1], [embedding2])[0][0]
        return float(similarity)

    def calculate_skills_match(self, resume_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
        """Compute skill overlap metrics for testing and reporting."""
        if not job_skills:
            return {'match_count': 0, 'total_required': 0, 'match_percentage': 0.0}
        normalized_resume = {skill.lower() for skill in (resume_skills or [])}
        normalized_job = {skill.lower() for skill in job_skills}
        matched = normalized_resume & normalized_job
        total_required = len(normalized_job)
        match_percentage = len(matched) / total_required if total_required else 0
        return {
            'match_count': len(matched),
            'total_required': total_required,
            'match_percentage': match_percentage
        }

    def calculate_experience_match(self, years: float, required_years: float, max_years: Optional[float] = None) -> float:
        """Calculate experience score (0-1) capped by optional maximum."""
        if required_years <= 0:
            return 0.0
        if years >= required_years:
            if max_years and years > max_years and max_years > required_years:
                return required_years / max_years
            return 1.0
        return max(0.0, years / required_years)

    def calculate_education_match(self, candidate_degree: str, required_degrees: List[str]) -> float:
        """Score educational alignment on a 0-1 scale."""
        rank_map = {
            'associate': 0.5,
            'bachelor': 1.0,
            'master': 1.2,
            'doctorate': 1.3,
        }
        candidate_rank = rank_map.get((candidate_degree or '').lower(), 0.5)
        required_ranks = [rank_map.get(degree.lower(), 0.5) for degree in (required_degrees or [])]
        min_required = min(required_ranks) if required_ranks else 1.0
        if candidate_rank >= min_required:
            return 1.0
        score = candidate_rank / min_required if min_required else 0.0
        return min(max(score, 0.0), 1.0)

    def calculate_keyword_match(self, text: str, keywords: List[str]) -> float:
        """Return ratio of keywords found in text, clipped between 0 and 1."""
        if not keywords:
            return 0.0
        lower_text = (text or '').lower()
        count = sum(1 for keyword in keywords if keyword.lower() in lower_text)
        return min(1.0, count / len(keywords))

    def calculate_match_score(
        self,
        resume_text: str,
        job_description: str,
        criteria: Optional[Dict] = None,
        application_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score.
        
        Uses Mistral AI if available, falls back to local computation.
        
        Args:
            resume_text: Resume text
            job_description: Job description
            criteria: Screening criteria
            application_data: Optional application-specific data used for screening answers and assessment scoring
            
        Returns:
            Match score and detailed analysis
        """
        criteria = criteria or {}
        required_skills = criteria.get('required_skills', [])
        
        # Try Mistral AI first
        if self.use_mistral:
            try:
                match_data = mistral_client.calculate_match_score(
                    resume_text,
                    job_description,
                    criteria.get('required_skills', [])
                )
                
                # Convert to our format
                details = {
                    'semantic_similarity': match_data.get('overall_score', 0) / 100,
                    'skills_match': match_data.get('skills_match', {}),
                    'experience_match': match_data.get('experience_match', {}).get('score', 0) / 100,
                    'education_match': match_data.get('education_match', {}).get('score', 0) / 100,
                    'strengths': match_data.get('strengths', []),
                    'weaknesses': match_data.get('weaknesses', []),
                    'recommendation': match_data.get('recommendation', ''),
                    'detailed_analysis': match_data.get('detailed_analysis', '')
                }

                if application_data:
                    screening_eval = self.evaluate_screening_answers(
                        application_data.get('screening_answers', []),
                        criteria.get('screening_questions_config', {}) or {}
                    )
                    screening_analysis = dict(screening_eval)
                    screening_analysis['score'] = screening_eval.get('overall_score', screening_analysis.get('score', 0))

                    assessment_eval = self.evaluate_assessments(
                        application_data.get('assessment_results', []),
                        required_skills
                    )
                    assessments_analysis = dict(assessment_eval)
                    assessments_analysis['score'] = assessment_eval.get('overall_score', assessments_analysis.get('score', 0))
                else:
                    screening_analysis = {
                        'score': 0.0,
                        'answers_reviewed': 0,
                        'strengths': [],
                        'concerns': []
                    }
                    assessments_analysis = {
                        'score': 0.0,
                        'tests_taken': 0,
                        'skills_validated': [],
                        'skills_missing': [],
                        'recommendations': []
                    }

                details['screening_answers_analysis'] = screening_analysis
                details['assessments_analysis'] = assessments_analysis

                return {
                    'match_score': match_data.get('overall_score', 0),
                    'match_details': details
                }
            except MistralAIError as e:
                logger.warning(f"Mistral AI match calculation failed: {e}, using fallback")
        
        # Fallback to local calculation
        return self._calculate_match_score_local(resume_text, job_description, criteria, application_data)

    def _calculate_match_score_local(
        self,
        resume_text: str,
        job_description: str,
        criteria: Dict,
        application_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate match score using local models.
        
        Args:
            resume_text: Resume text
            job_description: Job description
            criteria: Screening criteria
            application_data: Optional application context for screening/assessment scoring
            
        Returns:
            Match analysis
        """
        # Extract information
        resume_skills = self.extract_skills(resume_text)
        resume_experience = self.extract_experience_years(resume_text)
        resume_education = self.extract_education_level(resume_text)
        
        # Calculate semantic similarity
        semantic_score = self.calculate_semantic_similarity(resume_text, job_description)
        
        # Calculate skills match
        required_skills = criteria.get('required_skills', [])
        matched_skills = set(resume_skills) & set(required_skills)
        skills_score = len(matched_skills) / len(required_skills) if required_skills else 0
        
        # Calculate experience match
        min_exp = criteria.get('min_experience_years', 0)
        max_exp = criteria.get('max_experience_years')
        
        if resume_experience:
            if resume_experience >= min_exp:
                if max_exp and resume_experience > max_exp:
                    exp_score = 0.8  # Slight penalty for overqualification
                else:
                    exp_score = 1.0
            else:
                exp_score = resume_experience / min_exp if min_exp > 0 else 0.5
        else:
            exp_score = 0.5
        
        # Calculate education match
        required_education = criteria.get('required_education', [])
        education_hierarchy = {
            'diploma': 1,
            'associate': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5
        }
        
        resume_edu_level = education_hierarchy.get(resume_education, 0)
        required_edu_levels = [education_hierarchy.get(edu.lower(), 0) for edu in required_education]
        
        if required_edu_levels:
            min_required = min(required_edu_levels)
            edu_score = 1.0 if resume_edu_level >= min_required else resume_edu_level / min_required
        else:
            edu_score = 0.8
        
        # Calculate weighted final score
        weights = {
            'semantic': 0.3,
            'skills': criteria.get('weight_skills', 0.4),
            'experience': criteria.get('weight_experience', 0.2),
            'education': criteria.get('weight_education', 0.1)
        }
        
        screening_answers_score = 0.0
        assessments_score = 0.0
        screening_analysis = {
            'score': 0.0,
            'answers_reviewed': 0,
            'strengths': [],
            'concerns': []
        }
        assessments_analysis = {
            'score': 0.0,
            'tests_taken': 0,
            'skills_validated': [],
            'skills_missing': [],
            'recommendations': []
        }

        if application_data:
            screening_eval = self.evaluate_screening_answers(
                application_data.get('screening_answers', []),
                criteria.get('screening_questions_config', {}) or {}
            )
            screening_answers_score = screening_eval.get('overall_score', 50) / 100
            screening_analysis = dict(screening_eval)
            screening_analysis['score'] = screening_eval.get('overall_score', screening_analysis.get('score', 0))

            assessment_results = application_data.get('assessment_results', [])
            assessment_eval = self.evaluate_assessments(assessment_results, required_skills)
            assessments_score = assessment_eval.get('overall_score', 0) / 100
            assessments_analysis.update({
                'score': assessment_eval.get('overall_score', 0),
                'tests_taken': assessment_eval.get('tests_taken', 0),
                'skills_validated': assessment_eval.get('skills_validated', []),
                'skills_missing': assessment_eval.get('skills_missing', []),
                'recommendations': assessment_eval.get('recommendations', [])
            })

        # When application context exists, normalize the expanded weight set.
        if application_data:
            raw_weights = {
                'semantic': 0.25,
                'skills': criteria.get('weight_skills', 0.3),
                'experience': criteria.get('weight_experience', 0.2),
                'education': criteria.get('weight_education', 0.1),
                'screening': criteria.get('weight_screening_questions', 0.1),
                'assessments': criteria.get('weight_assessments', 0.1),
            }
            total_weight = sum(raw_weights.values())
            normalized = {
                key: (value / total_weight if total_weight else 0)
                for key, value in raw_weights.items()
            }

            final_score = (
                semantic_score * normalized['semantic'] +
                skills_score * normalized['skills'] +
                exp_score * normalized['experience'] +
                edu_score * normalized['education'] +
                screening_answers_score * normalized['screening'] +
                assessments_score * normalized['assessments']
            ) * 100
        else:
            final_score = (
                semantic_score * weights['semantic'] +
                skills_score * weights['skills'] +
                exp_score * weights['experience'] +
                edu_score * weights['education'] +
                screening_answers_score * criteria.get('weight_screening_questions', 0.1) +
                assessments_score * criteria.get('weight_assessments', 0.1)
            ) * 100

        details = {
            'semantic_similarity': semantic_score,
            'skills_match': {
                'matched': list(matched_skills),
                'missing': list(set(required_skills) - matched_skills),
                'score': skills_score * 100
            },
            'experience_match': exp_score,
            'education_match': edu_score,
            'resume_skills': resume_skills,
            'resume_experience_years': resume_experience,
            'resume_education': resume_education,
            'screening_answers_analysis': screening_analysis,
            'assessments_analysis': assessments_analysis
        }

        return {
            'match_score': round(min(final_score, 100), 2),
            'match_details': details
        }

    def evaluate_screening_answers(self, answers_list, criteria_config):
        """Evaluate screening answers against configured expectations.

        Args:
            answers_list (list[dict]): Candidate responses stored on the application.
            criteria_config (dict): Screening question configuration (expected answers and keywords).

        Returns:
            dict: Contains overall_score (0-100), answers_breakdown, strengths, and red_flags.
        """
        if not answers_list:
            return {
                'overall_score': 50,
                'answers_breakdown': [],
                'red_flags': [],
                'strengths': []
            }

        if not isinstance(answers_list, list):
            logger.warning("Invalid screening answers format: expected list, got %s", type(answers_list))
            return {
                'overall_score': 50,
                'answers_breakdown': [],
                'red_flags': [],
                'strengths': []
            }

        expected_answers = (criteria_config or {}).get('expected_answers', {})
        breakdown = []
        strengths = []
        red_flags = []

        for entry in answers_list:
            if not isinstance(entry, dict):
                logger.warning("Skipping invalid screening answer entry: %s", entry)
                continue

            question_key = entry.get('question') or entry.get('label') or entry.get('question_text', 'Unknown question')
            qtype = (entry.get('question_type') or entry.get('type') or 'text').lower()
            answer = (entry.get('answer') or entry.get('response') or '') or ''
            score = 0
            feedback = ''

            config = expected_answers.get(question_key, {})
            expected_value = config.get('value')
            keyword_list = config.get('keywords', [])

            if qtype == 'multiple_choice':
                if expected_value and answer.strip().lower() == expected_value.strip().lower():
                    score = 100
                    feedback = 'Matched expected choice'
                elif answer:
                    score = 60
                    feedback = 'Answered but did not match expectation'
                else:
                    score = 0
                    feedback = 'No response'

            elif qtype == 'yes_no':
                normalized = answer.strip().lower()
                if expected_value and normalized == expected_value.strip().lower():
                    score = 100
                    feedback = 'Matched required yes/no'
                elif normalized in ('yes', 'y', 'true', 'no', 'n', 'false'):
                    score = 60
                    feedback = 'Answered yes/no but not matching expectation'
                else:
                    score = 0
                    feedback = 'Missing yes/no answer'

            else:
                tokens = len(answer.split())
                score = min(100, tokens * 5)
                feedback = 'Free-text response captured'
                found_keyword = False
                for keyword in keyword_list or []:
                    if isinstance(keyword, str) and keyword.lower() in answer.lower():
                        score = min(100, score + 20)
                        found_keyword = True
                        feedback = f'Included keyword: {keyword}'
                if not answer:
                    score = 0
                    feedback = 'No response provided'
                elif not found_keyword and keyword_list:
                    feedback = 'Answer provided without matching keywords'

            score = min(max(score, 0), 100)
            breakdown.append({
                'question': question_key,
                'score': score,
                'feedback': feedback
            })

            if score >= 80:
                strengths.append(question_key)
            if score < 40:
                red_flags.append(question_key)

        overall = 50
        if breakdown:
            overall = sum(item['score'] for item in breakdown) / len(breakdown)

        return {
            'overall_score': overall,
            'answers_breakdown': breakdown,
            'red_flags': list(dict.fromkeys(red_flags)),
            'strengths': list(dict.fromkeys(strengths))
        }

    def evaluate_assessments(self, assessment_results, required_skills):
        """Summarize assessment performance versus required skills.

        Args:
            assessment_results (list[dict]): Completed assessment payloads from ApplicationDataService.
            required_skills (iterable): Skills defined on the screening criteria.

        Returns:
            dict: Summary with overall_score, tests_taken, skills_validated, missing skills, and recommendations.
        """
        required_skills = {skill.lower() for skill in (required_skills or [])}
        if not assessment_results:
            return {
                'overall_score': 0,
                'tests_taken': 0,
                'skills_validated': [],
                'skills_missing': sorted(list(required_skills)) if required_skills else [],
                'recommendations': ["No assessments completed; consider assigning relevant tests."]
            }

        total_score = 0
        validated_skills = set()
        tests_taken = 0

        for attempt in assessment_results:
            tests_taken += 1
            score = attempt.get('score') or 0
            total_score += score
            skills = attempt.get('skills_validated') or []
            if isinstance(skills, str):
                skills = [skills]
            for skill in skills:
                if isinstance(skill, str):
                    validated_skills.add(skill.lower())

        avg_score = total_score / tests_taken if tests_taken else 0
        coverage = 0
        if required_skills:
            overlap = required_skills & validated_skills
            coverage = len(overlap) / len(required_skills)
        else:
            overlap = set()
            coverage = 1.0

        boost = coverage * 10
        final_score = min(100, avg_score + boost)

        skills_missing = sorted(list(required_skills - overlap)) if required_skills else []

        recommendations = []
        if not coverage:
            recommendations.append("Assessments did not cover the required skills; add relevant tests.")
        if skills_missing:
            recommendations.append(f"Consider assessments for: {', '.join(skills_missing)}")

        return {
            'overall_score': final_score,
            'tests_taken': tests_taken,
            'skills_validated': sorted(list(overlap)),
            'skills_missing': skills_missing,
            'recommendations': recommendations or ["Assessments focused on required skills."]
        }

    def generate_match_explanation(self, match_result: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of match result.
        
        Args:
            match_result: Match result from calculate_match_score
            
        Returns:
            Human-readable explanation
        """
        score = match_result['match_score']
        details = match_result['match_details']
        
        # Check if we have Mistral AI detailed analysis
        if 'detailed_analysis' in details and details['detailed_analysis']:
            return details['detailed_analysis']
        
        # Generate local explanation
        explanation = []
        explanation.append(f"Match Score: {score:.0f}%\n")
        
        if score >= 90:
            explanation.append("🌟 EXCELLENT MATCH - Highly recommended!")
        elif score >= 80:
            explanation.append("👍 STRONG MATCH - Recommended for interview")
        elif score >= 70:
            explanation.append("✓ GOOD MATCH - Worth considering")
        elif score >= 60:
            explanation.append("~ POTENTIAL MATCH - May need training")
        else:
            explanation.append("✗ WEAK MATCH - Not recommended")
        
        # Skills section
        skills_match = details.get('skills_match', {})
        if isinstance(skills_match, dict):
            matched = skills_match.get('matched', [])
            missing = skills_match.get('missing', [])
            
            if matched:
                explanation.append(f"\n✓ Matched Skills: {', '.join(matched)}")
            if missing:
                explanation.append(f"\n✗ Missing Skills: {', '.join(missing)}")
        
        # Experience
        exp_match = details.get('experience_match')
        if exp_match:
            explanation.append(f"\nExperience Match: {exp_match * 100:.0f}%")
        
        # Strengths and weaknesses (if from Mistral AI)
        if 'strengths' in details and details['strengths']:
            explanation.append(f"\nStrengths: {', '.join(details['strengths'])}")
        if 'weaknesses' in details and details['weaknesses']:
            explanation.append(f"\nAreas for Development: {', '.join(details['weaknesses'])}")
        
        if 'recommendation' in details and details['recommendation']:
            explanation.append(f"\nRecommendation: {details['recommendation']}")
        
        return '\n'.join(explanation)


# Singleton instance
ai_screener = AIScreener()
