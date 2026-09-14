from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserSettings(models.Model):
    LANGUAGE_CHOICES = [('en', 'English'), ('fil', 'Filipino')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings')
    email_notifications = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings<{self.user.username}>"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.get_or_create(user=instance)
