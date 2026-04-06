"""
Utility functions for accounts app.
"""

from typing import Dict, List, Any
from django.utils import timezone


def map_resume_to_profile_data(parsed_result: Dict[str, Any], import_options: List[str] = None) -> Dict[str, Any]:
    """
    Map parsed resume data to profile fields.

    Args:
        parsed_result: Parsed resume data from ResumeParser
        import_options: List of fields to import (optional)

    Returns:
        Dict with profile field mappings
    """
    profile_data = {}
    
    # Only process requested fields if import_options is specified
    if import_options and 'personal_info' not in import_options:
        import_options = []
    
    # Basic contact info
    contact_info = parsed_result.get('contact_info', {})
    if contact_info.get('name') and (not import_options or 'personal_info' in import_options):
        profile_data['full_name'] = contact_info['name']
    
    if contact_info.get('phone') and (not import_options or 'personal_info' in import_options):
        profile_data['phone'] = contact_info['phone']
    
    if contact_info.get('location') and (not import_options or 'personal_info' in import_options):
        profile_data['location'] = contact_info['location']
    
    if contact_info.get('email') and (not import_options or 'personal_info' in import_options):
        profile_data['email'] = contact_info['email']
    
    # Skills
    if not import_options or 'skills' in import_options:
        skills_list = parsed_result.get('skills', [])
        if skills_list:
            profile_data['skills'] = [
                {'skill': skill, 'proficiency': 'intermediate'}
                for skill in skills_list[:20]  # Limit to 20 skills
            ]
    
    # Education
    if not import_options or 'education' in import_options:
        education_list = parsed_result.get('education', [])
        if education_list:
            profile_data['education'] = education_list[:5]  # Limit to 5 education entries
    
    # Certifications
    if not import_options or 'certifications' in import_options:
        certifications = parsed_result.get('certifications', [])
        if certifications:
            profile_data['certifications'] = [
                {
                    'name': cert.get('text', ''),
                    'issuer': _extract_certification_issuer(cert.get('text', '')),
                    'date': cert.get('date', ''),
                    'url': cert.get('url', '')
                }
                for cert in certifications[:10]  # Limit to 10 certs
            ]
    
    # Experience
    if not import_options or 'experience' in import_options:
        experience_list = parsed_result.get('experience', [])
        if experience_list:
            profile_data['experience'] = experience_list[:10]  # Limit to 10 experience entries
    
    return profile_data


def _extract_certification_issuer(cert_text: str) -> str:
    """
    Extract issuer from certification text.

    Examples:
    - "AWS Certified Solutions Architect" -> "AWS"
    - "Google Cloud Professional Cloud Architect" -> "Google Cloud"
    - "PMI-PMP Certification" -> "PMI"
    """
    # Common issuers and their patterns
    issuers = {
        'AWS': ['aws'],
        'Google Cloud': ['google cloud', 'gcp'],
        'Microsoft': ['microsoft', 'azure'],
        'Cisco': ['cisco'],
        'CompTIA': ['comp tia', 'comptia'],
        'PMI': ['pmi', 'project management institute'],
        'Oracle': ['oracle'],
        'Salesforce': ['salesforce'],
        'VMware': ['vmware'],
        'Linux': ['linux'],
        'ITIL': ['itil'],
        'GIAC': ['giac'],
        'ISC': ['isc'],
        'Atlassian': ['atlassian'],
        'HubSpot': ['hubspot'],
        'Tableau': ['tableau'],
        'ServiceNow': ['servicenow']
    }

    cert_lower = cert_text.lower()

    for issuer, patterns in issuers.items():
        for pattern in patterns:
            if pattern in cert_lower:
                return issuer

    # If no known issuer found, try to extract from common patterns
    # e.g., "Certified in X by Y" -> Y
    import re
    by_pattern = re.search(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', cert_text, re.IGNORECASE)
    if by_pattern:
        return by_pattern.group(1)

    # Default fallback
    return "Unknown Issuer"


def merge_profile_data(existing_profile, new_data: Dict[str, Any], merge_strategy: str = 'smart') -> Dict[str, Any]:
    """
    Merge new profile data with existing data.

    Args:
        existing_profile: PersonalProfile instance
        new_data: New data from resume
        merge_strategy: 'smart' (don't overwrite), 'replace' (overwrite), 'append' (add to existing)

    Returns:
        Merged profile data dict
    """
    merged = {}

    for field, new_value in new_data.items():
        existing_value = getattr(existing_profile, field, None)

        if merge_strategy == 'replace':
            # Always use new value
            merged[field] = new_value

        elif merge_strategy == 'append':
            # Append to existing (for lists)
            if isinstance(existing_value, list) and isinstance(new_value, list):
                merged[field] = existing_value + new_value
            else:
                merged[field] = new_value if new_value else existing_value

        else:  # smart merge
            # Don't overwrite existing data
            if not existing_value or existing_value == [] or existing_value == {}:
                merged[field] = new_value
            else:
                # Keep existing, but could add new items to lists
                if field in ['skills', 'education', 'certifications', 'experience']:
                    if isinstance(existing_value, list) and isinstance(new_value, list):
                        # Smart merge: add new items that don't conflict
                        merged[field] = _smart_merge_lists(existing_value, new_value, field)
                    else:
                        merged[field] = existing_value
                else:
                    # For non-list fields, keep existing
                    merged[field] = existing_value

    return merged


def _smart_merge_lists(existing: List, new: List, field_type: str) -> List:
    """
    Smart merge for list fields.

    For skills: Add new skills not already present
    For education/certifications: Add new entries (assume different)
    For experience: Add new entries (assume different roles)
    """
    if field_type == 'skills':
        # Extract skill names from existing
        existing_skills = {skill.get('skill', '').lower() for skill in existing if isinstance(skill, dict)}
        # Add new skills not already present
        merged = existing.copy()
        for new_skill in new:
            if isinstance(new_skill, dict):
                skill_name = new_skill.get('skill', '').lower()
                if skill_name not in existing_skills:
                    merged.append(new_skill)
            elif isinstance(new_skill, str):
                if new_skill.lower() not in existing_skills:
                    merged.append({'skill': new_skill, 'proficiency': 'intermediate'})
        return merged

    elif field_type in ['education', 'certifications', 'experience']:
        # For these, just append new entries (assume they're different)
        return existing + new

    else:
        return existing


def preview_import_changes(existing_profile, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a preview of what will change during import.

    Args:
        existing_profile: PersonalProfile instance
        profile_data: New profile data from resume

    Returns:
        Dict with changes preview
    """
    merged_data = merge_profile_data(existing_profile, profile_data, 'smart')

    preview = {}

    for field, new_value in profile_data.items():
        existing_value = getattr(existing_profile, field, None)
        
        changes = {'added': [], 'modified': [], 'removed': []}
        
        if field in ['skills', 'education', 'certifications', 'experience']:
            # Handle list fields
            if isinstance(existing_value, list) and isinstance(new_value, list):
                existing_items = existing_value or []
                new_items = new_value or []
                
                # Simple diff: items in new but not in existing are added
                # For now, we'll consider all new items as "added" since we can't easily match them
                changes['added'] = new_items
                
                if existing_items:
                    changes['modified'] = []  # Would need more complex matching logic
            else:
                if new_value and not existing_value:
                    changes['added'] = [str(new_value)]
        else:
            # Handle simple fields
            if existing_value != new_value:
                if existing_value:
                    changes['modified'] = [f'{existing_value} → {new_value}']
                else:
                    changes['added'] = [str(new_value)]
        
        if changes['added'] or changes['modified'] or changes['removed']:
            preview[field] = changes

    return preview