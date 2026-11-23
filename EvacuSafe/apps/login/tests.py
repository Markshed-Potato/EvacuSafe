from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='responder_user',
            email='responder@example.com',
            password='Password123!'
        )

    def test_anonymous_user_can_access_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
        self.assertContains(response, 'Forgot password?')

    def test_authenticated_user_redirected_to_home(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_valid_login_redirects_to_home(self):
        response = self.client.post(reverse('login'), {
            'username': 'responder_user',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'responder_user',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))


class PasswordResetWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reset_user',
            email='reset@example.com',
            password='OriginalPassword123!'
        )

    def test_password_reset_form_renders(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Password')

    def test_password_reset_sends_email_for_existing_user(self):
        response = self.client.post(reverse('password_reset'), {
            'email': 'reset@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset', mail.outbox[0].subject)

    def test_password_reset_done_renders(self):
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Instructions Sent')
