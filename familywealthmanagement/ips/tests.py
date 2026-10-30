import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase


class LoginIdentifierTests(TestCase):
    def setUp(self):
        self.client.post('/accounts/register/', dict(
            username='alice', password1='Sup3r-secret-pw', password2='Sup3r-secret-pw',
            name='Alice', email='Alice@X.com', phone='(555) 111-2222', mailing_address=''))
        self.client.post('/accounts/logout/')

    def login(self, identifier, password='Sup3r-secret-pw'):
        self.client.post('/accounts/logout/')
        self.client.post('/accounts/login/', {'username': identifier, 'password': password})
        return '_auth_user_id' in self.client.session

    def test_username_email_and_phone_all_work(self):
        for identifier in ('alice', 'alice@x.com', ' ALICE@x.com ', '5551112222', '555-111-2222'):
            self.assertTrue(self.login(identifier), identifier)

    def test_wrong_password_or_unknown_identifier_fails(self):
        self.assertFalse(self.login('alice@x.com', 'wrong'))
        self.assertFalse(self.login('5551112222', 'wrong'))
        self.assertFalse(self.login('nobody@x.com'))
        self.assertFalse(self.login('5550000000'))

    def test_inactive_user_cannot_log_in(self):
        User.objects.filter(username='alice').update(is_active=False)
        self.assertFalse(self.login('alice@x.com'))


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
