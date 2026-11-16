from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import EvacuationCenter


class EvacuationCenterCoordinateTests(TestCase):
    def test_coordinates_are_optional(self):
        center = EvacuationCenter(name='Unmapped Center')
        center.full_clean()

    def test_coordinates_accept_valid_geographic_ranges(self):
        center = EvacuationCenter(
            name='Mapped Center',
            latitude=Decimal('14.599500'),
            longitude=Decimal('120.984200'),
        )
        center.full_clean()

    def test_latitude_outside_geographic_range_is_rejected(self):
        center = EvacuationCenter(name='Invalid Center', latitude=91)
        with self.assertRaises(ValidationError):
            center.full_clean()

    def test_longitude_outside_geographic_range_is_rejected(self):
        center = EvacuationCenter(name='Invalid Center', longitude=-181)
        with self.assertRaises(ValidationError):
            center.full_clean()
