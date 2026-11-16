from django.contrib import admin
from .models import EvacuationCenter


@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'latitude', 'longitude', 'status', 'occupants', 'capacity', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name', 'location')
