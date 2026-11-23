from django import forms
from .models import EvacuationCenter, Incident, ResourceInventory


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

        capacity = cleaned_data.get('capacity')
        occupants = cleaned_data.get('occupants')
        if capacity is not None and capacity < 0:
            self.add_error('capacity', 'Capacity cannot be negative.')
        if occupants is not None and occupants < 0:
            self.add_error('occupants', 'Occupants count cannot be negative.')
        if capacity is not None and occupants is not None:
            if capacity > 0 and occupants > capacity:
                self.add_error('occupants', f'Occupants ({occupants}) cannot exceed total capacity ({capacity}).')
            if capacity > 0 and occupants >= capacity and cleaned_data.get('status') == 'active':
                cleaned_data['status'] = 'full'
        return cleaned_data


class EvacuationCenterUpdateForm(forms.ModelForm):
    class Meta:
        model = EvacuationCenter
        fields = ['status', 'occupants']
        widgets = {
            'occupants': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        occupants = cleaned_data.get('occupants')
        status = cleaned_data.get('status')
        if occupants is not None:
            if occupants < 0:
                self.add_error('occupants', 'Occupants count cannot be negative.')
            elif self.instance and self.instance.capacity > 0 and occupants > self.instance.capacity:
                self.add_error('occupants', f'Occupants ({occupants}) cannot exceed total capacity ({self.instance.capacity}).')
            elif self.instance and self.instance.capacity > 0 and occupants >= self.instance.capacity and status == 'active':
                cleaned_data['status'] = 'full'
        return cleaned_data


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ['title', 'disaster_type', 'severity', 'location', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Typhoon Betty Flash Flood'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Affected barangay or area'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Operational situation and relief requirements'}),
        }


class ResourceInventoryForm(forms.ModelForm):
    class Meta:
        model = ResourceInventory
        fields = ['food_packs', 'water_liters', 'medical_kits', 'blankets']
        widgets = {
            'food_packs': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-input'}),
            'water_liters': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-input'}),
            'medical_kits': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-input'}),
            'blankets': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-input'}),
        }
