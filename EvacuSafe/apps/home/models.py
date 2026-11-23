from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class EvacuationCenter(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('standby', 'Standby'),
        ('closed', 'Closed'),
        ('full', 'Full'),
    ]

    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    coordinates_are_approximate = models.BooleanField(default=False)
    capacity = models.PositiveIntegerField(default=0)
    occupants = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Lifecycle & Soft Delete / Archiving
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='archived_centers'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def occupancy_rate(self):
        if not self.capacity or self.capacity == 0:
            return 0
        return round((self.occupants / self.capacity) * 100, 1)

    @property
    def is_full(self):
        return self.capacity > 0 and self.occupants >= self.capacity

    @property
    def is_near_capacity(self):
        return self.capacity > 0 and self.occupancy_rate >= 85 and not self.is_full

    def clean(self):
        super().clean()
        if self.occupants is not None and self.occupants < 0:
            raise ValidationError({'occupants': 'Occupants count cannot be negative.'})
        if self.capacity is not None and self.capacity < 0:
            raise ValidationError({'capacity': 'Capacity cannot be negative.'})
        if self.capacity is not None and self.occupants is not None:
            if self.capacity > 0 and self.occupants > self.capacity:
                raise ValidationError({
                    'occupants': f'Current occupants ({self.occupants}) cannot exceed total capacity ({self.capacity}).'
                })
            # Automatically flag centers at 100% capacity as 'full'
            if self.capacity > 0 and self.occupants >= self.capacity and self.status == 'active':
                self.status = 'full'


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('archive', 'Archived'),
        ('restore', 'Restored'),
        ('delete', 'Deleted'),
    ]

    center = models.ForeignKey(
        EvacuationCenter,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs'
    )
    center_name = models.CharField(max_length=150)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='center_audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    old_occupants = models.IntegerField(null=True, blank=True)
    new_occupants = models.IntegerField(null=True, blank=True)
    old_capacity = models.IntegerField(null=True, blank=True)
    new_capacity = models.IntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor = self.user.username if self.user else 'System'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} {self.action} {self.center_name}"


class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    DISASTER_TYPES = [
        ('Typhoon', 'Typhoon / Tropical Cyclone'),
        ('Flood', 'Flash Flood / Inundation'),
        ('Earthquake', 'Earthquake'),
        ('Fire', 'Urban / Structural Fire'),
        ('Landslide', 'Landslide / Soil Collapse'),
        ('Volcanic', 'Volcanic Activity / Ashfall'),
        ('Other', 'Other Emergency Event'),
    ]

    title = models.CharField(max_length=150)
    disaster_type = models.CharField(max_length=50, choices=DISASTER_TYPES, default='Typhoon')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    declared_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    declared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='declared_incidents'
    )

    class Meta:
        ordering = ['-declared_at']

    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"


class ResourceInventory(models.Model):
    center = models.OneToOneField(
        EvacuationCenter,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    food_packs = models.PositiveIntegerField(default=0)
    water_liters = models.PositiveIntegerField(default=0)
    medical_kits = models.PositiveIntegerField(default=0)
    blankets = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resource_updates'
    )

    class Meta:
        verbose_name_plural = 'Resource Inventories'

    def __str__(self):
        return f"Resources for {self.center.name}"
