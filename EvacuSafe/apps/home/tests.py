from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
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


class HomeDashboardMapTests(TestCase):
    def test_dashboard_renders_coordinates_and_unmapped_center_count(self):
        user = User.objects.create_user(username='responder', password='test-password')
        EvacuationCenter.objects.create(
            name='Mapped Center',
            location='Cebu City',
            latitude=Decimal('10.315700'),
            longitude=Decimal('123.885400'),
            status='active',
            occupants=12,
            capacity=30,
        )
        EvacuationCenter.objects.create(name='Center Awaiting Coordinates')
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        map_centers = response.context['map_centers']
        mapped = next(center for center in map_centers if center['name'] == 'Mapped Center')
        self.assertEqual(mapped['latitude'], 10.3157)
        self.assertEqual(mapped['longitude'], 123.8854)
        self.assertEqual(mapped['status'], 'Active')
        self.assertEqual(mapped['occupants'], 12)
        self.assertEqual(mapped['capacity'], 30)
        self.assertGreater(response.context['unmapped_center_count'], 0)
        self.assertContains(response, 'evacuation-map')
        self.assertContains(
            response,
            'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        )
        self.assertContains(response, 'OpenStreetMap contributors')
        self.assertContains(response, 'CARTO')
        self.assertContains(response, 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js')
