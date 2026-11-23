from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from apps.profile.models import Profile
from apps.user_settings.models import UserSettings
from .models import AuditLog, EvacuationCenter, Incident, ResourceInventory


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
        self.assertContains(response, 'Filter map and center list')
        self.assertEqual(response.content.count(b'data-status-filter='), 8)
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



class EvacuationCenterCapacitySafeguardTests(TestCase):
    def test_model_clean_rejects_occupants_exceeding_capacity(self):
        center = EvacuationCenter(name='Overcrowded Center', capacity=50, occupants=51)
        with self.assertRaises(ValidationError) as ctx:
            center.clean()
        self.assertIn('occupants', ctx.exception.message_dict)

    def test_model_clean_rejects_negative_occupants(self):
        center = EvacuationCenter(name='Negative Occupants', capacity=50, occupants=-5)
        with self.assertRaises(ValidationError) as ctx:
            center.clean()
        self.assertIn('occupants', ctx.exception.message_dict)

    def test_model_clean_flags_center_at_maximum_capacity_as_full(self):
        center = EvacuationCenter(name='Max Capacity Center', capacity=100, occupants=100, status='active')
        center.clean()
        self.assertEqual(center.status, 'full')
        self.assertTrue(center.is_full)

    def test_create_form_rejects_occupants_exceeding_capacity(self):
        user = User.objects.create_user(username='coordinator_safe', password='password')
        Profile.objects.filter(user=user).update(role='Coordinator')
        self.client.force_login(user)

        response = self.client.post(reverse('manage_center'), {
            'name': 'Invalid Capacity Center',
            'capacity': 100,
            'occupants': 105,
            'status': 'active',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('occupants', response.json()['errors'])

    def test_update_form_rejects_occupants_exceeding_capacity(self):
        user = User.objects.create_user(username='coordinator_up', password='password')
        Profile.objects.filter(user=user).update(role='Coordinator')
        center = EvacuationCenter.objects.create(name='Update Cap Center', capacity=50, occupants=20)
        self.client.force_login(user)

        response = self.client.post(reverse('update_center', args=[center.pk]), {
            'status': 'active',
            'occupants': 55,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('occupants', response.json()['errors'])


class EvacuationCenterRBACTests(TestCase):
    def setUp(self):
        # Viewer / Responder (read-only)
        self.responder = User.objects.create_user(username='john_volunteer', password='password')
        Profile.objects.filter(user=self.responder).update(role='Responder')

        # Coordinator
        self.coordinator = User.objects.create_user(username='sarah_coord', password='password')
        Profile.objects.filter(user=self.coordinator).update(role='Coordinator')

        # Administrator
        self.admin = User.objects.create_user(username='mike_admin', password='password')
        Profile.objects.filter(user=self.admin).update(role='Admin')

        self.center = EvacuationCenter.objects.create(name='RBAC Test Center', capacity=100, occupants=10)

    def test_responder_blocked_from_creating_center(self):
        self.client.force_login(self.responder)
        response = self.client.post(reverse('manage_center'), {'name': 'Unauthorized Center', 'capacity': 50, 'occupants': 0})
        self.assertEqual(response.status_code, 403)
        self.assertIn('Permission denied', response.json()['error'])

    def test_responder_blocked_from_updating_center(self):
        self.client.force_login(self.responder)
        response = self.client.post(reverse('update_center', args=[self.center.pk]), {'status': 'closed', 'occupants': 0})
        self.assertEqual(response.status_code, 403)

    def test_responder_blocked_from_archiving_center(self):
        self.client.force_login(self.responder)
        response = self.client.post(reverse('archive_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 403)

    def test_responder_blocked_from_deleting_center(self):
        self.client.force_login(self.responder)
        response = self.client.post(reverse('delete_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 403)

    def test_coordinator_blocked_from_permanently_deleting_center(self):
        self.client.force_login(self.coordinator)
        response = self.client.post(reverse('delete_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(EvacuationCenter.objects.filter(pk=self.center.pk).exists())

    def test_admin_can_permanently_delete_center(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EvacuationCenter.objects.filter(pk=self.center.pk).exists())


class EvacuationCenterLifecycleAndAuditTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(username='coord_lifecycle', password='password')
        Profile.objects.filter(user=self.coordinator).update(role='Coordinator')

        self.admin = User.objects.create_user(username='admin_lifecycle', password='password')
        Profile.objects.filter(user=self.admin).update(role='Admin')

        self.center = EvacuationCenter.objects.create(
            name='Lifecycle Facility',
            location='District 3',
            capacity=120,
            occupants=30,
            status='active'
        )

    def test_archiving_center_soft_deletes_and_records_audit_log(self):
        self.client.force_login(self.coordinator)
        response = self.client.post(reverse('archive_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 200)

        self.center.refresh_from_db()
        self.assertTrue(self.center.is_archived)
        self.assertIsNotNone(self.center.archived_at)
        self.assertEqual(self.center.archived_by, self.coordinator)

        # AuditLog record created
        log = AuditLog.objects.filter(center=self.center, action='archive').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.coordinator)
        self.assertEqual(log.center_name, 'Lifecycle Facility')

    def test_restoring_center_unarchives_and_records_audit_log(self):
        self.center.is_archived = True
        self.center.save()
        self.client.force_login(self.coordinator)

        response = self.client.post(reverse('restore_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 200)

        self.center.refresh_from_db()
        self.assertFalse(self.center.is_archived)
        self.assertIsNone(self.center.archived_at)

        log = AuditLog.objects.filter(center=self.center, action='restore').first()
        self.assertIsNotNone(log)

    def test_permanent_deletion_records_audit_log_with_prior_state(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_center', args=[self.center.pk]))
        self.assertEqual(response.status_code, 200)

        # Center gone from DB
        self.assertFalse(EvacuationCenter.objects.filter(pk=self.center.pk).exists())

        # Audit log persists center name and previous occupants/capacity
        log = AuditLog.objects.filter(center_name='Lifecycle Facility', action='delete').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.old_capacity, 120)
        self.assertEqual(log.old_occupants, 30)


class LiveCentersAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='live_viewer', password='password')
        self.center = EvacuationCenter.objects.create(name='Live Center', capacity=80, occupants=25, status='active')

    def test_live_centers_api_returns_expected_structure(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('live_centers_api'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('summary', data)
        self.assertIn('centers', data)
        self.assertIn('audit_logs', data)
        self.assertIn('active_incidents', data)
        self.assertIn('timestamp', data)

        center_data = next((c for c in data['centers'] if c['id'] == self.center.id), None)
        self.assertIsNotNone(center_data)
        self.assertEqual(center_data['name'], 'Live Center')
        self.assertEqual(center_data['occupants'], 25)
        self.assertEqual(center_data['capacity'], 80)


class IncidentAndResourceTrackingTests(TestCase):
    def setUp(self):
        from django.core import mail
        mail.outbox = []

        self.coordinator = User.objects.create_user(
            username='coord_ops',
            email='coord@example.com',
            password='password'
        )
        Profile.objects.filter(user=self.coordinator).update(role='Coordinator')

        # Subscriber for email notifications
        self.subscriber = User.objects.create_user(
            username='subscriber_user',
            email='notify_me@example.com',
            password='password'
        )
        UserSettings.objects.filter(user=self.subscriber).update(email_notifications=True)

        self.center = EvacuationCenter.objects.create(name='Logistics Center', capacity=200, occupants=50)

    def test_declare_critical_incident_creates_record_and_triggers_email_alert(self):
        from django.core import mail
        self.client.force_login(self.coordinator)

        response = self.client.post(reverse('declare_incident'), {
            'title': 'Category 5 Typhoon Approaching',
            'disaster_type': 'Typhoon',
            'severity': 'critical',
            'location': 'Northern Coastal Zone',
            'description': 'High storm surge expected in 6 hours.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Incident.objects.filter(title='Category 5 Typhoon Approaching').exists())

        # Email alert was sent to subscribed user
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn('CRITICAL', mail.outbox[0].subject)
        self.assertIn('notify_me@example.com', mail.outbox[0].to)

    def test_resolve_incident_updates_status(self):
        incident = Incident.objects.create(
            title='Minor Inundation',
            disaster_type='Flood',
            severity='low',
            declared_by=self.coordinator
        )
        self.client.force_login(self.coordinator)
        response = self.client.post(reverse('resolve_incident', args=[incident.id]))
        self.assertEqual(response.status_code, 200)

        incident.refresh_from_db()
        self.assertFalse(incident.is_active)
        self.assertIsNotNone(incident.resolved_at)

    def test_update_center_resources_updates_inventory_and_audit(self):
        self.client.force_login(self.coordinator)
        response = self.client.post(reverse('update_resource', args=[self.center.id]), {
            'food_packs': 350,
            'water_liters': 1200,
            'medical_kits': 45,
            'blankets': 200,
        })
        self.assertEqual(response.status_code, 200)

        inv = ResourceInventory.objects.get(center=self.center)
        self.assertEqual(inv.food_packs, 350)
        self.assertEqual(inv.water_liters, 1200)
        self.assertEqual(inv.medical_kits, 45)
        self.assertEqual(inv.blankets, 200)
