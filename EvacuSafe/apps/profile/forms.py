from django import forms
from django.contrib.auth.models import User
from .models import Profile


class UserBasicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
        }


class ProfileForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
        required=False,
    )

    class Meta:
        model = Profile
        fields = ['avatar', 'role', 'phone', 'bio']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+63 912 345 6789'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Disaster response qualifications or operational zone'}),
        }
