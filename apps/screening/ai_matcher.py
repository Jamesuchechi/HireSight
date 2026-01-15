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

    def calculate_match_score(
        self,
        resume_text: str,
        job_description: str,
        criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score.
        
        Uses Mistral AI if available, falls back to local computation.
        
        Args:
            resume_text: Resume text
            job_description: Job description
            criteria: Screening criteria
            
        Returns:
            Match score and detailed analysis
        """
        criteria = criteria or {}
        
        # Try Mistral AI first
        if self.use_mistral:
            try:
                match_data = mistral_client.calculate_match_score(
                    resume_text,
                    job_description,
                    criteria.get('required_skills', [])
                )
                
                # Convert to our format
                return {
                    'match_score': match_data.get('overall_score', 0),
                    'match_details': {
                        'semantic_similarity': match_data.get('overall_score', 0) / 100,
                        'skills_match': match_data.get('skills_match', {}),
                        'experience_match': match_data.get('experience_match', {}).get('score', 0) / 100,
                        'education_match': match_data.get('education_match', {}).get('score', 0) / 100,
                        'strengths': match_data.get('strengths', []),
                        'weaknesses': match_data.get('weaknesses', []),
                        'recommendation': match_data.get('recommendation', ''),
                        'detailed_analysis': match_data.get('detailed_analysis', '')
                    }
                }
            except MistralAIError as e:
                logger.warning(f"Mistral AI match calculation failed: {e}, using fallback")
        
        # Fallback to local calculation
        return self._calculate_match_score_local(resume_text, job_description, criteria)

    def _calculate_match_score_local(
        self,
        resume_text: str,
        job_description: str,
        criteria: Dict
    ) -> Dict[str, Any]:
        """
        Calculate match score using local models.
        
        Args:
            resume_text: Resume text
            job_description: Job description
            criteria: Screening criteria
            
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
        
        final_score = (
            semantic_score * weights['semantic'] +
            skills_score * weights['skills'] +
            exp_score * weights['experience'] +
            edu_score * weights['education']
        ) * 100
        
        return {
            'match_score': round(min(final_score, 100), 2),
            'match_details': {
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
                'resume_education': resume_education
            }
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