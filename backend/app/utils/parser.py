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
    # Multiple patterns for common US/international formats
    patterns = [
        r'\((\d{3})\)\s*(\d{3})[-.\s]?(\d{4})',  # (415) 555-1234 or (415)555-1234
        r'(?:\+1\s?)?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})',  # 415-555-1234, +1 415 555 1234
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Reconstruct the phone number from groups
            match = matches[0]
            return f"{match[0]}-{match[1]}-{match[2]}"
    
    return None


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


def extract_experience(text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience from resume text.
    Looks for patterns like "Company Name", "Role Title", "2020-2023", etc.
    """
    experience = []
    
    # Look for common experience section headers
    experience_section = ""
    patterns = [
        r'(?:experience|work experience|professional experience)(.*?)(?:education|skills|projects|certifications|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            experience_section = match.group(1)
            break
    
    if not experience_section:
        experience_section = text  # Fallback to whole text
    
    # Extract individual entries (heuristic based on date patterns)
    date_pattern = r'(\d{4}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[.,\s\-]*(\d{4}|present|current|ongoing)?'
    
    # Split by potential entry boundaries
    entries = re.split(r'\n\n+', experience_section)
    
    for entry in entries:
        if len(entry.strip()) < 20:
            continue
        
        # Try to find company and role
        lines = [l.strip() for l in entry.split('\n') if l.strip()]
        if len(lines) >= 2:
            # Assume first line is company or role, second is the other
            company = lines[0][:80]
            role = lines[1][:80] if len(lines) > 1 else ""
            
            # Extract dates
            dates = re.findall(date_pattern, entry, re.IGNORECASE)
            start_date = None
            end_date = None
            
            if dates:
                start_date = f"{dates[0][0]}"
                if len(dates[0]) > 1 and dates[0][1]:
                    end_date = f"{dates[0][1]}"
            
            # Extract description (up to 200 chars)
            description = ' '.join(lines[2:])[:200] if len(lines) > 2 else ""
            
            experience.append({
                "company": company,
                "role": role,
                "start_date": start_date,
                "end_date": end_date,
                "description": description
            })
    
    return experience[:5]  # Limit to 5 most recent


def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extract education information from resume text.
    Looks for patterns like "University Name", "Degree", "GPA", graduation date, etc.
    """
    education = []
    
    # Look for education section
    education_section = ""
    patterns = [
        r'(?:education|academic|university|college|degree)(.*?)(?:experience|skills|projects|certifications|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            education_section = match.group(1)
            break
    
    if not education_section:
        education_section = text  # Fallback
    
    # Common degree types
    degree_pattern = r'\b(bachelor|master|phd|associate|diploma|graduate|bs|ba|ms|ma|mba|md|jd|btec|hnd)\b'
    
    # Extract entries
    entries = re.split(r'\n\n+', education_section)
    
    for entry in entries:
        if len(entry.strip()) < 15:
            continue
        
        lines = [l.strip() for l in entry.split('\n') if l.strip()]
        
        # Find degree type
        degree = ""
        for line in lines:
            degree_match = re.search(degree_pattern, line, re.IGNORECASE)
            if degree_match:
                degree = degree_match.group(1)
                break
        
        # Institution is usually first line or line before degree
        institution = lines[0][:100] if lines else ""
        
        # Try to extract graduation year
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        years = re.findall(year_pattern, entry)
        graduation_date = years[-1] if years else None
        
        # GPA extraction
        gpa_pattern = r'(?:gpa|cumulative|overall)[:\s]*([\d.]+)'
        gpa_match = re.search(gpa_pattern, entry, re.IGNORECASE)
        gpa = gpa_match.group(1) if gpa_match else None
        
        education.append({
            "institution": institution,
            "degree": degree,
            "graduation_date": graduation_date,
            "gpa": gpa,
            "description": ' '.join(lines[1:])[:150] if len(lines) > 1 else ""
        })
    
    return education[:3]  # Limit to 3 most recent


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
        experience = extract_experience(raw_text)
        education = extract_education(raw_text)
        
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
            "experience": experience,
            "education": education,
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
            "experience": [],
            "education": [],
            "raw_text": ""
        }
