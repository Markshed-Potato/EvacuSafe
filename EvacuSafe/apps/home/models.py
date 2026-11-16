from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class EvacuationCenter(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('standby', 'Standby'),
        ('closed', 'Closed'),
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
    capacity = models.PositiveIntegerField(default=0)
    occupants = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
