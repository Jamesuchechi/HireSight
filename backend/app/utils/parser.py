"""
Resume parsing utilities.
Handles PDF, DOCX extraction and text normalization.
"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text from PDF
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text from DOCX
    """
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        raise


def normalize_text(text: str) -> str:
    """
    Normalize resume text: remove extra whitespace, standardize formatting.
    
    Args:
        text: Raw text
        
    Returns:
        Normalized text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep important ones
    text = re.sub(r'[^\w\s\-.,@#]', '', text)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    # Simple pattern for common US/international formats
    pattern = r'(\+?1?\s?)(\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}'
    matches = re.findall(pattern, text)
    return ''.join(matches[0]) if matches else None


def extract_skills(text: str) -> List[str]:
    """
    Extract technical skills from resume text.
    Looks for common skill keywords.
    """
    # Common technical skills to look for
    COMMON_SKILLS = {
        # Languages
        'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'go', 'rust',
        'typescript', 'kotlin', 'swift', 'objective-c', 'perl', 'scala', 'groovy',
        
        # Web frameworks
        'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'express', 'rails',
        'spring', 'asp.net', '.net', 'laravel', 'nodejs', 'node.js',
        
        # Databases
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra', 'dynamodb',
        'elasticsearch', 'firestore', 'oracle', 'sqlite',
        
        # Cloud/DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
        'gitlab', 'github', 'terraform', 'ansible', 'circleci', 'travis ci',
        
        # Data/ML
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
        'spark', 'hadoop', 'scala', 'sql', 'tableau', 'power bi',
        
        # Other
        'git', 'rest', 'graphql', 'microservices', 'agile', 'scrum', 'linux',
        'windows', 'macos', 'html', 'css', 'xml', 'json', 'soap', 'jira',
        'confluence', 'slack', 'asana', 'monday.com'
    }
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in COMMON_SKILLS:
        if skill in text_lower:
            # Avoid partial matches (e.g., "c" in "docker")
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
    
    return sorted(list(found_skills))


def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Parse resume and extract structured data.
    
    Args:
        file_path: Path to resume file (PDF or DOCX)
        
    Returns:
        Dictionary with extracted resume data
    """
    file_ext = Path(file_path).suffix.lower()
    
    try:
        # Extract raw text based on file type
        if file_ext == '.pdf':
            raw_text = extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            raw_text = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        if not raw_text.strip():
            logger.warning(f"No text extracted from {file_path}")
            raw_text = "No text extracted"
        
        # Normalize text
        normalized_text = normalize_text(raw_text)
        
        # Extract key information
        email = extract_email(raw_text)
        phone = extract_phone(raw_text)
        skills = extract_skills(raw_text)
        
        # Try to extract name from beginning (heuristic)
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        name = lines[0] if lines else "Unknown"
        
        # Try to extract location (very basic - look for common city/state patterns)
        location_pattern = r'\b(?:New York|Los Angeles|San Francisco|Chicago|Austin|Seattle|Boston|Denver|Atlanta|Miami|Portland|Seattle|Austin|Denver)\b'
        location_matches = re.findall(location_pattern, raw_text, re.IGNORECASE)
        location = location_matches[0] if location_matches else None
        
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "skills": skills,
            "raw_text": raw_text[:5000],  # First 5000 chars for storage
            "normalized_text": normalized_text[:5000],
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error parsing resume {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "skills": [],
            "raw_text": ""
        }
