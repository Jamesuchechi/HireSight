from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PersonalProfile, CompanyProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when a new user is created.
    - Personal account → PersonalProfile
    - Company account → CompanyProfile
    """
    if created:
        if instance.account_type == 'personal':
            PersonalProfile.objects.create(
                user=instance,
                full_name=instance.email.split('@')[0].title()  # Default name from email
            )
        elif instance.account_type == 'company':
            CompanyProfile.objects.create(
                user=instance,
                company_name=f"{instance.email.split('@')[0].title()} Inc."  # Default company name
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the profile when user is saved.
    """
    if instance.account_type == 'personal' and hasattr(instance, 'personal_profile'):
        instance.personal_profile.save()
    elif instance.account_type == 'company' and hasattr(instance, 'company_profile'):
        instance.company_profile.save()