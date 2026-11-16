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
        EvacuationCenter.objects.create(
            name='Approximate Center',
            location='Approximate area only',
            latitude=Decimal('10.300000'),
            longitude=Decimal('123.900000'),
            coordinates_are_approximate=True,
        )
        EvacuationCenter.objects.create(name='Center Awaiting Coordinates')
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        map_centers = response.context['map_centers']
        mapped = next(center for center in map_centers if center['name'] == 'Mapped Center')
        self.assertIn('id', mapped)
        self.assertEqual(mapped['latitude'], 10.3157)
        self.assertEqual(mapped['longitude'], 123.8854)
        self.assertEqual(mapped['status'], 'Active')
        self.assertEqual(mapped['occupants'], 12)
        self.assertEqual(mapped['capacity'], 30)
        approximate = next(
            center for center in map_centers if center['name'] == 'Approximate Center'
        )
        self.assertTrue(approximate['coordinates_are_approximate'])
        self.assertEqual(response.context['approximate_center_count'], 4)
        self.assertGreater(response.context['unmapped_center_count'], 0)
        self.assertContains(response, 'evacuation-map')
        self.assertContains(response, 'id="center-search"')
        self.assertContains(response, 'id="open-create-center"')
        self.assertContains(response, 'id="center-dialog"')
        self.assertContains(response, 'name="latitude"')
        self.assertContains(response, 'name="longitude"')
        self.assertContains(response, 'class="inline-update-form"')
        self.assertContains(response, 'name="occupants"')
        self.assertContains(response, 'data-status-filter="all"')
        self.assertContains(response, 'data-status-filter="active"')
        self.assertContains(response, 'data-status-filter="standby"')
        self.assertContains(response, 'data-status-filter="closed"')
        self.assertContains(response, 'data-center-id="')
        self.assertContains(response, 'Approximate map location')
        self.assertContains(response, 'data-approximate-count="4"')
        self.assertContains(
            response,
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        )
        self.assertContains(response, 'OpenStreetMap contributors')
        self.assertContains(response, 'Sources: Esri')
        self.assertContains(response, 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js')


class EvacuationCenterCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='coordinator', password='test-password')
        self.url = reverse('manage_center')
        self.initial_center_count = EvacuationCenter.objects.count()

    def test_anonymous_user_cannot_create_center(self):
        response = self.client.post(self.url, {'name': 'New Center'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(EvacuationCenter.objects.count(), self.initial_center_count)

    def test_authenticated_user_creates_center_and_receives_updated_summary(self):
        self.client.force_login(self.user)
        initial_active_count = EvacuationCenter.objects.filter(status='active').count()
        initial_standby_count = EvacuationCenter.objects.filter(status='standby').count()
        initial_closed_count = EvacuationCenter.objects.filter(status='closed').count()
        initial_occupants = sum(EvacuationCenter.objects.values_list('occupants', flat=True))
        initial_capacity = sum(EvacuationCenter.objects.values_list('capacity', flat=True))
        EvacuationCenter.objects.create(
            name='Existing Center',
            status='active',
            capacity=100,
            occupants=40,
        )

        response = self.client.post(self.url, {
            'name': 'New Center',
            'location': 'Lahug',
            'status': 'standby',
            'capacity': 60,
            'occupants': 12,
            'latitude': '10.330000',
            'longitude': '123.900000',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['center']['name'], 'New Center')
        self.assertEqual(response.json()['center']['latitude'], 10.33)
        self.assertEqual(response.json()['center']['status_key'], 'standby')
        self.assertEqual(response.json()['summary'], {
            'active_count': initial_active_count + 1,
            'standby_count': initial_standby_count + 1,
            'closed_count': initial_closed_count,
            'total_count': self.initial_center_count + 2,
            'total_occupants': initial_occupants + 52,
            'total_capacity': initial_capacity + 160,
        })
        self.assertTrue(EvacuationCenter.objects.filter(name='New Center').exists())

    def test_partial_coordinates_are_rejected_without_creating_center(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            'name': 'Unmapped Center',
            'capacity': 10,
            'occupants': 0,
            'latitude': '10.330000',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('longitude', response.json()['errors'])
        self.assertEqual(EvacuationCenter.objects.count(), self.initial_center_count)

    def test_coordinates_outside_geographic_range_are_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            'name': 'Invalid Center',
            'capacity': 10,
            'occupants': 0,
            'latitude': '91',
            'longitude': '123.9',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('latitude', response.json()['errors'])
        self.assertEqual(EvacuationCenter.objects.count(), self.initial_center_count)


class EvacuationCenterUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='coordinator', password='test-password')
        self.center = EvacuationCenter.objects.create(
            name='Update Center',
            location='Cebu City',
            status='standby',
            capacity=80,
            occupants=20,
            latitude=Decimal('10.315700'),
            longitude=Decimal('123.885400'),
        )
        self.url = reverse('update_center', args=[self.center.pk])

    def test_anonymous_user_cannot_update_center(self):
        response = self.client.post(self.url, {'status': 'active', 'occupants': 30})

        self.assertEqual(response.status_code, 302)
        self.center.refresh_from_db()
        self.assertEqual(self.center.status, 'standby')
        self.assertEqual(self.center.occupants, 20)

    def test_authenticated_user_updates_center_and_receives_new_summary(self):
        self.client.force_login(self.user)
        old_active_count = EvacuationCenter.objects.filter(status='active').count()
        old_standby_count = EvacuationCenter.objects.filter(status='standby').count()
        old_closed_count = EvacuationCenter.objects.filter(status='closed').count()
        old_occupants = sum(EvacuationCenter.objects.values_list('occupants', flat=True))
        old_capacity = sum(EvacuationCenter.objects.values_list('capacity', flat=True))

        response = self.client.post(self.url, {'status': 'active', 'occupants': 35})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['center']['status_key'], 'active')
        self.assertEqual(response.json()['center']['occupants'], 35)
        self.assertEqual(response.json()['summary'], {
            'active_count': old_active_count + 1,
            'standby_count': old_standby_count - 1,
            'closed_count': old_closed_count,
            'total_count': EvacuationCenter.objects.count(),
            'total_occupants': old_occupants + 15,
            'total_capacity': old_capacity,
        })
        self.center.refresh_from_db()
        self.assertEqual(self.center.status, 'active')
        self.assertEqual(self.center.occupants, 35)

    def test_invalid_status_and_occupant_count_are_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {'status': 'unknown', 'occupants': -1})

        self.assertEqual(response.status_code, 400)
        self.assertIn('status', response.json()['errors'])
        self.assertIn('occupants', response.json()['errors'])
        self.center.refresh_from_db()
        self.assertEqual(self.center.status, 'standby')
        self.assertEqual(self.center.occupants, 20)

    def test_missing_center_returns_not_found(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('update_center', args=[999999]), {
            'status': 'active',
            'occupants': 0,
        })

        self.assertEqual(response.status_code, 404)
