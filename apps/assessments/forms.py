from django import forms
from django.core.exceptions import ValidationError
from .models import SkillAssessmentAttempt, SkillTest, QuestionPool, GroupChallenge, QuestionDiscussion


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
            ('oldest', 'Oldest First'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )


class QuestionGenerationForm(forms.Form):
    skill_name = forms.CharField(
        label='Skill / Topic',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
            'placeholder': 'e.g. Rust, Leadership, UI/UX'
        })
    )
    difficulty = forms.ChoiceField(
        choices=SkillTest.DIFFICULTY_LEVELS,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )
    question_type = forms.ChoiceField(
        choices=QuestionPool.QUESTION_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )
    question_count = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
        })
    )



class GroupChallengeForm(forms.ModelForm):
    class Meta:
        model = GroupChallenge
        fields = ['test', 'title', 'description', 'prize_description', 'start_date', 'end_date']
        widgets = {
            'test': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
                'placeholder': 'Challenge title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
                'rows': 3,
                'placeholder': 'Describe what this challenge is about'
            }),
            'prize_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
                'rows': 2,
                'placeholder': 'What will the winner earn?'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary'
            })
        }


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = QuestionDiscussion
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary',
                'placeholder': 'Leave a thoughtful observation or question about this item...'
            })
        }
