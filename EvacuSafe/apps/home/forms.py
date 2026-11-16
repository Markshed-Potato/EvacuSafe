from django import forms

from .models import EvacuationCenter


class EvacuationCenterCreateForm(forms.ModelForm):
    class Meta:
        model = EvacuationCenter
        fields = [
            'name',
            'location',
            'status',
            'capacity',
            'occupants',
            'latitude',
            'longitude',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'off', 'maxlength': 150}),
            'location': forms.TextInput(attrs={'autocomplete': 'off', 'maxlength': 200}),
            'capacity': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'occupants': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'latitude': forms.NumberInput(attrs={'min': -90, 'max': 90, 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'min': -180, 'max': 180, 'step': 'any'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if (latitude is None) != (longitude is None):
            message = 'Enter both latitude and longitude, or leave both blank.'
            if latitude is None:
                self.add_error('latitude', message)
            if longitude is None:
                self.add_error('longitude', message)
        return cleaned_data


class EvacuationCenterUpdateForm(forms.ModelForm):
    class Meta:
        model = EvacuationCenter
        fields = ['status', 'occupants']
        widgets = {
            'occupants': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }
