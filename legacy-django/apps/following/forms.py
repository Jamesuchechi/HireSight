from django import forms
from django.core.exceptions import ValidationError


class BulkFollowSelectionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ('follow', 'Follow selected users'),
            ('unfollow', 'Unfollow selected users')
        ],
        widget=forms.HiddenInput()
    )
    user_ids = forms.CharField(widget=forms.HiddenInput())

    def clean_user_ids(self):
        raw = self.cleaned_data['user_ids']
        if not raw:
            raise ValidationError("Select at least one user.")
        user_ids = []
        for chunk in raw.split(','):
            if not chunk.strip():
                continue
            try:
                user_ids.append(int(chunk))
            except ValueError:
                raise ValidationError("Invalid user selection.")
        if len(user_ids) > 50:
            raise ValidationError("You can only act on up to 50 users at once.")
        return user_ids


class BulkFollowCSVForm(forms.Form):
    csv_file = forms.FileField()
    action = forms.ChoiceField(
        choices=[('follow', 'Follow users from CSV')],
        widget=forms.HiddenInput(),
        initial='follow'
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.lower().endswith('.csv'):
            raise ValidationError("Upload a CSV file.")
        return csv_file
