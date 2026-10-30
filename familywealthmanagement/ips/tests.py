import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client.post('/accounts/register/', dict(
            username='alice', password1='Sup3r-secret-pw', password2='Sup3r-secret-pw',
            name='Alice', email='a@x.com', phone='5551112222', mailing_address=''))
        self.client.post('/accounts/logout/')

    def test_registration_stores_email_on_user(self):
        self.assertEqual(User.objects.get(username='alice').email, 'a@x.com')

    def test_reset_flow(self):
        self.assertEqual(self.client.get('/accounts/password-reset/').status_code, 200)
        r = self.client.post('/accounts/password-reset/', {'email': 'a@x.com'})
        self.assertRedirects(r, '/accounts/password-reset/sent/')
        self.assertEqual(len(mail.outbox), 1)
        path = re.search(r'/accounts/reset/\S+', mail.outbox[0].body).group(0)

        r = self.client.get(path, follow=True)  # Django swaps the token for a session URL
        self.assertContains(r, 'new_password1')
        r = self.client.post(r.redirect_chain[-1][0], {
            'new_password1': 'Brand-new-pw-77', 'new_password2': 'Brand-new-pw-77'})
        self.assertRedirects(r, '/accounts/reset/done/')
        self.assertTrue(self.client.login(username='alice', password='Brand-new-pw-77'))

    def test_unknown_email_sends_nothing(self):
        r = self.client.post('/accounts/password-reset/', {'email': 'nobody@x.com'})
        self.assertRedirects(r, '/accounts/password-reset/sent/')  # same response, so accounts aren't revealed
        self.assertEqual(len(mail.outbox), 0)

    def test_login_page_links_to_reset(self):
        self.assertContains(self.client.get('/accounts/login/'), '/accounts/password-reset/')
