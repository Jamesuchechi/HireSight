import re
import spacy
from typing import Dict, List, Optional
from django.conf import settings
import fitz  # PyMuPDF for PDF parsing
from docx import Document  # python-docx for DOCX parsing


class ResumeParser:
    """AI-powered resume parser using spaCy."""

    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model not available
            self.nlp = None

    def parse_file(self, file_path: str, filename: str) -> Dict:
        """
        Parse resume file and extract structured data.

        Args:
            file_path: Path to the uploaded file
            filename: Original filename

        Returns:
            Dict containing parsed data
        """
        # Extract text from file
        text = self._extract_text(file_path, filename)

        if not text:
            return {
                'success': False,
                'error': 'Could not extract text from file'
            }

        # Parse text with NLP
        parsed_data = self._parse_text(text)

        return {
            'success': True,
            'text': text,
            **parsed_data
        }

    def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text from PDF or DOCX file."""
        file_extension = filename.lower().split('.')[-1]

        try:
            if file_extension == 'pdf':
                return self._extract_pdf_text(file_path)
            elif file_extension == 'docx':
                return self._extract_docx_text(file_path)
            else:
                return ""
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def _parse_text(self, text: str) -> Dict:
        """Parse text using NLP to extract structured data."""
        if not self.nlp:
            return self._parse_text_fallback(text)

        doc = self.nlp(text)

        # Extract skills
        skills = self._extract_skills(doc)

        # Extract experience
        experience_years = self._extract_experience_years(text)

        # Extract education
        education = self._extract_education(doc)

        # Extract contact info
        contact_info = self._extract_contact_info(text)

        return {
            'skills': skills,
            'experience_years': experience_years,
            'education': education,
            'contact_info': contact_info,
        }

    def _extract_skills(self, doc) -> List[str]:
        """Extract skills from parsed document."""
        skills = []

        # Common tech skills to look for
        tech_skills = {
            'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'go', 'rust',
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'nodejs',
            'html', 'css', 'sass', 'tailwind', 'bootstrap',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'linux', 'bash', 'powershell',
            'machine learning', 'ai', 'nlp', 'computer vision', 'deep learning',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
        }

        # Extract nouns and proper nouns as potential skills
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                skill = token.text.lower()
                if skill in tech_skills or self._is_technical_skill(skill):
                    skills.append(token.text)

        # Remove duplicates and sort
        return list(set(skills))

    def _is_technical_skill(self, word: str) -> bool:
        """Check if a word looks like a technical skill."""
        # Simple heuristic: contains programming-related keywords
        tech_indicators = ['api', 'web', 'data', 'cloud', 'dev', 'code', 'script']
        return any(indicator in word for indicator in tech_indicators)

    def _extract_experience_years(self, text: str) -> Optional[float]:
        """Extract years of experience from text."""
        # Look for patterns like "5 years", "3+ years", etc.
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:\+?\s*)?years?\s*(?:of\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:\+?\s*)?years?',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the highest number found
                years = max(float(match) for match in matches)
                return years

        return None

    def _extract_education(self, doc) -> List[Dict]:
        """Extract education information."""
        education = []

        # Look for education keywords
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']

        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in education_keywords):
                education.append({
                    'text': sent.text.strip(),
                    'degree': self._extract_degree(sent.text),
                    'institution': self._extract_institution(sent.text)
                })

        return education

    def _extract_degree(self, text: str) -> str:
        """Extract degree from education text."""
        degrees = ['PhD', 'Master', 'Bachelor', 'MBA', 'MS', 'BS', 'BA']
        for degree in degrees:
            if degree.lower() in text.lower():
                return degree
        return ""

    def _extract_institution(self, text: str) -> str:
        """Extract institution name from education text."""
        # Simple extraction - look for capitalized words after degree
        words = text.split()
        institutions = []
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 3:
                institutions.append(word)
        return " ".join(institutions)

    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information."""
        contact_info = {}

        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]

        # Phone regex (simple)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]

        # LinkedIn URL
        linkedin_pattern = r'linkedin\.com/in/[^\s]+'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin:
            contact_info['linkedin'] = linkedin[0]

        return contact_info

    def _parse_text_fallback(self, text: str) -> Dict:
        """Fallback parsing without spaCy."""
        return {
            'skills': [],
            'experience_years': None,
            'education': [],
            'contact_info': self._extract_contact_info(text),
        }


# Global parser instance
resume_parser = ResumeParser()