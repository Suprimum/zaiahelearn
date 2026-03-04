# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Teacher


@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            return  # Skip creating Teacher profile for superusers
        elif hasattr(instance, 'userprofile') and instance.userprofile.role == 'teacher':
            Teacher.objects.create(user=instance)
            print(f"SIGNAL: Created Teacher profile for user: {instance.username}")

'''
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

'''