from django.db import migrations
import json

def convert_benefits_to_json(apps, schema_editor):
    """Convert existing benefits data from text to JSON array format."""
    CompanyProfile = apps.get_model('accounts', 'CompanyProfile')
    
    for profile in CompanyProfile.objects.all():
        # Check if benefits is already in JSON format
        if isinstance(profile.benefits, list):
            # Already in correct format, skip
            continue
            
        # Convert from old text format to JSON array
        if profile.benefits and isinstance(profile.benefits, str):
            # Split by newlines and filter empty lines
            benefit_lines = [line.strip() for line in profile.benefits.split('\n') if line.strip()]
            profile.benefits = benefit_lines
            profile.save()

def reverse_convert_benefits(apps, schema_editor):
    """Reverse conversion for migration rollback."""
    CompanyProfile = apps.get_model('accounts', 'CompanyProfile')
    
    for profile in CompanyProfile.objects.all():
        if isinstance(profile.benefits, list):
            # Convert back to newline-separated text
            profile.benefits = '\n'.join(profile.benefits)
            profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_alter_companyprofile_locations'),
    ]
    
    operations = [
        migrations.RunPython(
            convert_benefits_to_json,
            reverse_convert_benefits,
            elidable=True  # Allow Django to skip this migration if no data exists
        ),
    ]