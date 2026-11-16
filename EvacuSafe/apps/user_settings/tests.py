from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class DefaultThemeTests(TestCase):
    def test_login_and_registration_use_dark_theme_for_anonymous_users(self):
        for route_name in ('login', 'register'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'dark-mode')

    def test_new_accounts_default_to_dark_theme(self):
        user = User.objects.create_user(username='dark-responder', password='test-password')
        self.assertTrue(user.settings.dark_mode)

    def test_saved_light_preference_is_applied_to_authenticated_pages(self):
        user = User.objects.create_user(username='light-responder', password='test-password')
        user.settings.dark_mode = False
        user.settings.save()
        self.client.force_login(user)

        response = self.client.get(reverse('user_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'light-mode')
        self.assertNotContains(response, 'dark-mode')
