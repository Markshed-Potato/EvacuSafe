from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_RESPONDER = 'Responder'
    ROLE_COORDINATOR = 'Coordinator'
    ROLE_ADMIN = 'Admin'

    ROLE_CHOICES = [
        (ROLE_RESPONDER, 'Viewer / Responder'),
        (ROLE_COORDINATOR, 'Coordinator'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, blank=True, default=ROLE_RESPONDER)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    @property
    def is_coordinator(self):
        return self.role in (self.ROLE_COORDINATOR, self.ROLE_ADMIN) or self.user.is_staff or self.user.is_superuser

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.user.is_staff or self.user.is_superuser


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
