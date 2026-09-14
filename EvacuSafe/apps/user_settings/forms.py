from django import forms
from .models import UserSettings


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['email_notifications', 'sms_alerts', 'dark_mode', 'language']
