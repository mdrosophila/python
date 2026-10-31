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


class PortfolioTests(TestCase):
    def make_ips(self, username='bob', **overrides):
        from ips.models import Investor, InvestmentPolicyStatement
        user = User.objects.create_user(username, password='pw-123456-x')
        investor = Investor.objects.create(
            user=user, name=username, email=f'{username}@x.com', phone='555' + str(abs(hash(username)))[:7])
        fields = dict(risk_tolerance='moderate', max_acceptable_loss_pct=25, required_return_pct=6,
                      time_horizon_years=15, liquidity_reserve_pct=10)
        fields.update(overrides)
        return user, InvestmentPolicyStatement.objects.create(investor=investor, **fields)

    def test_portfolio_respects_statement_limits(self):
        from ips.portfolio import SIGMA_CAP, build_portfolio
        _, ips = self.make_ips()
        p = build_portfolio(ips)
        self.assertEqual(sum(p['weights'].values()), 100)
        self.assertGreaterEqual(p['stats']['worst'], -25)
        self.assertLessEqual(p['stats']['sigma'], SIGMA_CAP['moderate'])
        self.assertGreaterEqual(p['cash'], 10)
        self.assertTrue(p['meets_return'])
        self.assertGreaterEqual(p['stats']['cagr'], 6)

    def test_unreachable_return_falls_back_to_best_within_limits(self):
        from ips.portfolio import build_portfolio
        _, ips = self.make_ips(risk_tolerance='conservative', required_return_pct=15)
        p = build_portfolio(ips)
        self.assertFalse(p['meets_return'])
        self.assertLessEqual(p['stats']['sigma'], 8)

    def test_impossible_limits_give_no_portfolio(self):
        from ips.portfolio import build_portfolio
        _, ips = self.make_ips(max_acceptable_loss_pct=0, liquidity_reserve_pct=0, risk_tolerance='aggressive')
        # Zero tolerated loss is only met by T-bills, which cannot reach 6%.
        self.assertFalse(build_portfolio(ips)['meets_return'])
        _, ips = self.make_ips('carol', max_acceptable_loss_pct=0, liquidity_reserve_pct=0)
        ips.max_acceptable_loss_pct = -5  # no allocation avoids a loss in every year
        self.assertIsNone(build_portfolio(ips)['weights'])

    def test_view_shows_portfolio_and_hides_other_users(self):
        owner, ips = self.make_ips()
        other, _ = self.make_ips('dave')
        url = f'/ips/{ips.pk}/portfolio/'
        self.client.force_login(owner)
        r = self.client.get(url)
        self.assertContains(r, 'Recommended allocation')
        self.client.force_login(other)
        self.assertEqual(self.client.get(url).status_code, 404)


class EditTests(PortfolioTests):
    def test_owner_can_edit_and_others_cannot(self):
        owner, ips = self.make_ips()
        other, _ = self.make_ips('erin')
        url = f'/ips/{ips.pk}/edit/'
        self.client.force_login(owner)
        self.assertContains(self.client.get(url), 'Edit Investment Policy Statement')
        data = dict(risk_tolerance='aggressive', max_acceptable_loss_pct=40, required_return_pct=8,
                    time_horizon_years=20, liquidity_reserve_pct=5)
        self.assertRedirects(self.client.post(url, data), f'/ips/{ips.pk}/')
        ips.refresh_from_db()
        self.assertEqual((ips.risk_tolerance, ips.time_horizon_years), ('aggressive', 20))
        self.client.force_login(other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, data).status_code, 404)


class PortfolioLookbackTests(PortfolioTests):
    def test_lookback_changes_inputs_and_flags_short_window(self):
        from ips.portfolio import build_portfolio
        _, ips = self.make_ips('frank', time_horizon_years=15)
        recent = build_portfolio(ips, 10)
        self.assertIsNone(recent['success_rate'])  # 10 years is shorter than the 15-year horizon
        self.assertNotEqual(recent['stats'], build_portfolio(ips)['stats'])
        self.assertIsNotNone(build_portfolio(ips, 40)['success_rate'])

    def test_view_accepts_lookback(self):
        user, ips = self.make_ips('gina')
        self.client.force_login(user)
        r = self.client.get(f'/ips/{ips.pk}/portfolio/', {'lookback': 30})
        self.assertContains(r, 'Backtest of the last 15 years')
        self.assertContains(r, 'value="30"')
