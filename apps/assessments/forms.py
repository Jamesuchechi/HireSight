from django import forms
from django.core.exceptions import ValidationError
from .models import SkillAssessmentAttempt, SkillTest


class TestFilterForm(forms.Form):
    """Filter form for browsing tests"""
    
    skill = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
            'placeholder': 'Search by skill name...'
        })
    )
    
    difficulty = forms.ChoiceField(
        required=False,
        choices=[('', 'All Difficulties')] + list(SkillTest.DIFFICULTY_LEVELS),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )
    
    test_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(SkillTest.TEST_TYPES),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Default'),
            ('recommended', 'Recommended for You'),
            ('popular', 'Most Popular'),
            ('difficulty', 'By Difficulty'),
            ('newest', 'Newest First'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )