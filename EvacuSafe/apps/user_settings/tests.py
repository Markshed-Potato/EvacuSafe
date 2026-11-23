from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from apps.user_settings.models import UserSettings


class DefaultThemeTests(TestCase):
    def test_login_and_registration_use_dark_theme_for_anonymous_users(self):
        for route_name in ('login', 'register'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'class="auth-body dark-mode"')

    def test_saved_light_preference_is_applied_to_authenticated_pages(self):
        user = User.objects.create_user(username='light-user', password='test-password')
        settings, _ = UserSettings.objects.get_or_create(user=user)
        settings.dark_mode = False
        settings.save()
        self.client.force_login(user)

        for route_name in ('home', 'profile', 'user_settings'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'class=" light-mode"')

    def test_theme_toggle_saves_and_applies_light_mode(self):
        user = User.objects.create_user(username='toggle-user', password='test-password')
        self.client.force_login(user)

        response = self.client.post(reverse('user_settings'), {
            'save_settings': '',
            'email_notifications': 'on',
            'language': 'en',
        })
        self.assertEqual(response.status_code, 302)

        user_settings = UserSettings.objects.get(user=user)
        self.assertFalse(user_settings.dark_mode)

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class=" light-mode"')


class UserSettingsFunctionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='settings_tester',
            email='settings@example.com',
            password='CurrentPassword123!'
        )
        self.client.force_login(self.user)

    def test_language_selection_activates_localization_and_sets_cookie(self):
        response = self.client.post(reverse('user_settings'), {
            'save_settings': '',
            'language': 'fil',
            'email_notifications': 'on',
            'sms_alerts': 'on',
            'dark_mode': 'on',
        })
        self.assertEqual(response.status_code, 302)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.language, 'fil')
        self.assertEqual(response.cookies.get('django_language').value, 'fil')

    def test_password_change_with_valid_credentials_succeeds(self):
        response = self.client.post(reverse('user_settings'), {
            'change_password': '',
            'old_password': 'CurrentPassword123!',
            'new_password1': 'BrandNewPassword456!#',
            'new_password2': 'BrandNewPassword456!#',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_settings'))

        # Verify password actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewPassword456!#'))

    def test_password_change_with_incorrect_current_password_rejected(self):
        response = self.client.post(reverse('user_settings'), {
            'change_password': '',
            'old_password': 'WrongCurrentPassword!',
            'new_password1': 'BrandNewPassword456!#',
            'new_password2': 'BrandNewPassword456!#',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the password errors below.')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('CurrentPassword123!'))
