from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from apps.profile.models import Profile


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='responder_profile',
            email='profile@example.com',
            first_name='Maria',
            last_name='Santos',
            password='Password123!'
        )
        self.profile = Profile.objects.get_or_create(user=self.user)[0]
        self.profile.role = 'Responder'
        self.profile.phone = '+63 917 123 4567'
        self.profile.bio = 'Field volunteer in Cebu sector.'
        self.profile.save()

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_user_can_view_profile_and_session_diagnostics(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maria')
        self.assertContains(response, 'Santos')
        self.assertContains(response, 'Field volunteer in Cebu sector.')
        self.assertContains(response, 'Active Session & Security Diagnostics')
        self.assertContains(response, 'Client IP Address')
        self.assertContains(response, 'Danger Zone')

    def test_update_personal_and_responder_information(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'first_name': 'Maria Clara',
            'last_name': 'Santos-Delacruz',
            'email': 'maria.new@example.com',
            'role': 'Coordinator',
            'phone': '+63 999 888 7777',
            'bio': 'Promoted to Sector Lead Coordinator.',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Maria Clara')
        self.assertEqual(self.user.last_name, 'Santos-Delacruz')
        self.assertEqual(self.user.email, 'maria.new@example.com')
        self.assertEqual(self.profile.role, 'Coordinator')
        self.assertEqual(self.profile.phone, '+63 999 888 7777')

    def test_non_admin_cannot_escalate_own_role_to_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'profile@example.com',
            'role': 'Admin',
            'phone': '+63 917 123 4567',
            'bio': 'Trying to self-escalate to Admin',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only existing Administrators or staff may assign the Admin role.')
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.role, 'Admin')

    def test_self_service_account_deactivation(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'action': 'deactivate_account',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_self_service_account_deletion_with_confirmation(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'action': 'delete_account',
            'confirm_username': 'responder_profile',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(User.objects.filter(username='responder_profile').exists())
