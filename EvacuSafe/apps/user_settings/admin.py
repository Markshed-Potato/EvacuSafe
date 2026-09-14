from django.contrib import admin
from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_alerts', 'dark_mode', 'language', 'updated_at')
    list_filter = ('dark_mode', 'language')
