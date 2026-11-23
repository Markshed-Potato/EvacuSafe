from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from apps.profile.models import Profile
from apps.user_settings.models import UserSettings


class RegistrationViewTests(TestCase):
    def test_registration_page_renders_for_anonymous_user(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create your account')

    def test_authenticated_user_redirected_away_from_registration(self):
        user = User.objects.create_user(username='already_user', password='Password123!')
        self.client.force_login(user)
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_valid_registration_creates_user_and_auto_provisions_profile_and_settings(self):
        response = self.client.post(reverse('register'), {
            'username': 'new_responder',
            'email': 'new_responder@example.com',
            'password1': 'StrongPass123!@#',
            'password2': 'StrongPass123!@#',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

        # User is created and active
        self.assertTrue(User.objects.filter(username='new_responder').exists())
        user = User.objects.get(username='new_responder')
        self.assertEqual(user.email, 'new_responder@example.com')

        # Auto-provisioned profile & settings via signals
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.role, 'Responder')
        self.assertTrue(UserSettings.objects.filter(user=user).exists())

    def test_mismatched_passwords_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'fail_user',
            'email': 'fail@example.com',
            'password1': 'PassOne123!',
            'password2': 'PassTwo456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='fail_user').exists())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='existing_user', email='a@example.com', password='Password123!')
        response = self.client.post(reverse('register'), {
            'username': 'existing_user',
            'email': 'b@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
